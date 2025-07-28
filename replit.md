# Binance Trading Bot

## Overview

Este é um bot de trading sofisticado para Binance que implementa uma estratégia de trend following com gestão de risco adaptativa. O bot executa trades automaticamente baseado em indicadores técnicos e gerencia posições com stop-losses e take-profits dinâmicos. Inclui logging abrangente, notificações via Telegram e tratamento robusto de erros.

**Status Atual:** Bot completamente funcional e testado com modo demo. Pronto para operação real com chaves de API válidas.

## User Preferences

Preferred communication style: Simple, everyday language (português).

## System Architecture

The bot follows a modular architecture with clear separation of concerns:

- **Main Controller** (`main.py`): Orchestrates all components and manages the main trading loop
- **Strategy Engine** (`strategy.py`): Implements trend-following logic with multiple confirmation signals
- **Technical Analysis** (`indicators.py`): Calculates various technical indicators (EMA, MACD, RSI, ATR, etc.)
- **Risk Management** (`risk_manager.py`): Handles position sizing, stop-losses, and risk calculations based on volatility
- **Trade Execution** (`executor.py`): Manages all interactions with Binance API for order placement and position management
- **Notification System** (`telegram_notifier.py`): Sends trade alerts and notifications via Telegram
- **Utilities** (`utils.py`): Common functions for configuration loading and data processing
- **Logging** (`logger_config.py`): Comprehensive logging setup with file rotation

## Key Components

### Trading Strategy
- **Type**: Trend-following with multiple confirmation signals
- **Indicators**: EMA-200, MACD, RSI, ADX, ATR, Volume analysis
- **Entry Logic**: Requires alignment of price trend, momentum, and volume confirmation
- **Risk-Reward**: Configurable ratios using ATR-based stop-losses and targets

### Risk Management
- **Position Sizing**: Fixed 1% risk per trade based on account balance
- **Stop Losses**: Dynamic using ATR (Average True Range) multipliers
- **Take Profits**: Risk-reward ratios of typically 1:2 or 1:3
- **Volatility Adaptation**: Position sizes adjust automatically based on market volatility (ATR)

### API Integration
- **Exchange**: Binance (supports both live and testnet environments)
- **Authentication**: API key and secret stored in environment variables
- **Rate Limiting**: Built-in delays to respect API limits
- **Error Handling**: Comprehensive exception handling for API failures

### Notification System
- **Platform**: Telegram bot integration
- **Events**: Trade executions, position updates, errors, and system status
- **Format**: HTML-formatted messages with timestamps
- **Configuration**: Optional - can be disabled if not needed

## Data Flow

1. **Market Data Collection**: Bot fetches real-time price and volume data from Binance
2. **Technical Analysis**: Indicators module calculates all required technical signals
3. **Signal Generation**: Strategy module analyzes indicators and generates entry/exit signals
4. **Risk Assessment**: Risk manager calculates position sizes and stop-loss levels
5. **Order Execution**: Executor module places orders through Binance API
6. **Position Monitoring**: Continuous monitoring of open positions and market conditions
7. **Notifications**: Important events are sent via Telegram (if enabled)

## External Dependencies

### APIs and Services
- **Binance API**: Core trading functionality, market data, and account management
- **Telegram Bot API**: Notification delivery system

### Python Libraries
- **binance-python**: Official Binance API wrapper
- **pandas/numpy**: Data manipulation and numerical calculations
- **ta (Technical Analysis)**: Technical indicator calculations
- **PyYAML**: Configuration file parsing
- **requests**: HTTP requests for Telegram notifications

### Environment Variables Required
- `BINANCE_API_KEY`: Binance API key for authentication
- `BINANCE_SECRET_KEY`: Binance API secret for authentication
- `TELEGRAM_BOT_TOKEN`: Telegram bot token (optional)
- `TELEGRAM_CHAT_ID`: Telegram chat ID for notifications (optional)

## Deployment Strategy

### Configuration Management
- **Primary Config**: YAML-based configuration file (`config.yaml`)
- **Environment Override**: Sensitive credentials stored in environment variables
- **Validation**: Configuration validation on startup to prevent runtime errors

### Logging Strategy
- **File Logging**: Rotating log files with configurable size limits
- **Console Output**: Real-time status updates and errors
- **Log Levels**: Configurable logging levels (INFO, DEBUG, WARNING, ERROR)
- **Structured Format**: Timestamped logs with module identification

### Error Handling
- **API Failures**: Automatic retry logic with exponential backoff
- **Network Issues**: Connection monitoring and reconnection attempts
- **Invalid Signals**: Graceful handling of edge cases in technical analysis
- **Position Management**: Fail-safes for position tracking and order management

### Testing Framework
- **Unit Tests**: Comprehensive test coverage for all major components
- **Mock Integration**: Isolated testing without live API calls
- **Test Data**: Reproducible test scenarios with controlled market data

### Operational Considerations
- **Testnet Support**: Can run on Binance testnet for safe testing
- **Rate Limiting**: Built-in respect for API rate limits
- **Position Tracking**: Persistent position state management
- **Graceful Shutdown**: Clean exit procedures for position safety