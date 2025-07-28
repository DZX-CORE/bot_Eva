"""
Trade Execution Module
Handles all interactions with Binance API for trade execution and position management
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException
import time


class BinanceExecutor:
    """Handles trade execution and position management on Binance"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Binance client with API credentials"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Get API credentials from environment variables
        api_key = os.getenv('BINANCE_API_KEY', '')
        secret_key = os.getenv('BINANCE_SECRET_KEY', '')
        
        if not api_key or not secret_key:
            raise ValueError("Binance API credentials not found in environment variables")
        
        # Initialize Binance client
        try:
            self.client = Client(
                api_key=api_key,
                api_secret=secret_key,
                testnet=config['api'].get('testnet', False)
            )
            
            # Test connection
            self.client.ping()
            self.logger.info("Successfully connected to Binance API")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Binance API: {e}")
            raise
        
        self.symbol = config['trading']['symbol']
        self.rate_limit_delay = config['api']['rate_limit_delay']
        
        # Current position tracking
        self.current_position = None
        self.open_orders = []
    
    async def get_market_data(self, limit: int = 500) -> Optional[Dict]:
        """Get historical market data for analysis"""
        try:
            # Add rate limiting
            await asyncio.sleep(self.rate_limit_delay)
            
            # Get kline data (candlesticks)
            klines = self.client.get_historical_klines(
                self.symbol, 
                Client.KLINE_INTERVAL_5MINUTE,  # 5-minute candles
                limit=limit
            )
            
            if not klines:
                self.logger.error("No market data received")
                return None
            
            # Convert to structured format
            market_data = {
                'timestamp': [int(k[0]) for k in klines],
                'open': [float(k[1]) for k in klines],
                'high': [float(k[2]) for k in klines],
                'low': [float(k[3]) for k in klines],
                'close': [float(k[4]) for k in klines],
                'volume': [float(k[5]) for k in klines]
            }
            
            return market_data
            
        except BinanceAPIException as e:
            self.logger.error(f"Binance API error getting market data: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            return None
    
    async def get_orderbook(self, limit: int = 10) -> Optional[Dict]:
        """Get current order book"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            orderbook = self.client.get_order_book(symbol=self.symbol, limit=limit)
            
            return {
                'bids': orderbook['bids'],
                'asks': orderbook['asks']
            }
            
        except BinanceAPIException as e:
            self.logger.error(f"Binance API error getting orderbook: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting orderbook: {e}")
            return None
    
    async def get_account_balance(self) -> float:
        """Get current account balance in USDT"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            account = self.client.get_account()
            
            # Find USDT balance
            for balance in account['balances']:
                if balance['asset'] == 'USDT':
                    return float(balance['free'])
            
            return 0.0
            
        except BinanceAPIException as e:
            self.logger.error(f"Binance API error getting balance: {e}")
            return 0.0
        except Exception as e:
            self.logger.error(f"Error getting balance: {e}")
            return 0.0
    
    async def execute_trade(self, action: str, quantity: float, risk_params: Dict) -> Dict[str, Any]:
        """Execute a market order"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            # Determine order side
            side = Client.SIDE_BUY if action == 'BUY' else Client.SIDE_SELL
            
            # Place market order
            order = self.client.order_market(
                symbol=self.symbol,
                side=side,
                quantity=quantity
            )
            
            if order['status'] == 'FILLED':
                # Calculate actual fill price
                fill_price = float(order['fills'][0]['price']) if order['fills'] else 0
                
                # Set stop loss and take profit based on action
                if action == 'BUY':
                    stop_loss = risk_params['stop_loss_long']
                    take_profit = risk_params['take_profit_long']
                else:
                    stop_loss = risk_params['stop_loss_short']
                    take_profit = risk_params['take_profit_short']
                
                # Place stop loss order
                await self._place_stop_loss_order(action, quantity, stop_loss)
                
                # Place take profit order
                await self._place_take_profit_order(action, quantity, take_profit)
                
                # Update position tracking
                self.current_position = {
                    'side': action,
                    'quantity': quantity,
                    'entry_price': fill_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'order_id': order['orderId'],
                    'timestamp': order['transactTime']
                }
                
                self.logger.info(f"Trade executed successfully: {action} {quantity} at {fill_price}")
                
                return {
                    'success': True,
                    'order_id': order['orderId'],
                    'fill_price': fill_price,
                    'quantity': quantity
                }
            else:
                self.logger.error(f"Order not filled: {order['status']}")
                return {'success': False, 'error': f"Order status: {order['status']}"}
                
        except BinanceAPIException as e:
            self.logger.error(f"Binance API error executing trade: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _place_stop_loss_order(self, position_side: str, quantity: float, stop_price: float):
        """Place stop loss order"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            # Determine order side (opposite of position)
            order_side = Client.SIDE_SELL if position_side == 'BUY' else Client.SIDE_BUY
            
            # Place stop loss order
            stop_order = self.client.create_order(
                symbol=self.symbol,
                side=order_side,
                type="STOP_MARKET",
                quantity=quantity,
                stopPrice=stop_price
            )
            
            self.logger.info(f"Stop loss placed at {stop_price}")
            return stop_order
            
        except Exception as e:
            self.logger.error(f"Error placing stop loss: {e}")
            return None
    
    async def _place_take_profit_order(self, position_side: str, quantity: float, target_price: float):
        """Place take profit order"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            # Determine order side (opposite of position)
            order_side = Client.SIDE_SELL if position_side == 'BUY' else Client.SIDE_BUY
            
            # Place limit order at target price
            tp_order = self.client.create_order(
                symbol=self.symbol,
                side=order_side,
                type=Client.ORDER_TYPE_LIMIT,
                quantity=quantity,
                price=target_price,
                timeInForce=Client.TIME_IN_FORCE_GTC
            )
            
            self.logger.info(f"Take profit placed at {target_price}")
            return tp_order
            
        except Exception as e:
            self.logger.error(f"Error placing take profit: {e}")
            return None
    
    async def get_current_position(self) -> Optional[Dict]:
        """Get current position information"""
        try:
            # For spot trading, check current balance and open orders
            await asyncio.sleep(self.rate_limit_delay)
            
            # Check if we have any open orders that indicate a position
            open_orders = self.client.get_open_orders(symbol=self.symbol)
            
            if open_orders and self.current_position:
                return self.current_position
            else:
                self.current_position = None
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting current position: {e}")
            return None
    
    async def update_stop_loss(self, new_stop_price: float) -> bool:
        """Update stop loss order"""
        try:
            if not self.current_position:
                return False
            
            await asyncio.sleep(self.rate_limit_delay)
            
            # Cancel existing stop loss orders
            open_orders = self.client.get_open_orders(symbol=self.symbol)
            for order in open_orders:
                if order['type'] == 'STOP_MARKET':
                    self.client.cancel_order(symbol=self.symbol, orderId=order['orderId'])
            
            # Place new stop loss
            await self._place_stop_loss_order(
                self.current_position['side'],
                self.current_position['quantity'],
                new_stop_price
            )
            
            # Update position
            self.current_position['stop_loss'] = new_stop_price
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating stop loss: {e}")
            return False
    
    async def close_position(self, reason: str) -> Dict[str, Any]:
        """Close current position"""
        try:
            if not self.current_position:
                return {'success': False, 'error': 'No position to close'}
            
            await asyncio.sleep(self.rate_limit_delay)
            
            # Cancel all open orders for this symbol
            open_orders = self.client.get_open_orders(symbol=self.symbol)
            for order in open_orders:
                self.client.cancel_order(symbol=self.symbol, orderId=order['orderId'])
            
            # Place market order to close position
            close_side = Client.SIDE_SELL if self.current_position['side'] == 'BUY' else Client.SIDE_BUY
            
            close_order = self.client.order_market(
                symbol=self.symbol,
                side=close_side,
                quantity=self.current_position['quantity']
            )
            
            if close_order['status'] == 'FILLED':
                exit_price = float(close_order['fills'][0]['price']) if close_order['fills'] else 0
                
                # Calculate PnL
                entry_price = self.current_position['entry_price']
                if self.current_position['side'] == 'BUY':
                    pnl = (exit_price - entry_price) * self.current_position['quantity']
                else:
                    pnl = (entry_price - exit_price) * self.current_position['quantity']
                
                self.logger.info(f"Position closed: {reason}, PnL: {pnl:.2f}")
                
                # Clear position
                self.current_position = None
                
                return {
                    'success': True,
                    'exit_price': exit_price,
                    'pnl': round(pnl, 2),
                    'reason': reason
                }
            else:
                return {'success': False, 'error': f"Close order status: {close_order['status']}"}
                
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return {'success': False, 'error': str(e)}
