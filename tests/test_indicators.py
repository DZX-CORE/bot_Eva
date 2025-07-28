"""
Unit tests for technical indicators
"""

import unittest
import pandas as pd
import numpy as np
from indicators import TechnicalIndicators


class TestTechnicalIndicators(unittest.TestCase):
    """Test cases for technical indicators"""
    
    def setUp(self):
        """Set up test data"""
        self.config = {
            'ema_period': 20,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'rsi_period': 14,
            'atr_period': 14,
            'volume_period': 20,
            'volume_multiplier': 1.5,
            'adx_period': 14
        }
        
        self.indicators = TechnicalIndicators(self.config)
        
        # Create sample market data
        np.random.seed(42)  # For reproducible tests
        dates = pd.date_range('2023-01-01', periods=100, freq='5T')
        
        # Generate realistic price data
        price_base = 50000
        price_changes = np.random.normal(0, 0.01, 100)
        prices = [price_base]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        self.market_data = {
            'timestamp': [int(d.timestamp() * 1000) for d in dates],
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
            'close': prices,
            'volume': [np.random.uniform(100, 1000) for _ in range(100)]
        }
    
    def test_calculate_ema(self):
        """Test EMA calculation"""
        prices = pd.Series(self.market_data['close'])
        ema = self.indicators.calculate_ema(prices, 20)
        
        self.assertIsInstance(ema, pd.Series)
        self.assertEqual(len(ema), len(prices))
        self.assertFalse(ema.iloc[-1] == 0)  # Should have valid values
    
    def test_calculate_macd(self):
        """Test MACD calculation"""
        prices = pd.Series(self.market_data['close'])
        macd_data = self.indicators.calculate_macd(prices, 12, 26, 9)
        
        self.assertIn('macd', macd_data)
        self.assertIn('macd_signal', macd_data)
        self.assertIn('macd_histogram', macd_data)
        
        # Check that all series have the same length
        for key, series in macd_data.items():
            self.assertEqual(len(series), len(prices))
    
    def test_calculate_rsi(self):
        """Test RSI calculation"""
        prices = pd.Series(self.market_data['close'])
        rsi = self.indicators.calculate_rsi(prices, 14)
        
        self.assertIsInstance(rsi, pd.Series)
        self.assertEqual(len(rsi), len(prices))
        
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        self.assertTrue(all(0 <= val <= 100 for val in valid_rsi))
    
    def test_calculate_atr(self):
        """Test ATR calculation"""
        high = pd.Series(self.market_data['high'])
        low = pd.Series(self.market_data['low'])
        close = pd.Series(self.market_data['close'])
        
        atr = self.indicators.calculate_atr(high, low, close, 14)
        
        self.assertIsInstance(atr, pd.Series)
        self.assertEqual(len(atr), len(close))
        
        # ATR should be positive
        valid_atr = atr.dropna()
        self.assertTrue(all(val >= 0 for val in valid_atr))
    
    def test_calculate_all(self):
        """Test calculating all indicators at once"""
        indicators = self.indicators.calculate_all(self.market_data)
        
        expected_keys = [
            'ema_200', 'macd', 'macd_signal', 'macd_histogram',
            'rsi', 'atr', 'volume_ratio', 'adx'
        ]
        
        for key in expected_keys:
            self.assertIn(key, indicators)
            self.assertIsNotNone(indicators[key])
    
    def test_trend_detection(self):
        """Test trend detection methods"""
        price = 50000
        ema_200 = 49000
        
        # Test bullish trend
        self.assertTrue(self.indicators.is_trend_bullish(price, ema_200))
        self.assertFalse(self.indicators.is_trend_bearish(price, ema_200))
        
        # Test bearish trend
        price = 48000
        self.assertFalse(self.indicators.is_trend_bullish(price, ema_200))
        self.assertTrue(self.indicators.is_trend_bearish(price, ema_200))
    
    def test_macd_signals(self):
        """Test MACD signal detection"""
        # Test bullish MACD
        self.assertTrue(self.indicators.is_macd_bullish(0.5))
        self.assertFalse(self.indicators.is_macd_bearish(0.5))
        
        # Test bearish MACD
        self.assertFalse(self.indicators.is_macd_bullish(-0.5))
        self.assertTrue(self.indicators.is_macd_bearish(-0.5))
    
    def test_rsi_levels(self):
        """Test RSI overbought/oversold detection"""
        # Test oversold
        self.assertTrue(self.indicators.is_rsi_oversold(25))
        self.assertFalse(self.indicators.is_rsi_overbought(25))
        
        # Test overbought
        self.assertFalse(self.indicators.is_rsi_oversold(75))
        self.assertTrue(self.indicators.is_rsi_overbought(75))
        
        # Test neutral
        self.assertFalse(self.indicators.is_rsi_oversold(50))
        self.assertFalse(self.indicators.is_rsi_overbought(50))
    
    def test_volume_confirmation(self):
        """Test volume confirmation"""
        # Volume above threshold
        self.assertTrue(self.indicators.has_volume_confirmation(2.0))
        
        # Volume below threshold
        self.assertFalse(self.indicators.has_volume_confirmation(1.0))
    
    def test_trend_strength(self):
        """Test trend strength classification"""
        self.assertEqual(self.indicators.get_trend_strength(15), "WEAK")
        self.assertEqual(self.indicators.get_trend_strength(35), "MODERATE")
        self.assertEqual(self.indicators.get_trend_strength(65), "STRONG")


if __name__ == '__main__':
    unittest.main()
