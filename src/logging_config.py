"""
Comprehensive Logging Configuration for Binance Trading Bot
Provides structured logging for all trading operations
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import traceback


class TradingLogger:
    """
    Enhanced logging system for trading operations
    """
    
    def __init__(self, log_file: str = "bot.log", log_level: str = "INFO"):
        self.log_file = log_file
        self.log_level = getattr(logging, log_level.upper())
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup the main logger with file and console handlers"""
        
        # Create logger
        logger = logging.getLogger('TradingBot')
        logger.setLevel(self.log_level)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_api_request(self, method: str, endpoint: str, params: Dict[str, Any], 
                       response: Optional[Dict] = None, error: Optional[Exception] = None):
        """Log API request details"""
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'API_REQUEST',
            'method': method,
            'endpoint': endpoint,
            'params': params,
            'response': response,
            'error': str(error) if error else None
        }
        
        if error:
            self.logger.error(f"API Request Failed: {method} {endpoint}")
            self.logger.error(f"Parameters: {json.dumps(params, indent=2)}")
            self.logger.error(f"Error: {error}")
        else:
            self.logger.info(f"API Request: {method} {endpoint}")
            self.logger.debug(f"Parameters: {json.dumps(params, indent=2)}")
            if response:
                self.logger.debug(f"Response: {json.dumps(response, indent=2)}")
    
    def log_order_placement(self, order_type: str, symbol: str, side: str, 
                          quantity: float, price: Optional[float] = None,
                          order_id: Optional[str] = None, status: str = "PLACED"):
        """Log order placement details"""
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'ORDER_PLACEMENT',
            'order_type': order_type,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'order_id': order_id,
            'status': status
        }
        
        self.logger.info(f"Order {status}: {order_type} {side} {quantity} {symbol} @ {price}")
        self.logger.debug(f"Order details: {json.dumps(log_data, indent=2)}")
    
    def log_order_execution(self, order_id: str, symbol: str, executed_quantity: float,
                          executed_price: float, commission: float = 0.0):
        """Log order execution details"""
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'ORDER_EXECUTION',
            'order_id': order_id,
            'symbol': symbol,
            'executed_quantity': executed_quantity,
            'executed_price': executed_price,
            'commission': commission,
            'total_value': executed_quantity * executed_price
        }
        
        self.logger.info(f"Order Executed: {order_id} - {executed_quantity} {symbol} @ {executed_price}")
        self.logger.debug(f"Execution details: {json.dumps(log_data, indent=2)}")
    
    def log_strategy_event(self, strategy_type: str, strategy_id: str, event: str,
                          details: Dict[str, Any]):
        """Log strategy events (TWAP, Grid, etc.)"""
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'STRATEGY_EVENT',
            'strategy_type': strategy_type,
            'strategy_id': strategy_id,
            'event': event,
            'details': details
        }
        
        self.logger.info(f"Strategy Event: {strategy_type} {strategy_id} - {event}")
        self.logger.debug(f"Event details: {json.dumps(log_data, indent=2)}")
    
    def log_error(self, error: Exception, context: str = "", additional_info: Dict[str, Any] = None):
        """Log errors with full stack trace"""
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'ERROR',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'stack_trace': traceback.format_exc(),
            'additional_info': additional_info or {}
        }
        
        self.logger.error(f"Error in {context}: {error}")
        self.logger.error(f"Stack trace: {traceback.format_exc()}")
        self.logger.debug(f"Error details: {json.dumps(log_data, indent=2)}")
    
    def log_account_balance(self, balance: float, available_balance: float, 
                           unrealized_pnl: float = 0.0):
        """Log account balance information"""
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'ACCOUNT_BALANCE',
            'total_balance': balance,
            'available_balance': available_balance,
            'unrealized_pnl': unrealized_pnl
        }
        
        self.logger.info(f"Account Balance: {balance} USDT (Available: {available_balance})")
        self.logger.debug(f"Balance details: {json.dumps(log_data, indent=2)}")
    
    def log_price_movement(self, symbol: str, old_price: float, new_price: float,
                          price_change_pct: float):
        """Log price movement information"""
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'PRICE_MOVEMENT',
            'symbol': symbol,
            'old_price': old_price,
            'new_price': new_price,
            'price_change_pct': price_change_pct
        }
        
        self.logger.info(f"Price Movement: {symbol} {old_price} -> {new_price} ({price_change_pct:+.2f}%)")
        self.logger.debug(f"Price details: {json.dumps(log_data, indent=2)}")
    
    def log_performance_metrics(self, strategy_id: str, total_trades: int, 
                              winning_trades: int, total_pnl: float, 
                              win_rate: float, avg_trade_pnl: float):
        """Log performance metrics"""
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'PERFORMANCE_METRICS',
            'strategy_id': strategy_id,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'avg_trade_pnl': avg_trade_pnl
        }
        
        self.logger.info(f"Performance: {strategy_id} - {total_trades} trades, {win_rate:.1f}% win rate, PnL: {total_pnl:.2f}")
        self.logger.debug(f"Performance details: {json.dumps(log_data, indent=2)}")
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance"""
        return self.logger
    
    def create_log_summary(self) -> Dict[str, Any]:
        """Create a summary of recent log activity"""
        
        try:
            if not os.path.exists(self.log_file):
                return {"error": "Log file not found"}
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Count different log types
            log_counts = {
                'API_REQUEST': 0,
                'ORDER_PLACEMENT': 0,
                'ORDER_EXECUTION': 0,
                'STRATEGY_EVENT': 0,
                'ERROR': 0,
                'ACCOUNT_BALANCE': 0,
                'PRICE_MOVEMENT': 0,
                'PERFORMANCE_METRICS': 0
            }
            
            for line in lines:
                for log_type in log_counts:
                    if log_type in line:
                        log_counts[log_type] += 1
            
            return {
                'timestamp': datetime.now().isoformat(),
                'log_file': self.log_file,
                'total_lines': len(lines),
                'log_counts': log_counts,
                'last_activity': lines[-1].strip() if lines else "No activity"
            }
            
        except Exception as e:
            return {"error": f"Failed to create log summary: {e}"}


# Global logger instance
trading_logger = TradingLogger()


def get_trading_logger() -> TradingLogger:
    """Get the global trading logger instance"""
    return trading_logger

