"""
Adaptive Risk Management Module
Handles position sizing, stop losses, and risk calculations based on volatility
"""

import logging
from typing import Dict, Any
import math


class AdaptiveRiskManager:
    """Adaptive risk management based on market volatility"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize risk manager with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def calculate_position_size(self, account_balance: float, price: float, atr: float) -> Dict[str, Any]:
        """
        Calculate position size based on fixed risk percentage and volatility
        Formula: position_size = (capital_total * risk_percent) / (atr_multiplier * ATR)
        """
        try:
            # Risk amount (1% of capital)
            risk_amount = account_balance * 0.01  # 1% risk per trade
            
            # Stop loss distance (1.5 * ATR)
            stop_distance = self.config['atr_stop_multiplier'] * atr
            
            # Calculate position size
            position_size = risk_amount / stop_distance
            
            # Calculate stop loss and take profit prices
            stop_loss_long = price - stop_distance
            stop_loss_short = price + stop_distance
            
            # Take profit distance (3.0 * ATR for 1:2 R:R)
            target_distance = self.config['atr_target_multiplier'] * atr
            take_profit_long = price + target_distance
            take_profit_short = price - target_distance
            
            # Ensure minimum position size constraints
            min_notional = 10.0  # Minimum $10 position
            if position_size * price < min_notional:
                position_size = min_notional / price
                self.logger.warning(f"Position size adjusted to meet minimum notional requirement")
            
            # Round to appropriate precision
            position_size = self._round_quantity(position_size)
            
            risk_params = {
                'quantity': position_size,
                'risk_amount': risk_amount,
                'stop_distance': stop_distance,
                'target_distance': target_distance,
                'stop_loss_long': round(stop_loss_long, 8),
                'stop_loss_short': round(stop_loss_short, 8),
                'take_profit_long': round(take_profit_long, 8),
                'take_profit_short': round(take_profit_short, 8),
                'risk_reward_ratio': target_distance / stop_distance
            }
            
            self.logger.info(f"Position size calculated: {position_size}, Risk: ${risk_amount:.2f}")
            return risk_params
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return self._get_default_risk_params()
    
    def update_trailing_stop(self, position: Dict, current_price: float, indicators: Dict) -> float:
        """
        Update trailing stop loss based on current price and market conditions
        More volatile markets (higher ADX) get wider trailing stops
        """
        try:
            position_side = position['side']
            current_stop = position['stop_loss']
            entry_price = position['entry_price']
            
            # Get ATR for dynamic stop adjustment
            atr = indicators['atr']
            adx = indicators.get('adx', 25)
            
            # Adaptive trailing distance based on ADX
            # Higher ADX = stronger trend = wider trailing stop
            adx_multiplier = 1.0 + (adx - 25) / 100  # Adjusts based on trend strength
            trailing_distance = self.config['atr_stop_multiplier'] * atr * adx_multiplier
            
            if position_side == 'BUY':
                # For long positions, trail stop upward only
                new_stop = current_price - trailing_distance
                # Only update if new stop is higher than current stop
                if new_stop > current_stop:
                    self.logger.info(f"Trailing stop updated (LONG): {current_stop:.8f} -> {new_stop:.8f}")
                    return round(new_stop, 8)
                    
            elif position_side == 'SELL':
                # For short positions, trail stop downward only
                new_stop = current_price + trailing_distance
                # Only update if new stop is lower than current stop
                if new_stop < current_stop:
                    self.logger.info(f"Trailing stop updated (SHORT): {current_stop:.8f} -> {new_stop:.8f}")
                    return round(new_stop, 8)
            
            # Return current stop if no update needed
            return current_stop
            
        except Exception as e:
            self.logger.error(f"Error updating trailing stop: {e}")
            return position.get('stop_loss', 0)
    
    def calculate_risk_reward_ratio(self, entry_price: float, stop_loss: float, take_profit: float) -> float:
        """Calculate actual risk-reward ratio"""
        try:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            
            if risk == 0:
                return 0
                
            return reward / risk
            
        except Exception as e:
            self.logger.error(f"Error calculating R:R ratio: {e}")
            return 0
    
    def validate_risk_parameters(self, risk_params: Dict) -> bool:
        """Validate calculated risk parameters"""
        try:
            required_keys = ['quantity', 'risk_amount', 'stop_distance', 'target_distance']
            
            for key in required_keys:
                if key not in risk_params or risk_params[key] <= 0:
                    self.logger.error(f"Invalid risk parameter: {key}")
                    return False
            
            # Check risk-reward ratio
            rr_ratio = risk_params.get('risk_reward_ratio', 0)
            if rr_ratio < 1.5:  # Minimum 1.5:1 R:R
                self.logger.warning(f"Low risk-reward ratio: {rr_ratio:.2f}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating risk parameters: {e}")
            return False
    
    def get_max_position_size(self, account_balance: float, price: float) -> float:
        """Calculate maximum allowed position size (safety limit)"""
        try:
            # Maximum 5% of account balance in any single position
            max_position_value = account_balance * 0.05
            max_quantity = max_position_value / price
            
            return self._round_quantity(max_quantity)
            
        except Exception as e:
            self.logger.error(f"Error calculating max position size: {e}")
            return 0
    
    def _round_quantity(self, quantity: float) -> float:
        """Round quantity to appropriate precision based on symbol"""
        # For most crypto pairs, 6 decimal places is sufficient
        return round(quantity, 6)
    
    def _get_default_risk_params(self) -> Dict[str, Any]:
        """Return default risk parameters in case of error"""
        return {
            'quantity': 0,
            'risk_amount': 0,
            'stop_distance': 0,
            'target_distance': 0,
            'stop_loss_long': 0,
            'stop_loss_short': 0,
            'take_profit_long': 0,
            'take_profit_short': 0,
            'risk_reward_ratio': 0
        }
    
    def calculate_portfolio_risk(self, positions: list, account_balance: float) -> Dict[str, float]:
        """Calculate overall portfolio risk metrics"""
        try:
            total_risk = sum(pos.get('risk_amount', 0) for pos in positions)
            total_exposure = sum(pos.get('notional_value', 0) for pos in positions)
            
            risk_percentage = (total_risk / account_balance) * 100 if account_balance > 0 else 0
            exposure_percentage = (total_exposure / account_balance) * 100 if account_balance > 0 else 0
            
            return {
                'total_risk': total_risk,
                'total_exposure': total_exposure,
                'risk_percentage': risk_percentage,
                'exposure_percentage': exposure_percentage,
                'positions_count': len(positions)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio risk: {e}")
            return {}
