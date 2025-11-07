"""
Stock Advisor using Alpha Vantage API
======================================
Replaces Finnhub with Alpha Vantage for all stock data.
Includes: Quotes, Technical Indicators, Fundamental Data, Historical Data
Author: Bhoomika M
Date: 2025-11-07
"""

import requests
import time
from typing import Dict, Optional, List, Tuple
import pandas as pd
from datetime import datetime, timedelta


class StockAdvisorAlphaVantage:
    """
    Comprehensive stock advisor using Alpha Vantage API for:
    - Real-time quotes
    - Technical indicators (RSI, MACD, SMA, EMA, Bollinger Bands, etc.)
    - Fundamental data (Company overview, earnings, income statements)
    - Historical OHLCV data (Daily, Weekly, Monthly, Intraday)
    - Economic indicators
    """
    
    def __init__(self, api_key: str):
        """
        Initialize with Alpha Vantage API key.
        
        Args:
            api_key: Your Alpha Vantage API key from https://www.alphavantage.co/support/#api-key
        """
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.call_count = 0
        self.last_call_time = time.time()
        self.cache = {}  # Simple in-memory cache
        
    def _rate_limit(self):
        """
        Implements rate limiting: 5 calls per minute for free tier.
        Automatically handles the 12-second delay between calls.
        """
        self.call_count += 1
        
        # If we've made 5 calls, enforce 60-second wait
        if self.call_count >= 5:
            elapsed = time.time() - self.last_call_time
            if elapsed < 60:
                wait_time = 60 - elapsed
                print(f"⏳ Rate limit: Sleeping for {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            
            # Reset counter
            self.call_count = 0
            self.last_call_time = time.time()
        else:
            # Small delay between calls (12 seconds = 5 calls/minute)
            time.sleep(12)
    
    def _make_request(self, params: Dict, use_cache: bool = True) -> Optional[Dict]:
        """
        Makes an API request with rate limiting and caching.
        
        Args:
            params: Query parameters for the API
            use_cache: Whether to use cached response if available
            
        Returns:
            JSON response or None if error
        """
        # Create cache key
        cache_key = str(sorted(params.items()))
        
        # Check cache
        if use_cache and cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            # Cache valid for 1 hour
            if time.time() - cached_time < 3600:
                print(f"📦 Using cached data for {params.get('symbol', 'request')}")
                return cached_data
        
        self._rate_limit()
        
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                print(f"❌ API Error: {data['Error Message']}")
                return None
            
            if 'Note' in data:  # Rate limit message
                print(f"⚠️ API Note: {data['Note']}")
                print("Waiting 60 seconds and retrying...")
                time.sleep(60)
                return self._make_request(params, use_cache=False)  # Retry without cache
            
            if 'Information' in data:  # Often API limit message
                print(f"ℹ️ API Info: {data['Information']}")
                return None
            
            # Cache the successful response
            self.cache[cache_key] = (data, time.time())
            
            return data
            
        except requests.exceptions.Timeout:
            print(f"⏱️ Request timeout for {params.get('symbol', 'request')}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    # ==================== STOCK QUOTES ====================
    
    def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """
        Gets real-time quote for a stock.
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL', 'GOOGL')
            
        Returns:
            Dict with price, volume, change data or None if error
            
        Example:
            >>> advisor.get_stock_quote('AAPL')
            {'symbol': 'AAPL', 'price': 150.25, 'change': 2.5, ...}
        """
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if not data or 'Global Quote' not in data:
            return None
        
        quote = data['Global Quote']
        
        if not quote:
            return None
        
        try:
            return {
                'symbol': symbol,
                'price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                'volume': int(float(quote.get('06. volume', 0))),
                'high': float(quote.get('03. high', 0)),
                'low': float(quote.get('04. low', 0)),
                'open': float(quote.get('02. open', 0)),
                'previous_close': float(quote.get('08. previous close', 0)),
                'latest_trading_day': quote.get('07. latest trading day', '')
            }
        except (ValueError, TypeError) as e:
            print(f"❌ Error parsing quote for {symbol}: {e}")
            return None
    
    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
        """
        Gets quotes for multiple stocks.
        Note: Makes individual API calls for each symbol due to Alpha Vantage limitations.
        
        Args:
            symbols: List of stock tickers
            
        Returns:
            Dictionary mapping symbols to their quote data
        """
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_stock_quote(symbol)
        return results
    
    # ==================== HISTORICAL DATA ====================
    
    def get_daily_data(self, symbol: str, outputsize: str = 'compact') -> Optional[pd.DataFrame]:
        """
        Gets daily time series data.
        
        Args:
            symbol: Stock ticker
            outputsize: 'compact' (100 days) or 'full' (20+ years)
            
        Returns:
            Pandas DataFrame with OHLCV data indexed by date
        """
        params = {
            'function': 'TIME_SERIES_DAILY_ADJUSTED',
            'symbol': symbol,
            'outputsize': outputsize
        }
        
        data = self._make_request(params)
        
        if not data or 'Time Series (Daily)' not in data:
            return None
        
        try:
            df = pd.DataFrame.from_dict(
                data['Time Series (Daily)'], 
                orient='index'
            )
            df.columns = ['Open', 'High', 'Low', 'Close', 'Adjusted_Close', 
                         'Volume', 'Dividend', 'Split']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"❌ Error parsing daily data for {symbol}: {e}")
            return None
    
    def get_weekly_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Gets weekly time series data.
        
        Args:
            symbol: Stock ticker
            
        Returns:
            Pandas DataFrame with weekly OHLCV data
        """
        params = {
            'function': 'TIME_SERIES_WEEKLY_ADJUSTED',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if not data or 'Weekly Adjusted Time Series' not in data:
            return None
        
        try:
            df = pd.DataFrame.from_dict(
                data['Weekly Adjusted Time Series'], 
                orient='index'
            )
            df.columns = ['Open', 'High', 'Low', 'Close', 'Adjusted_Close', 
                         'Volume', 'Dividend']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"❌ Error parsing weekly data for {symbol}: {e}")
            return None
    
    def get_monthly_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Gets monthly time series data.
        
        Args:
            symbol: Stock ticker
            
        Returns:
            Pandas DataFrame with monthly OHLCV data
        """
        params = {
            'function': 'TIME_SERIES_MONTHLY_ADJUSTED',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if not data or 'Monthly Adjusted Time Series' not in data:
            return None
        
        try:
            df = pd.DataFrame.from_dict(
                data['Monthly Adjusted Time Series'], 
                orient='index'
            )
            df.columns = ['Open', 'High', 'Low', 'Close', 'Adjusted_Close', 
                         'Volume', 'Dividend']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"❌ Error parsing monthly data for {symbol}: {e}")
            return None
    
    def get_intraday_data(self, symbol: str, interval: str = '5min', 
                         outputsize: str = 'compact') -> Optional[pd.DataFrame]:
        """
        Gets intraday time series data.
        
        Args:
            symbol: Stock ticker
            interval: '1min', '5min', '15min', '30min', '60min'
            outputsize: 'compact' (latest 100 points) or 'full' (full day)
            
        Returns:
            Pandas DataFrame with intraday OHLCV data
        """
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize
        }
        
        data = self._make_request(params)
        
        time_series_key = f'Time Series ({interval})'
        
        if not data or time_series_key not in data:
            return None
        
        try:
            df = pd.DataFrame.from_dict(
                data[time_series_key], 
                orient='index'
            )
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"❌ Error parsing intraday data for {symbol}: {e}")
            return None
    
    # ==================== TECHNICAL INDICATORS ====================
    
    def get_rsi(self, symbol: str, interval: str = 'daily', 
                time_period: int = 14) -> Optional[pd.DataFrame]:
        """
        Gets RSI (Relative Strength Index) technical indicator.
        
        Args:
            symbol: Stock ticker
            interval: 'daily', 'weekly', 'monthly', '1min', '5min', '15min', '30min', '60min'
            time_period: Number of periods for RSI calculation (default 14)
            
        Returns:
            DataFrame with RSI values
        """
        params = {
            'function': 'RSI',
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period,
            'series_type': 'close'
        }
        
        data = self._make_request(params)
        
        if not data or 'Technical Analysis: RSI' not in data:
            return None
        
        try:
            df = pd.DataFrame.from_dict(
                data['Technical Analysis: RSI'], 
                orient='index'
            )
            df.columns = ['RSI']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"❌ Error parsing RSI for {symbol}: {e}")
            return None
    
    def get_macd(self, symbol: str, interval: str = 'daily',
                 fastperiod: int = 12, slowperiod: int = 26,
                 signalperiod: int = 9) -> Optional[pd.DataFrame]:
        """
        Gets MACD (Moving Average Convergence Divergence) indicator.
        
        Args:
            symbol: Stock ticker
            interval: Time interval
            fastperiod: Fast EMA period (default 12)
            slowperiod: Slow EMA period (default 26)
            signalperiod: Signal line period (default 9)
            
        Returns:
            DataFrame with MACD, Signal, and Histogram
        """
        params = {
            'function': 'MACD',
            'symbol': symbol,
            'interval': interval,
            'series_type': 'close',
            'fastperiod': fastperiod,
            'slowperiod': slowperiod,
            'signalperiod': signalperiod
        }
        
        data = self._make_request(params)
        
        if not data or 'Technical Analysis: MACD' not in data:
            return None
        
        try:
            df = pd.DataFrame.from_dict(
                data['Technical Analysis: MACD'], 
                orient='index'
            )
            df.columns = ['MACD', 'MACD_Signal', 'MACD_Hist']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"❌ Error parsing MACD for {symbol}: {e}")
            return None
    
    def get_sma(self, symbol: str, interval: str = 'daily', 
                time_period: int = 50) -> Optional[pd.DataFrame]:
        """
        Gets SMA (Simple Moving Average).
        
        Args:
            symbol: Stock ticker
            interval: Time interval
            time_period: Number of periods (e.g., 50, 200)
            
        Returns:
            DataFrame with SMA values
        """
        params = {
            'function': 'SMA',
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period,
            'series_type': 'close'
        }
        
        data = self._make_request(params)
        
        if not data or 'Technical Analysis: SMA' not in data:
            return None
        
        try:
            df = pd.DataFrame.from_dict(
                data['Technical Analysis: SMA'], 
                orient='index'
            )
            df.columns = ['SMA']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"❌ Error parsing SMA for {symbol}: {e}")
            return None
    
    def get_ema(self, symbol: str, interval: str = 'daily', 
                time_period: int = 50) -> Optional[pd.DataFrame]:
        """
        Gets EMA (Exponential Moving Average).
        
        Args:
            symbol: Stock ticker
            interval: Time interval
            time_period: Number of periods
            
        Returns:
            DataFrame with EMA values
        """
        params = {
            'function': 'EMA',
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period,
            'series_type': 'close'
        }
        
        data = self._make_request(params)
        
        if not data or 'Technical Analysis: EMA' not in data:
            return None
        
        try:
            df = pd.DataFrame.from_dict(
                data['Technical Analysis: EMA'], 
                orient='index'
            )
            df.columns = ['EMA']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"❌ Error parsing EMA for {symbol}: {e}")
            return None
    
    def get_bbands(self, symbol: str, interval: str = 'daily',
                   time_period: int = 20, nbdevup: int = 2,
                   nbdevdn: int = 2) -> Optional[pd.DataFrame]:
        """
        Gets Bollinger Bands.
        
        Args:
            symbol: Stock ticker
            interval: Time interval
            time_period: Moving average period (default 20)
            nbdevup: Upper band std deviations (default 2)
            nbdevdn: Lower band std deviations (default 2)
            
        Returns:
            DataFrame with upper, middle, and lower bands
        """
        params = {
            'function': 'BBANDS',
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period,
            'series_type': 'close',
            'nbdevup': nbdevup,
            'nbdevdn': nbdevdn
        }
        
        data = self._make_request(params)
        
        if not data or 'Technical Analysis: BBANDS' not in data:
            return None
        
        try:
            df = pd.DataFrame.from_dict(
                data['Technical Analysis: BBANDS'], 
                orient='index'
            )
            df.columns = ['Real_Upper_Band', 'Real_Middle_Band', 'Real_Lower_Band']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"❌ Error parsing Bollinger Bands for {symbol}: {e}")
            return None
    
    def get_stoch(self, symbol: str, interval: str = 'daily') -> Optional[pd.DataFrame]:
        """
        Gets Stochastic Oscillator.
        
        Args:
            symbol: Stock ticker
            interval: Time interval
            
        Returns:
            DataFrame with SlowK and SlowD values
        """
        params = {
            'function': 'STOCH',
            'symbol': symbol,
            'interval': interval
        }
        
        data = self._make_request(params)
        
        if not data or 'Technical Analysis: STOCH' not in data:
            return None
        
        try:
            df = pd.DataFrame.from_dict(
                data['Technical Analysis: STOCH'], 
                orient='index'
            )
            df.columns = ['SlowK', 'SlowD']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"❌ Error parsing Stochastic for {symbol}: {e}")
            return None
    
    def get_adx(self, symbol: str, interval: str = 'daily',
                time_period: int = 14) -> Optional[pd.DataFrame]:
        """
        Gets ADX (Average Directional Index) - trend strength indicator.
        
        Args:
            symbol: Stock ticker
            interval: Time interval
            time_period: Number of periods (default 14)
            
        Returns:
            DataFrame with ADX values
        """
        params = {
            'function': 'ADX',
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period
        }
        
        data = self._make_request(params)
        
        if not data or 'Technical Analysis: ADX' not in data:
            return None
        
        try:
            df = pd.DataFrame.from_dict(
                data['Technical Analysis: ADX'], 
                orient='index'
            )
            df.columns = ['ADX']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"❌ Error parsing ADX for {symbol}: {e}")
            return None
    
    def get_cci(self, symbol: str, interval: str = 'daily',
                time_period: int = 20) -> Optional[pd.DataFrame]:
        """
        Gets CCI (Commodity Channel Index).
        
        Args:
            symbol: Stock ticker
            interval: Time interval
            time_period: Number of periods (default 20)
            
        Returns:
            DataFrame with CCI values
        """
        params = {
            'function': 'CCI',
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period
        }
        
        data = self._make_request(params)
        
        if not data or 'Technical Analysis: CCI' not in data:
            return None
        
        try:
            df = pd.DataFrame.from_dict(
                data['Technical Analysis: CCI'], 
                orient='index'
            )
            df.columns = ['CCI']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"❌ Error parsing CCI for {symbol}: {e}")
            return None
    
    def get_obv(self, symbol: str, interval: str = 'daily') -> Optional[pd.DataFrame]:
        """
        Gets OBV (On-Balance Volume).
        
        Args:
            symbol: Stock ticker
            interval: Time interval
            
        Returns:
            DataFrame with OBV values
        """
        params = {
            'function': 'OBV',
            'symbol': symbol,
            'interval': interval
        }
        
        data = self._make_request(params)
        
        if not data or 'Technical Analysis: OBV' not in data:
            return None
        
        try:
            df = pd.DataFrame.from_dict(
                data['Technical Analysis: OBV'], 
                orient='index'
            )
            df.columns = ['OBV']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"❌ Error parsing OBV for {symbol}: {e}")
            return None
    
    # ==================== FUNDAMENTAL DATA ====================
    
    def get_company_overview(self, symbol: str) -> Optional[Dict]:
        """
        Gets comprehensive company information and fundamentals.
        
        Args:
            symbol: Stock ticker
            
        Returns:
            Dict with company overview including sector, market cap, P/E, etc.
        """
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if not data or 'Symbol' not in data:
            return None
        
        return data
    
    def get_earnings(self, symbol: str) -> Optional[Dict]:
        """
        Gets annual and quarterly earnings data.
        
        Args:
            symbol: Stock ticker
            
        Returns:
            Dict with earnings history and estimates
        """
        params = {
            'function': 'EARNINGS',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if not data or 'symbol' not in data:
            return None
        
        return data
    
    def get_income_statement(self, symbol: str) -> Optional[Dict]:
        """
        Gets annual and quarterly income statements.
        
        Args:
            symbol: Stock ticker
            
        Returns:
            Dict with revenue, expenses, net income, etc.
        """
        params = {
            'function': 'INCOME_STATEMENT',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if not data or 'symbol' not in data:
            return None
        
        return data
    
    def get_balance_sheet(self, symbol: str) -> Optional[Dict]:
        """
        Gets annual and quarterly balance sheets.
        
        Args:
            symbol: Stock ticker
            
        Returns:
            Dict with assets, liabilities, equity data
        """
        params = {
            'function': 'BALANCE_SHEET',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if not data or 'symbol' not in data:
            return None
        
        return data
    
    def get_cash_flow(self, symbol: str) -> Optional[Dict]:
        """
        Gets annual and quarterly cash flow statements.
        
        Args:
            symbol: Stock ticker
            
        Returns:
            Dict with operating, investing, financing cash flows
        """
        params = {
            'function': 'CASH_FLOW',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if not data or 'symbol' not in data:
            return None
        
        return data
    
    # ==================== COMPREHENSIVE ANALYSIS ====================
    
    def analyze_stock_technical(self, symbol: str) -> Optional[Dict]:
        """
        Comprehensive technical analysis using multiple indicators.
        This is the main function used by AI Budgeting.
        
        Args:
            symbol: Stock ticker
            
        Returns:
            Dict with technical analysis results including:
            - Current price and quote data
            - RSI (oversold/overbought signals)
            - MACD (buy/sell signals)
            - Trend analysis (SMA 50 vs 200)
            - Overall recommendation
        """
        print(f"📊 Analyzing {symbol} with Alpha Vantage...")
        
        # Get quote
        quote = self.get_stock_quote(symbol)
        if not quote:
            print(f"❌ Failed to get quote for {symbol}")
            return None
        
        # Get RSI
        rsi_df = self.get_rsi(symbol)
        latest_rsi = None
        if rsi_df is not None and len(rsi_df) > 0:
            latest_rsi = rsi_df.iloc[-1]['RSI']
        
        # Get MACD
        macd_df = self.get_macd(symbol)
        macd_signal = None
        if macd_df is not None and len(macd_df) > 0:
            latest_macd = macd_df.iloc[-1]
            macd_signal = 'BUY' if latest_macd['MACD'] > latest_macd['MACD_Signal'] else 'SELL'
        
        # Get SMAs for trend analysis
        sma_50 = self.get_sma(symbol, time_period=50)
        sma_200 = self.get_sma(symbol, time_period=200)
        
        trend = None
        if sma_50 is not None and sma_200 is not None and len(sma_50) > 0 and len(sma_200) > 0:
            if sma_50.iloc[-1]['SMA'] > sma_200.iloc[-1]['SMA']:
                trend = 'BULLISH'
            else:
                trend = 'BEARISH'
        
        # Generate overall recommendation
        recommendation = self._generate_recommendation(latest_rsi, macd_signal, trend, quote['price'])
        
        result = {
            'symbol': symbol,
            'price': quote['price'],
            'change': quote['change'],
            'change_percent': quote['change_percent'],
            'volume': quote['volume'],
            'high': quote['high'],
            'low': quote['low'],
            'rsi': latest_rsi,
            'macd_signal': macd_signal,
            'trend': trend,
            'recommendation': recommendation
        }
        
        print(f"✅ Analysis complete for {symbol}: {recommendation}")
        return result
    
    def _generate_recommendation(self, rsi: Optional[float], 
                                 macd_signal: Optional[str], 
                                 trend: Optional[str],
                                 price: float) -> str:
        """
        Generates buy/sell/hold recommendation based on technical indicators.
        
        Scoring system:
        - RSI < 30 (oversold): +2 buy signals
        - RSI 40-60 (neutral): +1 buy signal
        - RSI > 70 (overbought): +2 sell signals
        - MACD BUY: +2 buy signals
        - MACD SELL: +2 sell signals
        - Trend BULLISH: +1 buy signal
        - Trend BEARISH: +1 sell signal
        
        Returns:
            'STRONG_BUY', 'BUY', 'HOLD', 'SELL', or 'STRONG_SELL'
        """
        buy_signals = 0
        sell_signals = 0
        
        # RSI analysis
        if rsi:
            if rsi < 30:  # Oversold - good buying opportunity
                buy_signals += 2
            elif rsi > 70:  # Overbought - potential selling opportunity
                sell_signals += 2
            elif 40 < rsi < 60:  # Neutral zone
                buy_signals += 1
        
        # MACD analysis
        if macd_signal == 'BUY':
            buy_signals += 2
        elif macd_signal == 'SELL':
            sell_signals += 2
        
        # Trend analysis
        if trend == 'BULLISH':
            buy_signals += 1
        elif trend == 'BEARISH':
            sell_signals += 1
        
        # Final decision
        if buy_signals >= 4:
            return 'STRONG_BUY'
        elif buy_signals >= 2:
            return 'BUY'
        elif sell_signals >= 4:
            return 'STRONG_SELL'
        elif sell_signals >= 2:
            return 'SELL'
        else:
            return 'HOLD'
    
    def get_full_analysis(self, symbol: str) -> Optional[Dict]:
        """
        Gets complete analysis including technical AND fundamental data.
        This is a premium function that uses multiple API calls.
        
        Args:
            symbol: Stock ticker
            
        Returns:
            Comprehensive dict with all available data
        """
        print(f"🔍 Performing full analysis on {symbol}...")
        
        result = {
            'symbol': symbol,
            'technical': self.analyze_stock_technical(symbol),
            'overview': self.get_company_overview(symbol),
            'earnings': self.get_earnings(symbol)
        }
        
        return result
    
    # ==================== UTILITY FUNCTIONS ====================
    
    def search_symbol(self, keywords: str) -> Optional[List[Dict]]:
        """
        Searches for stock symbols by company name or keywords.
        
        Args:
            keywords: Search terms (e.g., 'Apple', 'Microsoft')
            
        Returns:
            List of matching symbols with company info
        """
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': keywords
        }
        
        data = self._make_request(params)
        
        if not data or 'bestMatches' not in data:
            return None
        
        return data['bestMatches']
    
    def clear_cache(self):
        """Clears the internal cache."""
        self.cache = {}
        print("🗑️ Cache cleared")
    
    def get_cache_size(self) -> int:
        """Returns the number of cached responses."""
        return len(self.cache)


# ==================== HELPER FUNCTIONS ====================

def format_large_number(num: float) -> str:
    """
    Formats large numbers into readable strings (e.g., 1.2B, 500M).
    
    Args:
        num: Number to format
        
    Returns:
        Formatted string
    """
    if num >= 1_000_000_000_000:
        return f"${num/1_000_000_000_000:.2f}T"
    elif num >= 1_000_000_000:
        return f"${num/1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"${num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"${num/1_000:.2f}K"
    else:
        return f"${num:.2f}"


def calculate_returns(start_price: float, end_price: float) -> float:
    """
    Calculates percentage return between two prices.
    
    Args:
        start_price: Initial price
        end_price: Final price
        
    Returns:
        Return percentage
    """
    if start_price == 0:
        return 0.0
    return ((end_price - start_price) / start_price) * 100


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    """
    Example usage and testing of the StockAdvisorAlphaVantage class.
    """
    
    # Initialize with your API key
    API_KEY = "ZRBAZ10IY283K3T7"  # Replace with your actual key
    advisor = StockAdvisorAlphaVantage(API_KEY)
    
    # Example 1: Get a stock quote
    print("\n=== Example 1: Stock Quote ===")
    quote = advisor.get_stock_quote('AAPL')
    if quote:
        print(f"AAPL Price: ${quote['price']}")
        print(f"Change: {quote['change_percent']}%")
    
    # Example 2: Technical analysis
    print("\n=== Example 2: Technical Analysis ===")
    analysis = advisor.analyze_stock_technical('TSLA')
    if analysis:
        print(f"Symbol: {analysis['symbol']}")
        print(f"Price: ${analysis['price']}")
        print(f"RSI: {analysis['rsi']}")
        print(f"MACD Signal: {analysis['macd_signal']}")
        print(f"Trend: {analysis['trend']}")
        print(f"Recommendation: {analysis['recommendation']}")
    
    # Example 3: Company overview
    print("\n=== Example 3: Company Overview ===")
    overview = advisor.get_company_overview('MSFT')
    if overview:
        print(f"Company: {overview.get('Name')}")
        print(f"Sector: {overview.get('Sector')}")
        print(f"Market Cap: {format_large_number(float(overview.get('MarketCapitalization', 0)))}")
    
    print("\n✅ Examples complete!")
