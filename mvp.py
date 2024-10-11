import os
from dotenv import load_dotenv
import pyupbit
import json

load_dotenv()


# 1. 업비트 차트 가져오기 (30일 일봉)
df = pyupbit.get_ohlcv("KRW-BTC", count=30, interval="day")


# 2. AI에게 차트 주고 투자 판단 받기 (Buy, Sell, Hold)
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
  model="gpt-4o",
  messages=[
    {
      "role": "system",
      "content": [
        {
          "type": "text",
          "text": "You are a Bitcoin investment expert.\nTell me which option to buy, sell, or hold based on the provided chart data. \n\nresponse example:\n{\"decision\":\"buy\",\"reason\":\"some technical reason\"}\n{\"decision\":\"sell\",\"reason\":\"some technical reason\"}\n{\"decision\":\"hole\",\"reason\":\"some technical reason\"}"
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": df.to_json()
        }
      ]
    },
  ],
  temperature=1,
  response_format={
    "type": "text"
  }
)

result = response.choices[0].message.content
result = json.loads(result)


# 3. 받은 데이터로 자동 매매하기
access = os.getenv("UPBIT_ACCESS_KEY")
secret = os.getenv("UPBIT_SECRET_KEY")
upbit = pyupbit.Upbit(access,secret)

def ai_trading():
    print(f"### decision: {result['decision']} ###")
    print(f"### Reason: {result['reason']} ###")

    if result['decision'] == "buy":    # 매수
        my_krw = upbit.get_balance("KRW")
        if my_krw > 10000*1.0005:
            print("### Buy Order Executed ###")
            print(upbit.buy_market_order("KRW-BTC", 10000))
        else:
            print("### 실패: 금액 부족 ###")

    elif result['decision'] == "sell":    # 매도
        amount_my_btc = upbit.get_balance("KRW-BTC")
        current_price_btc = pyupbit.get_orderbook(ticker="KRW-BTC")['orderbook_units'][0]['ask_price']
        my_btc = amount_my_btc * current_price_btc
        if my_btc >= 5000:
            print("### Buy Sell Executed ###")
            print(upbit.sell_market_order("KRW-BTC", amount_my_btc))
        else:
            print("### 실패: 코인 잔고 5000원 미만 ###")

    elif result['decision'] == "hold":    # 보유
        print(result['reason'])

ai_trading()