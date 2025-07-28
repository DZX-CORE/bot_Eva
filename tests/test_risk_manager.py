"""
Unit tests for risk management
"""

import unittest
from risk_manager import AdaptiveRiskManager


class TestAdaptiveRiskManager(unittest.TestCase):
    """Test cases for adaptive risk manager"""
    
    def setUp(self):
        """Set up test data"""
        self.config = {
            'atr_stop_multiplier': 1.5,
            'atr_target_multiplier': 3.0
        }
        
        self.risk_manager = AdaptiveRiskManager(self.config)
    
    def test_calculate_position_size(self):
        """Test position size calculation"""
        account_balance = 10000
        price = 50000
        atr = 500
        
        risk_params = self.risk_manager.calculate_position_size(
            account_balance, price, atr
        )
        
        # Check required fields
        required_fields = [
            'quantity', 'risk_amount', 'stop_distance', 'target_distance',
            'stop_loss_long', 'stop_loss_short', 'take_profit_long', 
            'take_profit_short', 'risk_reward_ratio'
        ]
        
        for field in required_fields:
            self.assertIn(field, risk_params)
        
        # Check risk amount is 1% of balance
        self.assertEqual(risk_params['risk_amount'], 100)
        
        # Check stop distance
        expected_stop_distance = 1.5 * atr
        self.assertEqual(risk_params['stop_distance'], expected_stop_distance)
        
        # Check target distance
        expected_target_distance = 3.0 * atr
        self.assertEqual(risk_params['target_distance'], expected_target_distance)
        
        # Check risk-reward ratio
        expected_rr = expected_target_distance / expected_stop_distance
        self.assertEqual(risk_params['risk_reward_ratio'], expected_rr)
        
        # Position size should be positive
        self.assertGreater(risk_params['quantity'], 0)
    
    def test_trailing_stop_long_position(self):
        """Test trailing stop for long position"""
        position = {
            'side': 'BUY',
            'entry_price': 50000,
            'stop_loss': 49000
        }
        
        current_price = 52000
        indicators = {'atr': 500, 'adx': 30}
        
        new_stop = self.risk_manager.update_trailing_stop(
            position, current_price, indicators
        )
        
        # New stop should be higher than current stop for long position
        self.assertGreater(new_stop, position['stop_loss'])
    
    def test_trailing_stop_short_position(self):
        """Test trailing stop for short position"""
        position = {
            'side': 'SELL',
            'entry_price': 50000,
            'stop_loss': 51000
        }
        
        current_price = 48000
        indicators = {'atr': 500, 'adx': 30}
        
        new_stop = self.risk_manager.update_trailing_stop(
            position, current_price, indicators
        )
        
        # New stop should be lower than current stop for short position
        self.assertLess(new_stop, position['stop_loss'])
    
    def test_trailing_stop_no_update(self):
        """Test trailing stop when no update is needed"""
        position = {
            'side': 'BUY',
            'entry_price': 50000,
            'stop_loss': 49000
        }
        
        # Price hasn't moved favorably enough
        current_price = 50200
        indicators = {'atr': 500, 'adx': 30}
        
        new_stop = self.risk_manager.update_trailing_stop(
            position, current_price, indicators
        )
        
        # Stop should remain the same
        self.assertEqual(new_stop, position['stop_loss'])
    
    def test_risk_reward_ratio_calculation(self):
        """Test risk-reward ratio calculation"""
        entry_price = 50000
        stop_loss = 49000
        take_profit = 52000
        
        rr_ratio = self.risk_manager.calculate_risk_reward_ratio(
            entry_price, stop_loss, take_profit
        )
        
        expected_risk = abs(entry_price - stop_loss)  # 1000
        expected_reward = abs(take_profit - entry_price)  # 2000
        expected_rr = expected_reward / expected_risk  # 2.0
        
        self.assertEqual(rr_ratio, expected_rr)
    
    def test_validate_risk_parameters_valid(self):
        """Test validation of valid risk parameters"""
        valid_params = {
            'quantity': 0.1,
            'risk_amount': 100,
            'stop_distance': 500,
            'target_distance': 1000,
            'risk_reward_ratio': 2.0
        }
        
        result = self.risk_manager.validate_risk_parameters(valid_params)
        self.assertTrue(result)
    
    def test_validate_risk_parameters_invalid(self):
        """Test validation of invalid risk parameters"""
        # Missing required field
        invalid_params = {
            'quantity': 0.1,
            'risk_amount': 100,
            'stop_distance': 500
            # Missing target_distance and risk_reward_ratio
        }
        
        result = self.risk_manager.validate_risk_parameters(invalid_params)
        self.assertFalse(result)
        
        # Low risk-reward ratio
        low_rr_params = {
            'quantity': 0.1,
            'risk_amount': 100,
            'stop_distance': 500,
            'target_distance': 600,
            'risk_reward_ratio': 1.2  # Below minimum
        }
        
        result = self.risk_manager.validate_risk_parameters(low_rr_params)
        self.assertFalse(result)
    
    def test_max_position_size(self):
        """Test maximum position size calculation"""
        account_balance = 10000
        price = 50000
        
        max_size = self.risk_manager.get_max_position_size(account_balance, price)
        
        # Should be 5% of account balance divided by price
        expected_max = (account_balance * 0.05) / price
        self.assertEqual(max_size, round(expected_max, 6))
    
    def test_portfolio_risk_calculation(self):
        """Test portfolio risk metrics calculation"""
        positions = [
            {'risk_amount': 100, 'notional_value': 5000},
            {'risk_amount': 150, 'notional_value': 7500}
        ]
        account_balance = 10000
        
        portfolio_risk = self.risk_manager.calculate_portfolio_risk(
            positions, account_balance
        )
        
        # Check calculated values
        self.assertEqual(portfolio_risk['total_risk'], 250)
        self.assertEqual(portfolio_risk['total_exposure'], 12500)
        self.assertEqual(portfolio_risk['risk_percentage'], 2.5)
        self.assertEqual(portfolio_risk['exposure_percentage'], 125)
        self.assertEqual(portfolio_risk['positions_count'], 2)
    
    def test_minimum_position_size_adjustment(self):
        """Test position size adjustment for minimum notional"""
        account_balance = 100  # Small balance
        price = 50000
        atr = 10  # Small ATR
        
        risk_params = self.risk_manager.calculate_position_size(
            account_balance, price, atr
        )
        
        # Should adjust to meet minimum notional requirement
        min_notional = 10.0
        actual_notional = risk_params['quantity'] * price
        self.assertGreaterEqual(actual_notional, min_notional)


if __name__ == '__main__':
    unittest.main()
