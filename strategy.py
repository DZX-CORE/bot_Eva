"""
Trading Strategy Module
Implements the trend following strategy with multiple confirmation signals
"""

import logging
from typing import Dict, Any, List
from indicators import TechnicalIndicators


class TrendFollowingStrategy:
    """Trend following strategy with multiple confirmation signals"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize strategy with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.indicators_config = config['indicators']
        self.risk_config = config['risk_management']
    
    def get_entry_signal(self, market_data: Dict, indicators: Dict) -> Dict[str, Any]:
        """
        Analyze market conditions and return entry signal
        Returns: {'action': 'BUY'/'SELL'/'NONE', 'confidence': float, 'reasons': list}
        """
        try:
            current_price = market_data['close'][-1]
            
            # Initialize signal
            signal = {
                'action': 'NONE',
                'confidence': 0.0,
                'reasons': []
            }
            
            # Check bullish conditions
            bullish_conditions = self._check_bullish_conditions(current_price, indicators)
            bearish_conditions = self._check_bearish_conditions(current_price, indicators)
            
            if bullish_conditions['valid']:
                signal['action'] = 'BUY'
                signal['confidence'] = bullish_conditions['confidence']
                signal['reasons'] = bullish_conditions['reasons']
                
            elif bearish_conditions['valid']:
                signal['action'] = 'SELL'
                signal['confidence'] = bearish_conditions['confidence']
                signal['reasons'] = bearish_conditions['reasons']
            
            self.logger.info(f"Entry signal: {signal['action']} (confidence: {signal['confidence']:.2f})")
            return signal
            
        except Exception as e:
            self.logger.error(f"Error generating entry signal: {e}")
            return {'action': 'NONE', 'confidence': 0.0, 'reasons': []}
    
    def _check_bullish_conditions(self, price: float, indicators: Dict) -> Dict:
        """Check all bullish entry conditions"""
        conditions = []
        reasons = []
        
        # 1. Trend: Price above EMA 200
        if price > indicators['ema_200']:
            conditions.append(True)
            reasons.append("Price above EMA 200 (bullish trend)")
        else:
            conditions.append(False)
            reasons.append("Price below EMA 200 (not bullish trend)")
        
        # 2. MACD: Histogram positive
        if indicators['macd_histogram'] > 0:
            conditions.append(True)
            reasons.append("MACD histogram positive (bullish momentum)")
        else:
            conditions.append(False)
            reasons.append("MACD histogram negative (not bullish momentum)")
        
        # 3. RSI: Not overbought (< 70)
        if indicators['rsi'] < 70:
            conditions.append(True)
            reasons.append(f"RSI {indicators['rsi']:.1f} not overbought")
        else:
            conditions.append(False)
            reasons.append(f"RSI {indicators['rsi']:.1f} overbought")
        
        # 4. Volume: Above average
        if indicators['volume_ratio'] > self.indicators_config['volume_multiplier']:
            conditions.append(True)
            reasons.append(f"Volume {indicators['volume_ratio']:.1f}x above average")
        else:
            conditions.append(False)
            reasons.append(f"Volume {indicators['volume_ratio']:.1f}x below threshold")
        
        # 5. Trend strength (ADX)
        min_adx = self.risk_config.get('min_adx_for_trend', 25)
        if indicators['adx'] >= min_adx:
            conditions.append(True)
            reasons.append(f"ADX {indicators['adx']:.1f} shows strong trend")
        else:
            conditions.append(False)
            reasons.append(f"ADX {indicators['adx']:.1f} shows weak trend")
        
        # All conditions must be met
        all_valid = all(conditions)
        confidence = sum(conditions) / len(conditions)
        
        return {
            'valid': all_valid,
            'confidence': confidence,
            'reasons': reasons
        }
    
    def _check_bearish_conditions(self, price: float, indicators: Dict) -> Dict:
        """Check all bearish entry conditions"""
        conditions = []
        reasons = []
        
        # 1. Trend: Price below EMA 200
        if price < indicators['ema_200']:
            conditions.append(True)
            reasons.append("Price below EMA 200 (bearish trend)")
        else:
            conditions.append(False)
            reasons.append("Price above EMA 200 (not bearish trend)")
        
        # 2. MACD: Histogram negative
        if indicators['macd_histogram'] < 0:
            conditions.append(True)
            reasons.append("MACD histogram negative (bearish momentum)")
        else:
            conditions.append(False)
            reasons.append("MACD histogram positive (not bearish momentum)")
        
        # 3. RSI: Not oversold (> 30)
        if indicators['rsi'] > 30:
            conditions.append(True)
            reasons.append(f"RSI {indicators['rsi']:.1f} not oversold")
        else:
            conditions.append(False)
            reasons.append(f"RSI {indicators['rsi']:.1f} oversold")
        
        # 4. Volume: Above average
        if indicators['volume_ratio'] > self.indicators_config['volume_multiplier']:
            conditions.append(True)
            reasons.append(f"Volume {indicators['volume_ratio']:.1f}x above average")
        else:
            conditions.append(False)
            reasons.append(f"Volume {indicators['volume_ratio']:.1f}x below threshold")
        
        # 5. Trend strength (ADX)
        min_adx = self.risk_config.get('min_adx_for_trend', 25)
        if indicators['adx'] >= min_adx:
            conditions.append(True)
            reasons.append(f"ADX {indicators['adx']:.1f} shows strong trend")
        else:
            conditions.append(False)
            reasons.append(f"ADX {indicators['adx']:.1f} shows weak trend")
        
        # All conditions must be met
        all_valid = all(conditions)
        confidence = sum(conditions) / len(conditions)
        
        return {
            'valid': all_valid,
            'confidence': confidence,
            'reasons': reasons
        }
    
    def validate_orderbook_pressure(self, orderbook: Dict, action: str) -> bool:
        """
        Validate order book pressure supports the intended action
        """
        try:
            if not orderbook or 'bids' not in orderbook or 'asks' not in orderbook:
                return False
            
            # Get top 5 levels
            levels = self.config['execution']['orderbook_levels']
            bids = orderbook['bids'][:levels]
            asks = orderbook['asks'][:levels]
            
            # Calculate total bid and ask volumes
            total_bid_volume = sum(float(bid[1]) for bid in bids)
            total_ask_volume = sum(float(ask[1]) for ask in asks)
            
            if action == 'BUY':
                # For buy orders, we want more bid pressure (buying interest)
                pressure_valid = total_bid_volume > total_ask_volume
                self.logger.info(f"Buy pressure check: Bids={total_bid_volume:.2f}, Asks={total_ask_volume:.2f}, Valid={pressure_valid}")
                
            elif action == 'SELL':
                # For sell orders, we want more ask pressure (selling interest)
                pressure_valid = total_ask_volume > total_bid_volume
                self.logger.info(f"Sell pressure check: Bids={total_bid_volume:.2f}, Asks={total_ask_volume:.2f}, Valid={pressure_valid}")
                
            else:
                pressure_valid = False
            
            return pressure_valid
            
        except Exception as e:
            self.logger.error(f"Error validating orderbook pressure: {e}")
            return False
    
    def get_exit_signal(self, market_data: Dict, indicators: Dict, position: Dict) -> Dict[str, Any]:
        """
        Check if current position should be exited
        Returns: {'should_exit': bool, 'reason': str}
        """
        try:
            current_price = market_data['close'][-1]
            position_side = position['side']
            entry_price = position['entry_price']
            
            # Check stop loss and take profit (handled by executor)
            # Here we check for strategy-based exits
            
            # Exit on trend reversal
            if position_side == 'BUY':
                # Exit long position if trend turns bearish
                if (current_price < indicators['ema_200'] and 
                    indicators['macd_histogram'] < 0 and
                    indicators['rsi'] > 70):
                    return {'should_exit': True, 'reason': 'Trend reversal (bearish)'}
                    
            elif position_side == 'SELL':
                # Exit short position if trend turns bullish
                if (current_price > indicators['ema_200'] and 
                    indicators['macd_histogram'] > 0 and
                    indicators['rsi'] < 30):
                    return {'should_exit': True, 'reason': 'Trend reversal (bullish)'}
            
            # Exit on weak trend
            if indicators['adx'] < 20:
                return {'should_exit': True, 'reason': 'Weak trend (ADX < 20)'}
            
            return {'should_exit': False, 'reason': 'No exit signal'}
            
        except Exception as e:
            self.logger.error(f"Error checking exit signal: {e}")
            return {'should_exit': False, 'reason': 'Error in exit analysis'}
