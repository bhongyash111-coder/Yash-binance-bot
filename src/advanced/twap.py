"""
TWAP (Time-Weighted Average Price) Orders Module for Binance Futures Trading Bot
Handles TWAP strategy that splits large orders into smaller chunks over time
"""

import logging
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException


class TWAPStrategy:
    """
    Implements TWAP (Time-Weighted Average Price) strategy for large order execution
    """
    
    def __init__(self, client: Client, logger: logging.Logger):
        self.client = client
        self.logger = logger
        self.active_strategies = {}
    
    def execute_twap_order(self, symbol: str, side: str, total_quantity: float,
                          duration_minutes: int, num_slices: int,
                          position_side: str = "BOTH") -> Dict:
        """
        Execute a TWAP order by splitting it into smaller chunks over time
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTCUSDT')
            side (str): 'BUY' or 'SELL'
            total_quantity (float): Total quantity to execute
            duration_minutes (int): Total duration in minutes
            num_slices (int): Number of slices to split the order
            position_side (str): Position side ('LONG', 'SHORT', or 'BOTH')
            
        Returns:
            Dict: TWAP strategy execution details
        """
        try:
            strategy_id = f"TWAP_{symbol}_{side}_{int(time.time())}"
            
            self.logger.info(f"Starting TWAP strategy {strategy_id}")
            self.logger.info(f"Symbol: {symbol}, Side: {side}, Total Qty: {total_quantity}")
            self.logger.info(f"Duration: {duration_minutes} minutes, Slices: {num_slices}")
            
            # Validate inputs
            if side not in ['BUY', 'SELL']:
                raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")
            
            if total_quantity <= 0:
                raise ValueError(f"Invalid total quantity: {total_quantity}. Must be positive")
            
            if duration_minutes <= 0:
                raise ValueError(f"Invalid duration: {duration_minutes}. Must be positive")
            
            if num_slices <= 0:
                raise ValueError(f"Invalid number of slices: {num_slices}. Must be positive")
            
            # Calculate slice parameters
            slice_quantity = total_quantity / num_slices
            slice_interval = (duration_minutes * 60) / num_slices  # seconds
            
            self.logger.info(f"Slice quantity: {slice_quantity}")
            self.logger.info(f"Slice interval: {slice_interval} seconds")
            
            # Create strategy record
            strategy = {
                'id': strategy_id,
                'symbol': symbol,
                'side': side,
                'total_quantity': total_quantity,
                'remaining_quantity': total_quantity,
                'duration_minutes': duration_minutes,
                'num_slices': num_slices,
                'slice_quantity': slice_quantity,
                'slice_interval': slice_interval,
                'start_time': datetime.now(),
                'status': 'RUNNING',
                'executed_orders': [],
                'total_executed': 0.0,
                'average_price': 0.0
            }
            
            self.active_strategies[strategy_id] = strategy
            
            # Start TWAP execution in a separate thread
            execution_thread = threading.Thread(
                target=self._execute_twap_slices,
                args=(strategy_id,)
            )
            execution_thread.daemon = True
            execution_thread.start()
            
            self.logger.info(f"TWAP strategy {strategy_id} started successfully")
            
            return {
                'strategy_id': strategy_id,
                'status': 'STARTED',
                'total_quantity': total_quantity,
                'num_slices': num_slices,
                'slice_quantity': slice_quantity,
                'slice_interval': slice_interval,
                'start_time': strategy['start_time'].isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error starting TWAP strategy: {e}")
            raise
    
    def _execute_twap_slices(self, strategy_id: str):
        """
        Execute TWAP slices in a separate thread
        
        Args:
            strategy_id (str): Strategy ID to execute
        """
        try:
            strategy = self.active_strategies[strategy_id]
            
            for slice_num in range(strategy['num_slices']):
                if strategy['status'] != 'RUNNING':
                    self.logger.info(f"Strategy {strategy_id} stopped, skipping slice {slice_num + 1}")
                    break
                
                # Wait for the slice interval (except for the first slice)
                if slice_num > 0:
                    time.sleep(strategy['slice_interval'])
                
                # Execute the slice
                self._execute_slice(strategy_id, slice_num + 1)
            
            # Mark strategy as completed
            if strategy['status'] == 'RUNNING':
                strategy['status'] = 'COMPLETED'
                strategy['end_time'] = datetime.now()
                self.logger.info(f"TWAP strategy {strategy_id} completed")
            
        except Exception as e:
            self.logger.error(f"Error executing TWAP slices for {strategy_id}: {e}")
            strategy['status'] = 'ERROR'
            strategy['error'] = str(e)
    
    def _execute_slice(self, strategy_id: str, slice_num: int):
        """
        Execute a single TWAP slice
        
        Args:
            strategy_id (str): Strategy ID
            slice_num (int): Slice number
        """
        try:
            strategy = self.active_strategies[strategy_id]
            
            if strategy['remaining_quantity'] <= 0:
                self.logger.info(f"Strategy {strategy_id} - no remaining quantity for slice {slice_num}")
                return
            
            # Get current market price
            ticker = self.client.futures_symbol_ticker(symbol=strategy['symbol'])
            current_price = float(ticker['price'])
            
            # Calculate slice quantity (use remaining quantity for the last slice)
            slice_quantity = min(strategy['slice_quantity'], strategy['remaining_quantity'])
            
            self.logger.info(f"Executing slice {slice_num}/{strategy['num_slices']} for {strategy_id}")
            self.logger.info(f"Slice quantity: {slice_quantity}, Current price: {current_price}")
            
            # Place market order for the slice
            order = self.client.futures_create_order(
                symbol=strategy['symbol'],
                side=strategy['side'],
                type='MARKET',
                quantity=slice_quantity,
                positionSide=strategy.get('position_side', 'BOTH')
            )
            
            # Update strategy with executed order
            strategy['executed_orders'].append({
                'slice_num': slice_num,
                'order_id': order['orderId'],
                'quantity': slice_quantity,
                'price': current_price,
                'timestamp': datetime.now().isoformat()
            })
            
            strategy['remaining_quantity'] -= slice_quantity
            strategy['total_executed'] += slice_quantity
            
            # Calculate average price
            total_value = sum(order['quantity'] * order['price'] for order in strategy['executed_orders'])
            strategy['average_price'] = total_value / strategy['total_executed'] if strategy['total_executed'] > 0 else 0
            
            self.logger.info(f"Slice {slice_num} executed successfully: Order {order['orderId']}")
            self.logger.info(f"Remaining quantity: {strategy['remaining_quantity']}")
            self.logger.info(f"Average price so far: {strategy['average_price']:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error executing slice {slice_num} for {strategy_id}: {e}")
            strategy['status'] = 'ERROR'
            strategy['error'] = str(e)
    
    def stop_twap_strategy(self, strategy_id: str) -> Dict:
        """
        Stop a running TWAP strategy
        
        Args:
            strategy_id (str): Strategy ID to stop
            
        Returns:
            Dict: Strategy status after stopping
        """
        try:
            if strategy_id not in self.active_strategies:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            strategy = self.active_strategies[strategy_id]
            strategy['status'] = 'STOPPED'
            strategy['end_time'] = datetime.now()
            
            self.logger.info(f"TWAP strategy {strategy_id} stopped")
            
            return {
                'strategy_id': strategy_id,
                'status': 'STOPPED',
                'total_executed': strategy['total_executed'],
                'remaining_quantity': strategy['remaining_quantity'],
                'average_price': strategy['average_price']
            }
            
        except Exception as e:
            self.logger.error(f"Error stopping TWAP strategy: {e}")
            raise
    
    def get_strategy_status(self, strategy_id: str) -> Dict:
        """
        Get status of a TWAP strategy
        
        Args:
            strategy_id (str): Strategy ID
            
        Returns:
            Dict: Strategy status information
        """
        try:
            if strategy_id not in self.active_strategies:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            strategy = self.active_strategies[strategy_id]
            
            return {
                'strategy_id': strategy_id,
                'status': strategy['status'],
                'symbol': strategy['symbol'],
                'side': strategy['side'],
                'total_quantity': strategy['total_quantity'],
                'total_executed': strategy['total_executed'],
                'remaining_quantity': strategy['remaining_quantity'],
                'average_price': strategy['average_price'],
                'num_slices': strategy['num_slices'],
                'executed_slices': len(strategy['executed_orders']),
                'start_time': strategy['start_time'].isoformat(),
                'end_time': strategy.get('end_time', '').isoformat() if strategy.get('end_time') else None,
                'error': strategy.get('error')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting strategy status: {e}")
            raise
    
    def get_all_strategies(self) -> List[Dict]:
        """
        Get all TWAP strategies
        
        Returns:
            List[Dict]: List of all strategies
        """
        try:
            strategies = []
            for strategy_id, strategy in self.active_strategies.items():
                strategies.append(self.get_strategy_status(strategy_id))
            
            self.logger.info(f"Retrieved {len(strategies)} TWAP strategies")
            return strategies
            
        except Exception as e:
            self.logger.error(f"Error getting all strategies: {e}")
            raise


def main():
    """CLI interface for TWAP orders"""
    import argparse
    import sys
    from binance.client import Client
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger('TWAPStrategy')
    
    parser = argparse.ArgumentParser(description='Binance Futures TWAP Strategy Bot')
    parser.add_argument('symbol', help='Trading pair symbol (e.g., BTCUSDT)')
    parser.add_argument('side', choices=['BUY', 'SELL'], help='Order side')
    parser.add_argument('quantity', type=float, help='Total order quantity')
    parser.add_argument('duration', type=int, help='Duration in minutes')
    parser.add_argument('slices', type=int, help='Number of slices')
    parser.add_argument('--api-key', required=True, help='Binance API key')
    parser.add_argument('--api-secret', required=True, help='Binance API secret')
    parser.add_argument('--testnet', action='store_true', default=True, help='Use testnet')
    parser.add_argument('--position-side', default='BOTH', 
                       choices=['LONG', 'SHORT', 'BOTH'], help='Position side')
    
    args = parser.parse_args()
    
    try:
        # Initialize client
        if args.testnet:
            client = Client(args.api_key, args.api_secret, testnet=True)
        else:
            client = Client(args.api_key, args.api_secret)
        
        # Initialize TWAP strategy
        twap = TWAPStrategy(client, logger)
        
        # Execute TWAP order
        result = twap.execute_twap_order(
            symbol=args.symbol,
            side=args.side,
            total_quantity=args.quantity,
            duration_minutes=args.duration,
            num_slices=args.slices,
            position_side=args.position_side
        )
        
        print(f"✅ TWAP strategy started successfully!")
        print(f"Strategy ID: {result['strategy_id']}")
        print(f"Total Quantity: {result['total_quantity']}")
        print(f"Number of Slices: {result['num_slices']}")
        print(f"Slice Quantity: {result['slice_quantity']}")
        print(f"Slice Interval: {result['slice_interval']} seconds")
        print(f"Start Time: {result['start_time']}")
        
        print(f"\n📊 Monitor progress with:")
        print(f"python src/advanced/twap.py status {result['strategy_id']} --api-key {args.api_key} --api-secret {args.api_secret}")
        
    except Exception as e:
        logger.error(f"Failed to start TWAP strategy: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
