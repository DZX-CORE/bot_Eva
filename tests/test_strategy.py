"""
Unit tests for trading strategy
"""

import unittest
from unittest.mock import Mock, patch
from strategy import TrendFollowingStrategy


class TestTrendFollowingStrategy(unittest.TestCase):
    """Test cases for trading strategy"""
    
    def setUp(self):
        """Set up test data"""
        self.config = {
            'trading': {
                'symbol': 'BTCUSDT',
                'risk_per_trade': 0.01
            },
            'indicators': {
                'volume_multiplier': 1.5
            },
            'risk_management': {
                'min_adx_for_trend': 25
            },
            'execution': {
                'orderbook_levels': 5
            }
        }
        
        self.strategy = TrendFollowingStrategy(self.config)
        
        # Sample market data
        self.market_data = {
            'close': [49000, 49500, 50000, 50500, 51000]
        }
        
        # Sample indicators for bullish scenario
        self.bullish_indicators = {
            'ema_200': 48000,
            'macd_histogram': 0.5,
            'rsi': 65,
            'volume_ratio': 2.0,
            'adx': 30
        }
        
        # Sample indicators for bearish scenario
        self.bearish_indicators = {
            'ema_200': 52000,
            'macd_histogram': -0.5,
            'rsi': 35,
            'volume_ratio': 2.0,
            'adx': 30
        }
    
    def test_bullish_entry_signal(self):
        """Test bullish entry signal generation"""
        signal = self.strategy.get_entry_signal(self.market_data, self.bullish_indicators)
        
        self.assertEqual(signal['action'], 'BUY')
        self.assertEqual(signal['confidence'], 1.0)  # All conditions met
        self.assertIn('reasons', signal)
        self.assertGreater(len(signal['reasons']), 0)
    
    def test_bearish_entry_signal(self):
        """Test bearish entry signal generation"""
        signal = self.strategy.get_entry_signal(self.market_data, self.bearish_indicators)
        
        self.assertEqual(signal['action'], 'SELL')
        self.assertEqual(signal['confidence'], 1.0)  # All conditions met
        self.assertIn('reasons', signal)
        self.assertGreater(len(signal['reasons']), 0)
    
    def test_no_signal_mixed_conditions(self):
        """Test no signal when conditions are mixed"""
        mixed_indicators = {
            'ema_200': 48000,  # Bullish
            'macd_histogram': -0.5,  # Bearish
            'rsi': 65,
            'volume_ratio': 2.0,
            'adx': 30
        }
        
        signal = self.strategy.get_entry_signal(self.market_data, mixed_indicators)
        
        self.assertEqual(signal['action'], 'NONE')
        self.assertLess(signal['confidence'], 1.0)
    
    def test_no_signal_low_volume(self):
        """Test no signal when volume is insufficient"""
        low_volume_indicators = self.bullish_indicators.copy()
        low_volume_indicators['volume_ratio'] = 1.0  # Below threshold
        
        signal = self.strategy.get_entry_signal(self.market_data, low_volume_indicators)
        
        self.assertEqual(signal['action'], 'NONE')
    
    def test_no_signal_weak_trend(self):
        """Test no signal when trend is weak (low ADX)"""
        weak_trend_indicators = self.bullish_indicators.copy()
        weak_trend_indicators['adx'] = 15  # Below threshold
        
        signal = self.strategy.get_entry_signal(self.market_data, weak_trend_indicators)
        
        self.assertEqual(signal['action'], 'NONE')
    
    def test_orderbook_validation_buy(self):
        """Test order book validation for buy orders"""
        orderbook = {
            'bids': [['50000', '1.0'], ['49950', '0.5'], ['49900', '0.3']],
            'asks': [['50050', '0.5'], ['50100', '0.3'], ['50150', '0.2']]
        }
        
        # More bid volume than ask volume - should validate buy
        result = self.strategy.validate_orderbook_pressure(orderbook, 'BUY')
        self.assertTrue(result)
    
    def test_orderbook_validation_sell(self):
        """Test order book validation for sell orders"""
        orderbook = {
            'bids': [['50000', '0.3'], ['49950', '0.2'], ['49900', '0.1']],
            'asks': [['50050', '1.0'], ['50100', '0.8'], ['50150', '0.5']]
        }
        
        # More ask volume than bid volume - should validate sell
        result = self.strategy.validate_orderbook_pressure(orderbook, 'SELL')
        self.assertTrue(result)
    
    def test_orderbook_validation_insufficient_pressure(self):
        """Test order book validation with insufficient pressure"""
        orderbook = {
            'bids': [['50000', '1.0'], ['49950', '0.5']],
            'asks': [['50050', '1.2'], ['50100', '0.8']]
        }
        
        # More ask volume - should not validate buy
        result = self.strategy.validate_orderbook_pressure(orderbook, 'BUY')
        self.assertFalse(result)
    
    def test_exit_signal_trend_reversal_long(self):
        """Test exit signal for long position on trend reversal"""
        position = {
            'side': 'BUY',
            'entry_price': 50000
        }
        
        # Bearish reversal indicators
        reversal_indicators = {
            'ema_200': 52000,  # Price below EMA
            'macd_histogram': -0.5,  # Bearish momentum
            'rsi': 75,  # Overbought
            'adx': 30
        }
        
        # Current price below EMA
        reversal_market_data = {
            'close': [51000, 50500, 50000, 49500, 49000]
        }
        
        exit_signal = self.strategy.get_exit_signal(
            reversal_market_data, reversal_indicators, position
        )
        
        self.assertTrue(exit_signal['should_exit'])
        self.assertIn('reversal', exit_signal['reason'].lower())
    
    def test_exit_signal_trend_reversal_short(self):
        """Test exit signal for short position on trend reversal"""
        position = {
            'side': 'SELL',
            'entry_price': 50000
        }
        
        # Bullish reversal indicators
        reversal_indicators = {
            'ema_200': 48000,  # Price above EMA
            'macd_histogram': 0.5,  # Bullish momentum
            'rsi': 25,  # Oversold
            'adx': 30
        }
        
        # Current price above EMA
        reversal_market_data = {
            'close': [49000, 49500, 50000, 50500, 51000]
        }
        
        exit_signal = self.strategy.get_exit_signal(
            reversal_market_data, reversal_indicators, position
        )
        
        self.assertTrue(exit_signal['should_exit'])
        self.assertIn('reversal', exit_signal['reason'].lower())
    
    def test_exit_signal_weak_trend(self):
        """Test exit signal on weak trend (low ADX)"""
        position = {'side': 'BUY', 'entry_price': 50000}
        
        weak_trend_indicators = {
            'ema_200': 48000,
            'macd_histogram': 0.1,
            'rsi': 50,
            'adx': 15  # Below threshold
        }
        
        exit_signal = self.strategy.get_exit_signal(
            self.market_data, weak_trend_indicators, position
        )
        
        self.assertTrue(exit_signal['should_exit'])
        self.assertIn('weak trend', exit_signal['reason'].lower())
    
    def test_no_exit_signal(self):
        """Test no exit signal when conditions are favorable"""
        position = {'side': 'BUY', 'entry_price': 50000}
        
        favorable_indicators = {
            'ema_200': 48000,  # Bullish trend continues
            'macd_histogram': 0.3,  # Still bullish
            'rsi': 60,  # Not overbought
            'adx': 35  # Strong trend
        }
        
        exit_signal = self.strategy.get_exit_signal(
            self.market_data, favorable_indicators, position
        )
        
        self.assertFalse(exit_signal['should_exit'])


if __name__ == '__main__':
    unittest.main()
