


!pip install yfinance
import yfinance as yf
import pandas as pd

def get_stock_info(stock_code):
    # 獲取股票資料
    stock = yf.Ticker(stock_code)

    # 獲取基本資訊
    info = stock.info

    # 打印基本資訊
    print(f"\n股票: {info.get('shortName', 'N/A')} ({stock_code})")
    print(f"市場價格: {info.get('regularMarketPrice', 'N/A')}")
    print(f"市值: {info.get('marketCap', 'N/A')}")
    print(f"市盈率: {info.get('trailingPE', 'N/A')}")
    print(f"股息率: {info.get('dividendYield', 'N/A')}")
    print(f"52周高點: {info.get('fiftyTwoWeekHigh', 'N/A')}")
    print(f"52周低點: {info.get('fiftyTwoWeekLow', 'N/A')}")

    # 獲取歷史市場數據
    hist = stock.history(period="1y")

    # 顯示最近的五條歷史市場數據
    print("\n最近的五條歷史市場數據：")
    print(hist.tail())
