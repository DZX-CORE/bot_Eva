"""
Utility Functions Module
Common utility functions used across the trading bot
"""

import os
import yaml
import json
import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import hashlib


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Override with environment variables if available
        config = _override_with_env_vars(config)
        
        logging.info(f"Configuration loaded from {config_path}")
        return config
        
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML configuration: {e}")
        raise
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        raise


def _override_with_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """Override configuration with environment variables"""
    
    # API credentials
    if os.getenv('BINANCE_API_KEY'):
        config['api']['binance_api_key'] = os.getenv('BINANCE_API_KEY')
    
    if os.getenv('BINANCE_SECRET_KEY'):
        config['api']['binance_secret_key'] = os.getenv('BINANCE_SECRET_KEY')
    
    # Telegram credentials
    if os.getenv('TELEGRAM_BOT_TOKEN'):
        config['telegram']['bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if os.getenv('TELEGRAM_CHAT_ID'):
        config['telegram']['chat_id'] = os.getenv('TELEGRAM_CHAT_ID')
    
    # Trading symbol
    if os.getenv('TRADING_SYMBOL'):
        config['trading']['symbol'] = os.getenv('TRADING_SYMBOL')
    
    # Risk percentage
    if os.getenv('RISK_PER_TRADE'):
        try:
            risk_value = os.getenv('RISK_PER_TRADE')
            if risk_value:
                config['trading']['risk_per_trade'] = float(risk_value)
        except ValueError:
            logging.warning("Invalid RISK_PER_TRADE environment variable")
    
    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration parameters"""
    required_sections = ['api', 'trading', 'indicators', 'risk_management', 'execution']
    
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")
    
    # Validate trading parameters
    trading_config = config['trading']
    if trading_config['risk_per_trade'] <= 0 or trading_config['risk_per_trade'] > 0.1:
        raise ValueError("risk_per_trade must be between 0 and 0.1 (10%)")
    
    if trading_config['risk_reward_ratio'] < 1:
        raise ValueError("risk_reward_ratio must be >= 1")
    
    # Validate indicator parameters
    indicators_config = config['indicators']
    required_indicators = ['ema_period', 'macd_fast', 'macd_slow', 'rsi_period', 'atr_period']
    
    for indicator in required_indicators:
        if indicator not in indicators_config or indicators_config[indicator] <= 0:
            raise ValueError(f"Invalid indicator parameter: {indicator}")
    
    logging.info("Configuration validation passed")
    return True


def calculate_portfolio_metrics(trades: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate portfolio performance metrics"""
    if not trades:
        return {}
    
    # Calculate basic metrics
    total_trades = len(trades)
    winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
    losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
    
    win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
    
    total_pnl = sum(t.get('pnl', 0) for t in trades)
    average_win = sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades) if winning_trades else 0
    average_loss = sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0
    
    # Risk metrics
    profit_factor = abs(sum(t.get('pnl', 0) for t in winning_trades) / sum(t.get('pnl', 0) for t in losing_trades)) if losing_trades else float('inf')
    
    # Drawdown calculation
    running_pnl = 0
    peak = 0
    max_drawdown = 0
    
    for trade in trades:
        running_pnl += trade.get('pnl', 0)
        if running_pnl > peak:
            peak = running_pnl
        drawdown = peak - running_pnl
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    return {
        'total_trades': total_trades,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'average_win': average_win,
        'average_loss': average_loss,
        'profit_factor': profit_factor,
        'max_drawdown': max_drawdown,
        'best_trade': max((t.get('pnl', 0) for t in trades), default=0),
        'worst_trade': min((t.get('pnl', 0) for t in trades), default=0)
    }


def format_currency(amount: float, decimals: int = 2) -> str:
    """Format currency amount with proper decimals"""
    return f"${amount:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage with proper decimals"""
    return f"{value:.{decimals}f}%"


def calculate_time_difference(start_time: datetime, end_time: datetime | None = None) -> str:
    """Calculate human-readable time difference"""
    if end_time is None:
        end_time = datetime.now()
    
    diff = end_time - start_time
    
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m {seconds}s"


def generate_trade_id() -> str:
    """Generate unique trade ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
    return f"TRADE_{timestamp}_{random_hash}"


def save_trade_history(trade_data: Dict[str, Any], file_path: str = "data/trade_history.json"):
    """Save trade to history file"""
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Load existing data
        try:
            with open(file_path, 'r') as file:
                trades = json.load(file)
        except FileNotFoundError:
            trades = []
        
        # Add new trade
        trades.append(trade_data)
        
        # Save updated data
        with open(file_path, 'w') as file:
            json.dump(trades, file, indent=2, default=str)
        
        logging.info(f"Trade saved to history: {trade_data.get('trade_id', 'Unknown')}")
        
    except Exception as e:
        logging.error(f"Error saving trade history: {e}")


def load_trade_history(file_path: str = "data/trade_history.json") -> List[Dict[str, Any]]:
    """Load trade history from file"""
    try:
        with open(file_path, 'r') as file:
            trades = json.load(file)
        return trades
    except FileNotFoundError:
        logging.info("No trade history file found")
        return []
    except Exception as e:
        logging.error(f"Error loading trade history: {e}")
        return []


def clean_old_logs(log_directory: str = "logs", days_to_keep: int = 30):
    """Clean up old log files"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for filename in os.listdir(log_directory):
            file_path = os.path.join(log_directory, filename)
            
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                
                if file_time < cutoff_date:
                    os.remove(file_path)
                    logging.info(f"Deleted old log file: {filename}")
    
    except Exception as e:
        logging.error(f"Error cleaning old logs: {e}")


def create_backup(source_file: str, backup_directory: str = "backups"):
    """Create backup of important files"""
    try:
        os.makedirs(backup_directory, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(source_file)
        backup_filename = f"{filename}.{timestamp}.backup"
        backup_path = os.path.join(backup_directory, backup_filename)
        
        with open(source_file, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        
        logging.info(f"Backup created: {backup_path}")
        
    except Exception as e:
        logging.error(f"Error creating backup: {e}")


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = datetime.now()
        
        # Remove old calls outside time window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < timedelta(seconds=self.time_window)]
        
        # Check if we need to wait
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0]).seconds
            if sleep_time > 0:
                logging.info(f"Rate limit reached, waiting {sleep_time} seconds")
                await asyncio.sleep(sleep_time)
        
        # Record this call
        self.calls.append(now)
