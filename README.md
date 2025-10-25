# Binance Futures Trading Bot

A comprehensive CLI-based trading bot for Binance USDT-M Futures that supports multiple order types with robust logging, validation, and documentation.

## Assignment Submission

**Student**: Yash Bhong  
**Project**: Binance Future Order Bot  
**Date**: October 2025

## Features

### Core Orders (Mandatory)

- ✅ **Market Orders**: Immediate execution at current market price
- ✅ **Limit Orders**: Execute at specified price or better
- ✅ **Stop-Limit Orders**: Trigger limit orders when stop price is hit
- ✅ **OCO Orders**: One-Cancels-Other orders for take-profit and stop-loss

### Advanced Orders (Bonus)

- ✅ **TWAP Strategy**: Time-Weighted Average Price execution
- ✅ **Grid Strategy**: Automated buy-low/sell-high within price range

### Technical Features

- ✅ **Comprehensive Logging**: Structured logging with timestamps and error traces
- ✅ **Input Validation**: Validate symbol, quantity, and price thresholds
- ✅ **Error Handling**: Robust error handling for all scenarios
- ✅ **Testnet Integration**: Safe testing environment
- ✅ **Modular Design**: Separate modules for different order types

## Installation

1. Clone the repository:
```bash
git clone https://github.com/bhongyash111-coder/Yash-binance-bot.git
cd binancetrade_bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Get your Binance Testnet API credentials:
   - Visit [Binance Testnet](https://testnet.binancefuture.com/)
   - Register and activate your account
   - Generate API key and secret

## Usage

### Basic Usage

All commands follow this pattern:

```bash
python src/basic_bot.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET [command] [arguments]
```

### Available Commands

#### 1. Market Order
Place a market order (immediate execution at current market price):

```bash
python src/basic_bot.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET market BTCUSDT BUY 0.001
```

#### 2. Limit Order
Place a limit order (executes only at specified price or better):

```bash
python src/basic_bot.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET limit BTCUSDT BUY 0.001 50000
```

#### 3. Stop-Limit Order
Place a stop-limit order (triggers when stop price is reached):

```bash
python src/basic_bot.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET stop-limit BTCUSDT SELL 0.001 45000 46000
```

#### 4. OCO Order (One-Cancels-Other)
Place an OCO order (combines limit and stop orders):

```bash
python src/basic_bot.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET oco BTCUSDT SELL 0.001 55000 50000 49000
```

#### 5. Account Information
View your account balance and information:

```bash
python src/basic_bot.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET account
```

#### 6. Get Current Price
Get the current price of a trading pair:

```bash
python src/basic_bot.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET price BTCUSDT
```

#### 7. View Open Orders
View all open orders:

```bash
python src/basic_bot.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET orders
```

Filter by symbol:

```bash
python src/basic_bot.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET orders --symbol BTCUSDT
```

### Advanced Order Modules

You can also use individual modules directly:

```bash
# Market order
python src/market_orders.py BTCUSDT BUY 0.001 --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET

# Limit order
python src/limit_orders.py BTCUSDT BUY 0.001 50000 --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET

# OCO order
python src/advanced/oco.py BTCUSDT SELL 0.001 55000 50000 49000 --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET

# TWAP strategy (symbol, side, total_quantity, num_orders, time_interval_minutes)
python src/advanced/twap.py BTCUSDT BUY 0.01 10 5 --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET

# Grid strategy (symbol, lower_price, upper_price, grid_levels, quantity_per_order)
python src/advanced/grid_strategy.py BTCUSDT 45000 55000 10 0.001 --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET

# Stop-limit order
python src/advanced/stop_limit.py BTCUSDT SELL 0.001 45000 46000 --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET
```

## Project Structure

```
binancetrade_bot/
├── src/
│   ├── market_orders.py      # Market order implementation
│   ├── limit_orders.py       # Limit order implementation
│   ├── logging_config.py     # Logging configuration
│   └── advanced/             # Advanced trading strategies
│       ├── oco.py            # OCO order implementation
│       ├── twap.py           # TWAP strategy
│       ├── grid_strategy.py  # Grid trading strategy
│       └── stop_limit.py     # Stop-limit orders
├── bot.log                   # Log file (auto-generated)
├── requirements.txt          # Python dependencies
└── README.md                 # Documentation
```

## Logging

All API requests, responses, and errors are logged to `bot.log` file with:

- Timestamp of each operation
- API request details
- Response data
- Error messages and stack traces

## Error Handling

The bot includes comprehensive error handling for:

- Invalid API credentials
- Network connectivity issues
- Invalid order parameters
- Insufficient balance
- API rate limiting

## Safety Features

- **Testnet Only**: No real funds at risk
- **Input Validation**: All parameters are validated before execution
- **Comprehensive Logging**: Track all operations and errors
- **Rate Limit Compliance**: Respects API rate limits
- **Safe Order Execution**: Validates orders before submission

## Example Usage Session

```bash
# Check account balance
python src/basic_bot.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET account

# Get current BTC price
python src/basic_bot.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET price BTCUSDT

# Place a small test market order
python src/basic_bot.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET market BTCUSDT BUY 0.001

# Check open orders
python src/basic_bot.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET orders
```

## Support

For issues or questions:

1. Check the `bot.log` file for detailed error information
2. Review this documentation
3. Submit an issue in the GitHub repository: https://github.com/bhongyash111-coder/Yash-binance-bot

## Security Best Practices

⚠️ **Important Security Notes:**

- **Never commit API keys** to version control
- Store credentials in environment variables or secure configuration files
- Use `.gitignore` to exclude sensitive files
- This bot is for **TESTNET ONLY** - always test thoroughly before using on mainnet
- Regularly rotate your API keys
- Use API key restrictions (IP whitelist, permissions) when possible

## License

This project is created for educational purposes.
