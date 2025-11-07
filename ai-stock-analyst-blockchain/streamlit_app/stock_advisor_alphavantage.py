"""
Stock Advisor using Alpha Vantage API (ROBUST VERSION)
======================================================
Complete stock data advisor with error handling, rate limiting, and API depletion detection.
Replaces Finnhub with Alpha Vantage for all stock data.

Features:
- Real-time quotes
- Technical indicators (RSI, MACD, SMA, EMA, Bollinger Bands, etc.)
- Fundamental data (Company overview, earnings, income statements)
- Historical OHLCV data (Daily, Weekly, Monthly, Intraday)
- Comprehensive error handling for 403, 401, 429, 500 errors
- API call tracking and depletion detection
- Intelligent rate limiting and caching
- Fallback mechanisms for failed requests

Author: Bhoomika M
Date: 2025-11-08
Version: 3.0 (Robust with 403 Handling & Depletion Detection)
"""

import requests
import time
from typing import Dict, Optional, List, Tuple, Any
import pandas as pd
from datetime import datetime, timedelta
import logging

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class APIUsageTracker:
    """
    Tracks API usage and detects when daily limit is approaching or depleted.
    """
    
    def __init__(self, daily_limit: int = 25):
        """
        Initialize API usage tracker.
        
        Args:
            daily_limit: Maximum calls per day (25 for free tier)
        """
        self.daily_limit = daily_limit
        self.calls_made = 0
        self.last_reset_date = datetime.now().date()
        self.call_history = []  # Track timestamps of each call
        self.rate_limit_hits = 0
        self.error_429_count = 0
        self.error_403_count = 0
        self.error_401_count = 0
    
    def add_call(self, symbol: str = "unknown", success: bool = True, 
                 error_code: Optional[int] = None):
        """
        Record an API call.
        
        Args:
            symbol: Stock symbol queried
            success: Whether call was successful
            error_code: HTTP error code if failed
        """
        current_date = datetime.now().date()
        
        # Reset if new day
        if current_date != self.last_reset_date:
            self.calls_made = 0
            self.call_history = []
            self.last_reset_date = current_date
            logger.info("🔄 Daily API limit reset (UTC midnight)")
        
        self.calls_made += 1
        self.call_history.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'success': success,
            'error_code': error_code
        })
        
        # Track specific errors
        if error_code == 429:
            self.error_429_count += 1
        elif error_code == 403:
            self.error_403_count += 1
        elif error_code == 401:
            self.error_401_count += 1
    
    def get_remaining_calls(self) -> int:
        """Get estimated remaining calls for today."""
        return max(0, self.daily_limit - self.calls_made)
    
    def is_depleted(self) -> bool:
        """Check if daily limit is depleted."""
        return self.calls_made >= self.daily_limit
    
    def is_near_limit(self, threshold: int = 5) -> bool:
        """Check if approaching daily limit."""
        return self.get_remaining_calls() <= threshold
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive usage status."""
        return {
            'calls_made': self.calls_made,
            'daily_limit': self.daily_limit,
            'remaining': self.get_remaining_calls(),
            'is_depleted': self.is_depleted(),
            'is_near_limit': self.is_near_limit(),
            'error_403_count': self.error_403_count,
            'error_401_count': self.error_401_count,
            'error_429_count': self.error_429_count,
            'rate_limit_hits': self.rate_limit_hits,
            'last_reset_date': str(self.last_reset_date)
        }
    
    def print_status(self):
        """Print human-readable status."""
        status = self.get_status()
        print("\n" + "=" * 80)
        print("📊 API USAGE STATUS")
        print("=" * 80)
        print(f"Calls Made:     {status['calls_made']}/{status['daily_limit']}")
        print(f"Remaining:      {status['remaining']}")
        print(f"Depleted:       {'⚠️ YES' if status['is_depleted'] else '✓ NO'}")
        print(f"Near Limit:     {'⚠️ YES' if status['is_near_limit'] else '✓ NO'}")
        print(f"403 Errors:     {status['error_403_count']}")
        print(f"401 Errors:     {status['error_401_count']}")
        print(f"429 Errors:     {status['error_429_count']}")
        print(f"Rate Limits:    {status['rate_limit_hits']}")
        print(f"Last Reset:     {status['last_reset_date']}")
        print("=" * 80 + "\n")


class StockAdvisorAlphaVantage:
    """
    Comprehensive stock advisor using Alpha Vantage API for:
    - Real-time quotes
    - Technical indicators (RSI, MACD, SMA, EMA, Bollinger Bands, etc.)
    - Fundamental data (Company overview, earnings, income statements)
    - Historical OHLCV data (Daily, Weekly, Monthly, Intraday)
    - Economic indicators
    
    Features:
    - Handles 403/401/429/500 errors gracefully
    - Tracks API depletion
    - Intelligent rate limiting (5 calls/minute, 25/day)
    - Response caching
    - Automatic retries
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
        self.usage_tracker = APIUsageTracker(daily_limit=25)
        
        logger.info(f"✓ StockAdvisorAlphaVantage initialized")
        logger.info(f"✓ API Key: {api_key[:10]}...")
        logger.info(f"✓ Rate limits: 5 calls/minute, 25 calls/day")
    
    def _rate_limit(self):
        """
        Implements rate limiting: 5 calls per minute for free tier.
        Automatically handles the 12-second delay between calls.
        """
        self.call_count += 1
        
        # Check if daily limit is depleted
        if self.usage_tracker.is_depleted():
            logger.warning("⚠️ DAILY API LIMIT DEPLETED (25/25 calls)")
            logger.warning("⏰ Wait until tomorrow (UTC midnight) or use premium tier")
            raise Exception("Daily API limit depleted. Please wait until tomorrow or upgrade API key.")
        
        # Check if near limit
        if self.usage_tracker.is_near_limit(threshold=3):
            remaining = self.usage_tracker.get_remaining_calls()
            logger.warning(f"⚠️ APPROACHING DAILY LIMIT: {remaining} calls remaining")
        
        # If we've made 5 calls, enforce 60-second wait
        if self.call_count >= 5:
            elapsed = time.time() - self.last_call_time
            if elapsed < 60:
                wait_time = 60 - elapsed
                logger.warning(f"⏳ Rate limited: {self.call_count} calls in {elapsed:.1f}s, waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                self.usage_tracker.rate_limit_hits += 1
            
            # Reset counter
            self.call_count = 0
            self.last_call_time = time.time()
        else:
            # Small delay between calls (12 seconds = 5 calls/minute)
            time.sleep(12)
    
    def _make_request(self, params: Dict, use_cache: bool = True, 
                     retry_count: int = 0, max_retries: int = 2) -> Optional[Dict]:
        """
        Makes an API request with rate limiting, caching, and comprehensive error handling.
        
        Handles:
        - 403 Forbidden (invalid API key)
        - 401 Unauthorized (expired key)
        - 429 Too Many Requests (rate limited)
        - 500 Server Error (temporary)
        - Timeouts and connection errors
        
        Args:
            params: Query parameters for the API
            use_cache: Whether to use cached response if available
            retry_count: Current retry attempt
            max_retries: Maximum retry attempts
            
        Returns:
            JSON response or None if error
        """
        symbol = params.get('symbol', 'unknown')
        
        # Create cache key
        cache_key = str(sorted(params.items()))
        
        # Check cache
        if use_cache and cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            # Cache valid for 1 hour
            if time.time() - cached_time < 3600:
                logger.debug(f"📦 Using cached data for {symbol}")
                return cached_data
        
        self._rate_limit()
        
        params['apikey'] = self.api_key
        
        try:
            logger.debug(f"Requesting {symbol} from Alpha Vantage...")
            response = requests.get(self.base_url, params=params, timeout=15)
            
            # Log response status
            logger.debug(f"Response status: {response.status_code} for {symbol}")
            
            # ===== HANDLE HTTP ERROR CODES =====
            
            if response.status_code == 403:
                logger.error(f"❌ 403 FORBIDDEN for {symbol}")
                logger.error(f"   Your API key may be invalid or expired")
                logger.error(f"   Response: {response.text[:300]}")
                self.usage_tracker.add_call(symbol, False, 403)
                return None
            
            elif response.status_code == 401:
                logger.error(f"❌ 401 UNAUTHORIZED for {symbol}")
                logger.error(f"   Invalid or expired API key")
                self.usage_tracker.add_call(symbol, False, 401)
                return None
            
            elif response.status_code == 429:
                logger.warning(f"⚠️ 429 TOO MANY REQUESTS for {symbol}")
                logger.warning(f"   Rate limit exceeded. Waiting 60 seconds...")
                self.usage_tracker.add_call(symbol, False, 429)
                time.sleep(60)
                
                # Retry once after waiting
                if retry_count < max_retries:
                    logger.info(f"Retrying {symbol} (attempt {retry_count + 1}/{max_retries})...")
                    return self._make_request(params, use_cache=False, 
                                            retry_count=retry_count + 1, max_retries=max_retries)
                return None
            
            elif response.status_code == 500:
                logger.warning(f"⚠️ 500 SERVER ERROR for {symbol}")
                logger.warning(f"   Alpha Vantage server error. Try again later.")
                self.usage_tracker.add_call(symbol, False, 500)
                
                # Retry with exponential backoff
                if retry_count < max_retries:
                    wait_time = (2 ** retry_count) * 5  # 5s, 10s, 20s
                    logger.info(f"Retrying {symbol} in {wait_time}s (attempt {retry_count + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    return self._make_request(params, use_cache=False,
                                            retry_count=retry_count + 1, max_retries=max_retries)
                return None
            
            elif response.status_code >= 400:
                logger.error(f"❌ HTTP Error {response.status_code} for {symbol}")
                logger.error(f"   Response: {response.text[:300]}")
                self.usage_tracker.add_call(symbol, False, response.status_code)
                return None
            
            # ===== PARSE JSON RESPONSE =====
            
            response.raise_for_status()  # Raises HTTPError for bad status codes
            data = response.json()
            
            # Check for API-level errors in JSON
            if 'Error Message' in data:
                logger.error(f"❌ API Error for {symbol}: {data['Error Message']}")
                self.usage_tracker.add_call(symbol, False, 403)  # Treat as auth error
                return None
            
            if 'Note' in data:  # Rate limit message
                logger.warning(f"⚠️ API Note: {data['Note']}")
                self.usage_tracker.add_call(symbol, False, 429)
                logger.info("Waiting 60 seconds and retrying...")
                time.sleep(60)
                
                if retry_count < max_retries:
                    return self._make_request(params, use_cache=False,
                                            retry_count=retry_count + 1, max_retries=max_retries)
                return None
            
            if 'Information' in data:  # Often API limit message
                logger.warning(f"ℹ️ API Info: {data['Information']}")
                self.usage_tracker.add_call(symbol, False, 429)
                return None
            
            # ===== SUCCESS =====
            
            # Cache the successful response
            self.cache[cache_key] = (data, time.time())
            self.usage_tracker.add_call(symbol, True)
            logger.debug(f"✓ Successfully retrieved data for {symbol}")
            
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ TIMEOUT for {symbol} - Server did not respond in time")
            self.usage_tracker.add_call(symbol, False, -1)
            
            if retry_count < max_retries:
                logger.info(f"Retrying {symbol} (attempt {retry_count + 1}/{max_retries})...")
                return self._make_request(params, use_cache=False,
                                        retry_count=retry_count + 1, max_retries=max_retries)
            return None
        
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ CONNECTION ERROR for {symbol} - Check internet connectivity")
            self.usage_tracker.add_call(symbol, False, -2)
            return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ REQUEST ERROR for {symbol}: {str(e)}")
            self.usage_tracker.add_call(symbol, False, -3)
            return None
        
        except Exception as e:
            logger.error(f"❌ UNEXPECTED ERROR for {symbol}: {type(e).__name__}: {str(e)}")
            self.usage_tracker.add_call(symbol, False, -999)
            return None
    
    # ==================== STOCK QUOTES ====================
    
    def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """
        Gets real-time quote for a stock.
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL', 'GOOGL')
            
        Returns:
            Dict with price, volume, change data or None if error
        """
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if not data or 'Global Quote' not in data:
            logger.warning(f"No Global Quote data for {symbol}")
            return None
        
        quote = data['Global Quote']
        
        if not quote or len(quote) == 0:
            logger.warning(f"Empty Global Quote for {symbol}")
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
            logger.error(f"Error parsing quote for {symbol}: {e}")
            return None
    
    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
        """
        Gets quotes for multiple stocks.
        
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
            logger.warning(f"No daily data for {symbol}")
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
            
            logger.debug(f"✓ Retrieved {len(df)} daily records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing daily data for {symbol}: {e}")
            return None
    
    def get_weekly_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Gets weekly time series data."""
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
            logger.error(f"Error parsing weekly data for {symbol}: {e}")
            return None
    
    def get_monthly_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Gets monthly time series data."""
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
            logger.error(f"Error parsing monthly data for {symbol}: {e}")
            return None
    
    def get_intraday_data(self, symbol: str, interval: str = '5min', 
                         outputsize: str = 'compact') -> Optional[pd.DataFrame]:
        """Gets intraday time series data."""
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
            logger.error(f"Error parsing intraday data for {symbol}: {e}")
            return None
    
    # ==================== TECHNICAL INDICATORS ====================
    
    def get_rsi(self, symbol: str, interval: str = 'daily', 
                time_period: int = 14) -> Optional[pd.DataFrame]:
        """Gets RSI (Relative Strength Index) technical indicator."""
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
            logger.error(f"Error parsing RSI for {symbol}: {e}")
            return None
    
    def get_macd(self, symbol: str, interval: str = 'daily',
                 fastperiod: int = 12, slowperiod: int = 26,
                 signalperiod: int = 9) -> Optional[pd.DataFrame]:
        """Gets MACD (Moving Average Convergence Divergence) indicator."""
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
            logger.error(f"Error parsing MACD for {symbol}: {e}")
            return None
    
    def get_sma(self, symbol: str, interval: str = 'daily', 
                time_period: int = 50) -> Optional[pd.DataFrame]:
        """Gets SMA (Simple Moving Average)."""
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
            logger.error(f"Error parsing SMA for {symbol}: {e}")
            return None
    
    def get_ema(self, symbol: str, interval: str = 'daily', 
                time_period: int = 50) -> Optional[pd.DataFrame]:
        """Gets EMA (Exponential Moving Average)."""
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
            logger.error(f"Error parsing EMA for {symbol}: {e}")
            return None
    
    def get_bbands(self, symbol: str, interval: str = 'daily',
                   time_period: int = 20, nbdevup: int = 2,
                   nbdevdn: int = 2) -> Optional[pd.DataFrame]:
        """Gets Bollinger Bands."""
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
            logger.error(f"Error parsing Bollinger Bands for {symbol}: {e}")
            return None
    
    def get_stoch(self, symbol: str, interval: str = 'daily') -> Optional[pd.DataFrame]:
        """Gets Stochastic Oscillator."""
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
            logger.error(f"Error parsing Stochastic for {symbol}: {e}")
            return None
    
    def get_adx(self, symbol: str, interval: str = 'daily',
                time_period: int = 14) -> Optional[pd.DataFrame]:
        """Gets ADX (Average Directional Index)."""
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
            logger.error(f"Error parsing ADX for {symbol}: {e}")
            return None
    
    def get_cci(self, symbol: str, interval: str = 'daily',
                time_period: int = 20) -> Optional[pd.DataFrame]:
        """Gets CCI (Commodity Channel Index)."""
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
            logger.error(f"Error parsing CCI for {symbol}: {e}")
            return None
    
    def get_obv(self, symbol: str, interval: str = 'daily') -> Optional[pd.DataFrame]:
        """Gets OBV (On-Balance Volume)."""
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
            logger.error(f"Error parsing OBV for {symbol}: {e}")
            return None
    
    # ==================== FUNDAMENTAL DATA ====================
    
    def get_company_overview(self, symbol: str) -> Optional[Dict]:
        """Gets comprehensive company information and fundamentals."""
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if not data or 'Symbol' not in data:
            logger.warning(f"No company overview for {symbol}")
            return None
        
        return data
    
    def get_earnings(self, symbol: str) -> Optional[Dict]:
        """Gets annual and quarterly earnings data."""
        params = {
            'function': 'EARNINGS',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if not data or 'symbol' not in data:
            logger.warning(f"No earnings data for {symbol}")
            return None
        
        return data
    
    def get_income_statement(self, symbol: str) -> Optional[Dict]:
        """Gets annual and quarterly income statements."""
        params = {
            'function': 'INCOME_STATEMENT',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if not data or 'symbol' not in data:
            logger.warning(f"No income statement for {symbol}")
            return None
        
        return data
    
    def get_balance_sheet(self, symbol: str) -> Optional[Dict]:
        """Gets annual and quarterly balance sheets."""
        params = {
            'function': 'BALANCE_SHEET',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if not data or 'symbol' not in data:
            logger.warning(f"No balance sheet for {symbol}")
            return None
        
        return data
    
    def get_cash_flow(self, symbol: str) -> Optional[Dict]:
        """Gets annual and quarterly cash flow statements."""
        params = {
            'function': 'CASH_FLOW',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        
        if not data or 'symbol' not in data:
            logger.warning(f"No cash flow data for {symbol}")
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
            Dict with technical analysis results
        """
        logger.info(f"📊 Starting technical analysis for {symbol}...")
        
        try:
            # Get quote
            quote = self.get_stock_quote(symbol)
            if not quote:
                logger.error(f"Failed to get quote for {symbol}")
                return None
            
            logger.debug(f"✓ Quote retrieved for {symbol}: ${quote['price']}")
            
            # Get RSI
            rsi_df = self.get_rsi(symbol)
            latest_rsi = None
            if rsi_df is not None and len(rsi_df) > 0:
                latest_rsi = float(rsi_df.iloc[-1]['RSI'])
                logger.debug(f"✓ RSI: {latest_rsi:.2f}")
            
            # Get MACD
            macd_df = self.get_macd(symbol)
            macd_signal = None
            if macd_df is not None and len(macd_df) > 0:
                latest_macd = macd_df.iloc[-1]
                macd_signal = 'BUY' if float(latest_macd['MACD']) > float(latest_macd['MACD_Signal']) else 'SELL'
                logger.debug(f"✓ MACD Signal: {macd_signal}")
            
            # Get SMAs for trend analysis
            sma_50 = self.get_sma(symbol, time_period=50)
            sma_200 = self.get_sma(symbol, time_period=200)
            
            trend = None
            if sma_50 is not None and sma_200 is not None and len(sma_50) > 0 and len(sma_200) > 0:
                sma_50_val = float(sma_50.iloc[-1]['SMA'])
                sma_200_val = float(sma_200.iloc[-1]['SMA'])
                trend = 'BULLISH' if sma_50_val > sma_200_val else 'BEARISH'
                logger.debug(f"✓ Trend: {trend} (SMA50: {sma_50_val:.2f}, SMA200: {sma_200_val:.2f})")
            
            # Generate recommendation
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
            
            logger.info(f"✅ Analysis complete for {symbol}: {recommendation}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {type(e).__name__}: {e}", exc_info=True)
            return None
    
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
            if rsi < 30:  # Oversold
                buy_signals += 2
            elif rsi > 70:  # Overbought
                sell_signals += 2
            elif 40 < rsi < 60:  # Neutral
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
        """Gets complete analysis including technical AND fundamental data."""
        logger.info(f"🔍 Performing full analysis on {symbol}...")
        
        try:
            result = {
                'symbol': symbol,
                'technical': self.analyze_stock_technical(symbol),
                'overview': self.get_company_overview(symbol),
                'earnings': self.get_earnings(symbol)
            }
            return result
        except Exception as e:
            logger.error(f"Error in full analysis for {symbol}: {e}")
            return None
    
    # ==================== UTILITY FUNCTIONS ====================
    
    def search_symbol(self, keywords: str) -> Optional[List[Dict]]:
        """Searches for stock symbols by company name or keywords."""
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': keywords
        }
        
        data = self._make_request(params)
        
        if not data or 'bestMatches' not in data:
            logger.warning(f"No search results for '{keywords}'")
            return None
        
        return data['bestMatches']
    
    def clear_cache(self):
        """Clears the internal cache."""
        self.cache = {}
        logger.info("🗑️ Cache cleared")
    
    def get_cache_size(self) -> int:
        """Returns the number of cached responses."""
        return len(self.cache)
    
    def get_usage_status(self) -> Dict[str, Any]:
        """Get API usage status."""
        return self.usage_tracker.get_status()
    
    def print_usage_status(self):
        """Print API usage status."""
        self.usage_tracker.print_status()
    
    def is_api_depleted(self) -> bool:
        """Check if daily API limit is depleted."""
        return self.usage_tracker.is_depleted()
    
    def get_remaining_calls(self) -> int:
        """Get remaining API calls for today."""
        return self.usage_tracker.get_remaining_calls()


