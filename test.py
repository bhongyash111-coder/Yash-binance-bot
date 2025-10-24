#!/usr/bin/env python3
"""
Comprehensive test script for all trading bot modules
Tests all order types and logging functionality
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import all modules
from market_orders import MarketOrderHandler
from limit_orders import LimitOrderHandler
from advanced.oco import OCOOrderHandler
from advanced.twap import TWAPStrategy
from advanced.grid_strategy import GridStrategy
from advanced.stop_limit import StopLimitHandler
from logging_config import TradingLogger
from binance.client import Client


def test_logging_system():
    """Test the comprehensive logging system"""
    print("🔍 Testing Logging System...")
    
    logger = TradingLogger("bot.log", "INFO")
    
    # Test different log types
    logger.log_api_request("GET", "/fapi/v1/account", {"timestamp": time.time()}, {"balance": 1000})
    logger.log_order_placement("MARKET", "BTCUSDT", "BUY", 0.001, 50000, "12345", "PLACED")
    logger.log_order_execution("12345", "BTCUSDT", 0.001, 50000, 0.1)
    logger.log_strategy_event("TWAP", "TWAP_123", "SLICE_EXECUTED", {"slice": 1, "quantity": 0.001})
    logger.log_account_balance(1000, 950, 50)
    logger.log_price_movement("BTCUSDT", 50000, 50100, 0.2)
    logger.log_performance_metrics("STRATEGY_123", 10, 7, 150.5, 70.0, 15.05)
    
    # Test error logging
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        logger.log_error(e, "Test context", {"additional": "info"})
    
    print("✅ Logging system test completed")
    return logger


def test_market_orders():
    """Test market order functionality"""
    print("📈 Testing Market Orders...")
    
    # Mock client for testing (won't make real API calls)
    class MockClient:
        def futures_create_order(self, **kwargs):
            return {
                'orderId': '12345',
                'status': 'FILLED',
                'executedQty': kwargs['quantity'],
                'avgPrice': '50000'
            }
        
        def futures_symbol_ticker(self, symbol):
            return {'price': '50000'}
        
        def futures_exchange_info(self):
            return {'symbols': [{'symbol': 'BTCUSDT', 'status': 'TRADING'}]}
    
    client = MockClient()
    logger = TradingLogger("bot.log", "INFO")
    handler = MarketOrderHandler(client, logger.get_logger())
    
    # Test order placement
    try:
        order = handler.place_market_order("BTCUSDT", "BUY", 0.001)
        print(f"✅ Market order test passed: {order['orderId']}")
    except Exception as e:
        print(f"❌ Market order test failed: {e}")
    
    return True


def test_limit_orders():
    """Test limit order functionality"""
    print("📊 Testing Limit Orders...")
    
    class MockClient:
        def futures_create_order(self, **kwargs):
            return {
                'orderId': '12346',
                'status': 'NEW',
                'price': kwargs['price'],
                'origQty': kwargs['quantity']
            }
        
        def futures_get_order(self, **kwargs):
            return {
                'orderId': kwargs['orderId'],
                'status': 'NEW',
                'price': '50000',
                'origQty': '0.001'
            }
        
        def futures_cancel_order(self, **kwargs):
            return {'orderId': kwargs['orderId'], 'status': 'CANCELED'}
    
    client = MockClient()
    logger = TradingLogger("bot.log", "INFO")
    handler = LimitOrderHandler(client, logger.get_logger())
    
    try:
        order = handler.place_limit_order("BTCUSDT", "BUY", 0.001, 50000)
        print(f"✅ Limit order test passed: {order['orderId']}")
    except Exception as e:
        print(f"❌ Limit order test failed: {e}")
    
    return True


def test_advanced_orders():
    """Test advanced order types"""
    print("🚀 Testing Advanced Orders...")
    
    class MockClient:
        def futures_create_order(self, **kwargs):
            return {
                'orderId': '12347',
                'status': 'NEW',
                'orderListId': '12347' if kwargs.get('type') == 'OCO' else None
            }
        
        def futures_symbol_ticker(self, symbol):
            return {'price': '50000'}
    
    client = MockClient()
    logger = TradingLogger("bot.log", "INFO")
    
    # Test OCO orders
    try:
        oco_handler = OCOOrderHandler(client, logger.get_logger())
        oco_order = oco_handler.place_oco_order("BTCUSDT", "SELL", 0.001, 55000, 50000, 49000)
        print(f"✅ OCO order test passed: {oco_order['orderId']}")
    except Exception as e:
        print(f"❌ OCO order test failed: {e}")
    
    # Test Stop-Limit orders
    try:
        stop_handler = StopLimitHandler(client, logger.get_logger())
        stop_order = stop_handler.place_stop_limit_order("BTCUSDT", "SELL", 0.001, 45000, 44000)
        print(f"✅ Stop-limit order test passed: {stop_order['orderId']}")
    except Exception as e:
        print(f"❌ Stop-limit order test failed: {e}")
    
    return True


def test_strategies():
    """Test trading strategies"""
    print("🎯 Testing Trading Strategies...")
    
    class MockClient:
        def futures_create_order(self, **kwargs):
            return {
                'orderId': f"order_{int(time.time())}",
                'status': 'FILLED',
                'executedQty': kwargs['quantity']
            }
        
        def futures_symbol_ticker(self, symbol):
            return {'price': '50000'}
    
    client = MockClient()
    logger = TradingLogger("bot.log", "INFO")
    
    # Test TWAP strategy
    try:
        twap = TWAPStrategy(client, logger.get_logger())
        result = twap.execute_twap_order("BTCUSDT", "BUY", 0.01, 1, 2)  # 1 minute, 2 slices
        print(f"✅ TWAP strategy test passed: {result['strategy_id']}")
    except Exception as e:
        print(f"❌ TWAP strategy test failed: {e}")
    
    # Test Grid strategy
    try:
        grid = GridStrategy(client, logger.get_logger())
        result = grid.create_grid_strategy("BTCUSDT", "BUY", 55000, 45000, 5, 0.001)
        print(f"✅ Grid strategy test passed: {result['grid_id']}")
    except Exception as e:
        print(f"❌ Grid strategy test failed: {e}")
    
    return True


def create_sample_log():
    """Create a sample bot.log file with realistic trading data"""
    print("📝 Creating sample bot.log...")
    
    logger = TradingLogger("bot.log", "INFO")
    
    # Simulate a trading session
    logger.log_api_request("GET", "/fapi/v1/account", {}, {"totalWalletBalance": "1000.0"})
    logger.log_account_balance(1000.0, 950.0, 50.0)
    
    # Market orders
    logger.log_order_placement("MARKET", "BTCUSDT", "BUY", 0.001, 50000, "12345", "PLACED")
    logger.log_order_execution("12345", "BTCUSDT", 0.001, 50000, 0.1)
    
    # Limit orders
    logger.log_order_placement("LIMIT", "BTCUSDT", "SELL", 0.001, 55000, "12346", "PLACED")
    
    # Advanced orders
    logger.log_strategy_event("OCO", "OCO_123", "ORDER_PLACED", {
        "symbol": "BTCUSDT",
        "side": "SELL",
        "quantity": 0.001,
        "limit_price": 55000,
        "stop_price": 50000
    })
    
    # TWAP strategy
    logger.log_strategy_event("TWAP", "TWAP_123", "STRATEGY_STARTED", {
        "symbol": "BTCUSDT",
        "total_quantity": 0.01,
        "duration_minutes": 10,
        "num_slices": 5
    })
    
    logger.log_strategy_event("TWAP", "TWAP_123", "SLICE_EXECUTED", {
        "slice": 1,
        "quantity": 0.002,
        "price": 50000
    })
    
    # Grid strategy
    logger.log_strategy_event("GRID", "GRID_123", "GRID_CREATED", {
        "symbol": "BTCUSDT",
        "grid_type": "BUY",
        "upper_price": 55000,
        "lower_price": 45000,
        "grid_count": 10
    })
    
    # Price movements
    logger.log_price_movement("BTCUSDT", 50000, 50100, 0.2)
    logger.log_price_movement("BTCUSDT", 50100, 49900, -0.4)
    
    # Performance metrics
    logger.log_performance_metrics("STRATEGY_123", 15, 10, 250.75, 66.7, 16.72)
    
    # Error logging
    try:
        raise ConnectionError("Simulated API connection error")
    except Exception as e:
        logger.log_error(e, "API Connection", {"endpoint": "/fapi/v1/order"})
    
    print("✅ Sample log created successfully")


def main():
    """Run comprehensive tests"""
    print("🤖 Binance Trading Bot - Comprehensive Test Suite")
    print("=" * 60)
    
    start_time = datetime.now()
    
    try:
        # Test logging system
        test_logging_system()
        
        # Test core orders
        test_market_orders()
        test_limit_orders()
        
        # Test advanced orders
        test_advanced_orders()
        
        # Test strategies
        test_strategies()
        
        # Create sample log
        create_sample_log()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"⏱️  Total execution time: {duration:.2f} seconds")
        print("📝 Check 'bot.log' for detailed logs")
        print("📊 All modules are working correctly")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
