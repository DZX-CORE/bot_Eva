"""
Telegram Notification Module
Handles sending notifications via Telegram bot
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
import requests
from datetime import datetime


class TelegramNotifier:
    """Handles Telegram notifications for trading bot events"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Telegram notifier"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Get Telegram credentials from environment
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', config.get('bot_token', ''))
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', config.get('chat_id', ''))
        
        if not self.bot_token or not self.chat_id:
            self.logger.warning("Telegram credentials not found. Notifications disabled.")
            self.enabled = False
        else:
            self.enabled = True
            self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
            self.logger.info("Telegram notifications enabled")
    
    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send a message to Telegram"""
        if not self.enabled:
            return False
        
        try:
            # Format message with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"[{timestamp}]\n{message}"
            
            # Prepare request
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': formatted_message,
                'parse_mode': parse_mode
            }
            
            # Send message
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.debug("Telegram message sent successfully")
                return True
            else:
                self.logger.error(f"Failed to send Telegram message: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False
    
    async def send_trade_alert(self, action: str, symbol: str, price: float, 
                              quantity: float, stop_loss: float, take_profit: float) -> bool:
        """Send trade execution alert"""
        emoji = "🟢" if action == "BUY" else "🔴"
        
        message = f"""
{emoji} <b>TRADE EXECUTED</b>

<b>Action:</b> {action}
<b>Symbol:</b> {symbol}
<b>Price:</b> ${price:,.4f}
<b>Quantity:</b> {quantity}
<b>Stop Loss:</b> ${stop_loss:,.4f}
<b>Take Profit:</b> ${take_profit:,.4f}

<i>Risk-Reward Ratio: 1:2</i>
        """
        
        return await self.send_message(message)
    
    async def send_position_closed_alert(self, symbol: str, pnl: float, 
                                        exit_price: float, reason: str) -> bool:
        """Send position closed alert"""
        emoji = "✅" if pnl > 0 else "❌"
        pnl_text = f"+${pnl:,.2f}" if pnl > 0 else f"-${abs(pnl):,.2f}"
        
        message = f"""
{emoji} <b>POSITION CLOSED</b>

<b>Symbol:</b> {symbol}
<b>Exit Price:</b> ${exit_price:,.4f}
<b>PnL:</b> {pnl_text}
<b>Reason:</b> {reason}

<i>Position management complete</i>
        """
        
        return await self.send_message(message)
    
    async def send_risk_alert(self, alert_type: str, message_text: str) -> bool:
        """Send risk management alert"""
        message = f"""
⚠️ <b>RISK ALERT: {alert_type}</b>

{message_text}

<i>Immediate attention required</i>
        """
        
        return await self.send_message(message)
    
    async def send_error_alert(self, error_type: str, error_message: str) -> bool:
        """Send error alert"""
        message = f"""
🚨 <b>ERROR ALERT</b>

<b>Type:</b> {error_type}
<b>Message:</b> {error_message}

<i>Bot may require intervention</i>
        """
        
        return await self.send_message(message)
    
    async def send_daily_summary(self, summary_data: Dict[str, Any]) -> bool:
        """Send daily performance summary"""
        message = f"""
📊 <b>DAILY SUMMARY</b>

<b>Trades Executed:</b> {summary_data.get('trades_count', 0)}
<b>Win Rate:</b> {summary_data.get('win_rate', 0):.1f}%
<b>Total PnL:</b> ${summary_data.get('total_pnl', 0):,.2f}
<b>Best Trade:</b> ${summary_data.get('best_trade', 0):,.2f}
<b>Worst Trade:</b> ${summary_data.get('worst_trade', 0):,.2f}

<b>Account Balance:</b> ${summary_data.get('account_balance', 0):,.2f}
<b>Drawdown:</b> {summary_data.get('drawdown', 0):.2f}%

<i>End of day report</i>
        """
        
        return await self.send_message(message)
    
    async def send_system_status(self, status: str, uptime: str, last_trade: str = "N/A") -> bool:
        """Send system status update"""
        status_emoji = "🟢" if status == "ACTIVE" else "🟡" if status == "IDLE" else "🔴"
        
        message = f"""
{status_emoji} <b>SYSTEM STATUS</b>

<b>Status:</b> {status}
<b>Uptime:</b> {uptime}
<b>Last Trade:</b> {last_trade}

<i>System monitoring update</i>
        """
        
        return await self.send_message(message)
    
    async def test_connection(self) -> bool:
        """Test Telegram connection"""
        if not self.enabled:
            return False
        
        test_message = "🤖 Trading Bot - Connection Test"
        result = await self.send_message(test_message)
        
        if result:
            self.logger.info("Telegram connection test successful")
        else:
            self.logger.error("Telegram connection test failed")
        
        return result