# ==================== HELPER FUNCTIONS ====================

def format_large_number(num: float) -> str:
    """Formats large numbers into readable strings."""
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
    """Calculates percentage return between two prices."""
    if start_price == 0:
        return 0.0
    return ((end_price - start_price) / start_price) * 100


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    """Example usage and testing."""
    
    API_KEY = "ZRBAZ10IY283K3T7"
    advisor = StockAdvisorAlphaVantage(API_KEY)
    
    print("\n" + "=" * 80)
    print("STOCK ADVISOR - ALPHA VANTAGE")
    print("=" * 80)
    
    # Example 1: Get a stock quote
    print("\n=== Example 1: Stock Quote ===")
    quote = advisor.get_stock_quote('AAPL')
    if quote:
        print(f"✓ AAPL Price: ${quote['price']}")
        print(f"  Change: {quote['change_percent']}%")
    
    # Example 2: Technical analysis
    print("\n=== Example 2: Technical Analysis ===")
    analysis = advisor.analyze_stock_technical('MSFT')
    if analysis:
        print(f"✓ Symbol: {analysis['symbol']}")
        print(f"  Price: ${analysis['price']}")
        print(f"  RSI: {analysis['rsi']}")
        print(f"  MACD: {analysis['macd_signal']}")
        print(f"  Trend: {analysis['trend']}")
        print(f"  Recommendation: {analysis['recommendation']}")
    
    # Show API usage
    print("\n=== API Usage ===")
    advisor.print_usage_status()
    
    print("\n✅ Examples complete!")
