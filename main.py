#!/usr/bin/env python3
"""
Sophisticated Binance Trading Bot with Trend Following and Adaptive Risk Management
Main entry point for the trading bot
"""

import os
import time
import asyncio
import logging
import yaml
from datetime import datetime
from typing import Dict, Any

from indicators import TechnicalIndicators
from strategy import TrendFollowingStrategy
from risk_manager import AdaptiveRiskManager
from executor import BinanceExecutor
from logger_config import setup_logging
from telegram_notifier import TelegramNotifier
from utils import load_config, validate_config


class TradingBot:
    """Main trading bot class orchestrating all components"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the trading bot with configuration"""
        self.config = load_config(config_path)
        validate_config(self.config)
        
        # Setup logging
        setup_logging(self.config['logging'])
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.indicators = TechnicalIndicators(self.config['indicators'])
        self.strategy = TrendFollowingStrategy(self.config)
        self.risk_manager = AdaptiveRiskManager(self.config['risk_management'])
        self.executor = BinanceExecutor(self.config)
        
        # Optional Telegram notifications
        self.telegram = None
        if self.config['telegram']['enabled']:
            self.telegram = TelegramNotifier(self.config['telegram'])
        
        # Bot state
        self.is_running = False
        self.current_position = None
        self.last_check_time = None
        
        self.logger.info("Trading bot initialized successfully")
    
    async def start(self):
        """Start the trading bot main loop"""
        self.logger.info("Starting trading bot...")
        self.is_running = True
        
        if self.telegram:
            await self.telegram.send_message("🤖 Trading bot started")
        
        try:
            while self.is_running:
                await self.run_trading_cycle()
                await asyncio.sleep(self.config['execution']['check_interval'])
                
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
            if self.telegram:
                await self.telegram.send_message(f"❌ Bot error: {e}")
        finally:
            await self.shutdown()
    
    async def run_trading_cycle(self):
        """Execute one complete trading cycle"""
        try:
            # Get market data
            market_data = await self.executor.get_market_data()
            if not market_data:
                self.logger.warning("Failed to get market data")
                return
            
            # Calculate technical indicators
            indicators_data = self.indicators.calculate_all(market_data)
            
            # Check current position status
            current_position = await self.executor.get_current_position()
            
            if current_position:
                # Manage existing position
                self.current_position = current_position
                await self.manage_position(market_data, indicators_data)
            else:
                # Look for new entry opportunities
                self.current_position = None
                await self.evaluate_entry(market_data, indicators_data)
                
        except Exception as e:
            self.logger.error(f"Error in trading cycle: {e}")
    
    async def evaluate_entry(self, market_data: Dict, indicators_data: Dict):
        """Evaluate potential entry opportunities"""
        try:
            # Get current price
            current_price = market_data['close'][-1]
            
            # Check strategy signals
            signal = self.strategy.get_entry_signal(market_data, indicators_data)
            
            if signal['action'] == 'NONE':
                return
            
            # Get order book data for confirmation
            orderbook = await self.executor.get_orderbook()
            if not orderbook or not self.strategy.validate_orderbook_pressure(orderbook, signal['action']):
                self.logger.info(f"Order book pressure doesn't confirm {signal['action']} signal")
                return
            
            # Calculate position size and risk parameters
            account_balance = await self.executor.get_account_balance()
            risk_params = self.risk_manager.calculate_position_size(
                account_balance, current_price, indicators_data['atr']
            )
            
            # Execute trade
            trade_result = await self.executor.execute_trade(
                signal['action'], risk_params['quantity'], risk_params
            )
            
            if trade_result['success']:
                self.logger.info(f"Trade executed: {signal['action']} {risk_params['quantity']} at {current_price}")
                
                if self.telegram:
                    message = (f"📈 Trade Executed\n"
                             f"Action: {signal['action']}\n"
                             f"Price: {current_price}\n"
                             f"Quantity: {risk_params['quantity']}\n"
                             f"Stop Loss: {risk_params['stop_loss']}\n"
                             f"Take Profit: {risk_params['take_profit']}")
                    await self.telegram.send_message(message)
            else:
                self.logger.error(f"Trade execution failed: {trade_result['error']}")
                
        except Exception as e:
            self.logger.error(f"Error evaluating entry: {e}")
    
    async def manage_position(self, market_data: Dict, indicators_data: Dict):
        """Manage existing position with trailing stops and exit conditions"""
        try:
            current_price = market_data['close'][-1]
            
            # Update trailing stop if enabled
            if self.config['risk_management']['trailing_stop_enabled'] and self.current_position:
                new_stop = self.risk_manager.update_trailing_stop(
                    self.current_position, current_price, indicators_data
                )
                
                if new_stop != self.current_position['stop_loss']:
                    await self.executor.update_stop_loss(new_stop)
                    self.logger.info(f"Updated trailing stop to {new_stop}")
            
            # Check exit conditions
            if self.current_position:
                exit_signal = self.strategy.get_exit_signal(
                    market_data, indicators_data, self.current_position
                )
            else:
                return
            
            if exit_signal['should_exit']:
                result = await self.executor.close_position(exit_signal['reason'])
                
                if result['success']:
                    pnl = result['pnl']
                    self.logger.info(f"Position closed: {exit_signal['reason']}, PnL: {pnl}")
                    
                    if self.telegram:
                        message = (f"🎯 Position Closed\n"
                                 f"Reason: {exit_signal['reason']}\n"
                                 f"PnL: {pnl}\n"
                                 f"Exit Price: {current_price}")
                        await self.telegram.send_message(message)
                        
        except Exception as e:
            self.logger.error(f"Error managing position: {e}")
    
    async def shutdown(self):
        """Gracefully shutdown the bot"""
        self.logger.info("Shutting down trading bot...")
        self.is_running = False
        
        # Close any open positions if needed
        if self.current_position:
            await self.executor.close_position("Bot shutdown")
        
        if self.telegram:
            await self.telegram.send_message("🛑 Trading bot stopped")
        
        self.logger.info("Trading bot shutdown complete")


async def main():
    """Main entry point"""
    try:
        bot = TradingBot()
        await bot.start()
    except Exception as e:
        logging.error(f"Failed to start trading bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())
