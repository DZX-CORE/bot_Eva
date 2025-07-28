"""
Logging Configuration Module
Sets up comprehensive logging for the trading bot
"""

import logging
import logging.handlers
import os
from typing import Dict, Any


def setup_logging(config: Dict[str, Any]):
    """Setup logging configuration for the trading bot"""
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Get configuration
    log_level = config.get('level', 'INFO')
    log_file = os.path.join(log_dir, config.get('file', 'trading_bot.log'))
    max_file_size = config.get('max_file_size', 10485760)  # 10MB
    backup_count = config.get('backup_count', 5)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_file_size,
        backupCount=backup_count
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Create separate loggers for different components
    setup_component_loggers(formatter)
    
    logging.info("Logging system initialized")


def setup_component_loggers(formatter):
    """Setup specialized loggers for different components"""
    
    # Trading decisions logger
    trading_logger = logging.getLogger('trading_decisions')
    trading_handler = logging.FileHandler('logs/trading_decisions.log')
    trading_handler.setFormatter(formatter)
    trading_logger.addHandler(trading_handler)
    trading_logger.setLevel(logging.INFO)
    
    # API communication logger
    api_logger = logging.getLogger('api_communication')
    api_handler = logging.FileHandler('logs/api_communication.log')
    api_handler.setFormatter(formatter)
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.DEBUG)
    
    # Risk management logger
    risk_logger = logging.getLogger('risk_management')
    risk_handler = logging.FileHandler('logs/risk_management.log')
    risk_handler.setFormatter(formatter)
    risk_logger.addHandler(risk_handler)
    risk_logger.setLevel(logging.INFO)
    
    # Performance logger
    performance_logger = logging.getLogger('performance')
    performance_handler = logging.FileHandler('logs/performance.log')
    performance_formatter = logging.Formatter(
        '%(asctime)s,%(message)s',  # CSV format for analysis
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    performance_handler.setFormatter(performance_formatter)
    performance_logger.addHandler(performance_handler)
    performance_logger.setLevel(logging.INFO)


class TradingLogger:
    """Specialized logger for trading operations"""
    
    def __init__(self):
        self.trading_logger = logging.getLogger('trading_decisions')
        self.api_logger = logging.getLogger('api_communication')
        self.risk_logger = logging.getLogger('risk_management')
        self.performance_logger = logging.getLogger('performance')
    
    def log_signal(self, signal_type: str, action: str, price: float, confidence: float, reasons: list):
        """Log trading signal details"""
        message = f"SIGNAL: {signal_type} | Action: {action} | Price: {price} | Confidence: {confidence:.2f} | Reasons: {', '.join(reasons)}"
        self.trading_logger.info(message)
    
    def log_trade_execution(self, action: str, quantity: float, price: float, order_id: str):
        """Log trade execution details"""
        message = f"TRADE: {action} | Quantity: {quantity} | Price: {price} | OrderID: {order_id}"
        self.trading_logger.info(message)
    
    def log_position_update(self, position_type: str, details: dict):
        """Log position updates"""
        message = f"POSITION: {position_type} | Details: {details}"
        self.trading_logger.info(message)
    
    def log_risk_calculation(self, risk_type: str, calculations: dict):
        """Log risk management calculations"""
        message = f"RISK: {risk_type} | Calculations: {calculations}"
        self.risk_logger.info(message)
    
    def log_api_call(self, endpoint: str, params: dict, response_status: str):
        """Log API call details"""
        message = f"API: {endpoint} | Params: {params} | Status: {response_status}"
        self.api_logger.debug(message)
    
    def log_performance(self, trade_id: str, entry_price: float, exit_price: float, 
                       pnl: float, duration: int, reason: str):
        """Log performance data in CSV format"""
        message = f"{trade_id},{entry_price},{exit_price},{pnl},{duration},{reason}"
        self.performance_logger.info(message)
    
    def log_error(self, component: str, error_message: str, error_details: str = ""):
        """Log error details"""
        message = f"ERROR: {component} | Message: {error_message}"
        if error_details:
            message += f" | Details: {error_details}"
        logging.error(message)
