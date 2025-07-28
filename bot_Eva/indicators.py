"""
Technical Indicators Module
Implements all technical analysis indicators used by the trading strategy
"""

import pandas as pd
import numpy as np
import ta
from typing import Dict, List, Any
import logging


class TechnicalIndicators:
    """Class for calculating technical indicators"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with indicator configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def calculate_all(self, market_data: Dict) -> Dict[str, Any]:
        """Calculate all required technical indicators"""
        try:
            df = pd.DataFrame(market_data)
            
            indicators = {}
            
            # Exponential Moving Average
            indicators['ema_200'] = self.calculate_ema(df['close'], self.config['ema_period'])
            
            # MACD
            macd_data = self.calculate_macd(
                df['close'],
                self.config['macd_fast'],
                self.config['macd_slow'],
                self.config['macd_signal']
            )
            indicators.update(macd_data)
            
            # RSI
            indicators['rsi'] = self.calculate_rsi(df['close'], self.config['rsi_period'])
            
            # ATR (Average True Range)
            indicators['atr'] = self.calculate_atr(
                df['high'], df['low'], df['close'], self.config['atr_period']
            )
            
            # Volume analysis
            indicators['volume_ma'] = self.calculate_volume_ma(df['volume'], self.config['volume_period'])
            indicators['volume_ratio'] = df['volume'].iloc[-1] / indicators['volume_ma'].iloc[-1]
            
            # ADX for trend strength
            indicators['adx'] = self.calculate_adx(
                df['high'], df['low'], df['close'], self.config.get('adx_period', 14)
            )
            
            # Current values (most recent)
            current_indicators = {
                'ema_200': indicators['ema_200'].iloc[-1],
                'macd': indicators['macd'].iloc[-1],
                'macd_signal': indicators['macd_signal'].iloc[-1],
                'macd_histogram': indicators['macd_histogram'].iloc[-1],
                'rsi': indicators['rsi'].iloc[-1],
                'atr': indicators['atr'].iloc[-1],
                'volume_ratio': indicators['volume_ratio'],
                'adx': indicators['adx'].iloc[-1]
            }
            
            return current_indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return {}
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return ta.trend.ema_indicator(close=prices, window=period)
    
    def calculate_macd(self, prices: pd.Series, fast: int, slow: int, signal: int) -> Dict[str, pd.Series]:
        """Calculate MACD indicator"""
        return {
            'macd': ta.trend.macd(close=prices, window_fast=fast, window_slow=slow),
            'macd_signal': ta.trend.macd_signal(close=prices, window_fast=fast, window_slow=slow, window_sign=signal),
            'macd_histogram': ta.trend.macd_diff(close=prices, window_fast=fast, window_slow=slow, window_sign=signal)
        }
    
    def calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Relative Strength Index"""
        return ta.momentum.rsi(close=prices, window=period)
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        """Calculate Average True Range"""
        return ta.volatility.average_true_range(high=high, low=low, close=close, window=period)
    
    def calculate_volume_ma(self, volume: pd.Series, period: int) -> pd.Series:
        """Calculate Volume Moving Average"""
        return volume.rolling(window=period).mean()
    
    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        """Calculate Average Directional Index"""
        return ta.trend.adx(high=high, low=low, close=close, window=period)
    
    def is_trend_bullish(self, price: float, ema_200: float) -> bool:
        """Check if trend is bullish based on EMA 200"""
        return price > ema_200
    
    def is_trend_bearish(self, price: float, ema_200: float) -> bool:
        """Check if trend is bearish based on EMA 200"""
        return price < ema_200
    
    def is_macd_bullish(self, macd_histogram: float) -> bool:
        """Check if MACD shows bullish momentum"""
        return macd_histogram > 0
    
    def is_macd_bearish(self, macd_histogram: float) -> bool:
        """Check if MACD shows bearish momentum"""
        return macd_histogram < 0
    
    def is_rsi_oversold(self, rsi: float, threshold: float = 30) -> bool:
        """Check if RSI indicates oversold conditions"""
        return rsi < threshold
    
    def is_rsi_overbought(self, rsi: float, threshold: float = 70) -> bool:
        """Check if RSI indicates overbought conditions"""
        return rsi > threshold
    
    def has_volume_confirmation(self, volume_ratio: float) -> bool:
        """Check if volume confirms the move"""
        return volume_ratio > self.config['volume_multiplier']
    
    def get_trend_strength(self, adx: float) -> str:
        """Determine trend strength based on ADX"""
        if adx < 25:
            return "WEAK"
        elif adx < 50:
            return "MODERATE"
        else:
            return "STRONG"
