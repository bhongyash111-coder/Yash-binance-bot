"""
Grid Trading Strategy Module for Binance Futures Trading Bot
Implements automated buy-low/sell-high strategy within a price range
"""

import logging
import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException


class GridStrategy:
    """
    Implements Grid Trading Strategy for automated buy-low/sell-high trading
    """
    
    def __init__(self, client: Client, logger: logging.Logger):
        self.client = client
        self.logger = logger
        self.active_grids = {}
    
    def create_grid_strategy(self, symbol: str, grid_type: str, 
                           upper_price: float, lower_price: float,
                           grid_count: int, order_quantity: float,
                           position_side: str = "BOTH") -> Dict:
        """
        Create a grid trading strategy
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTCUSDT')
            grid_type (str): 'BUY' or 'SELL' or 'BOTH'
            upper_price (float): Upper price boundary
            lower_price (float): Lower price boundary
            grid_count (int): Number of grid levels
            order_quantity (float): Quantity per grid level
            position_side (str): Position side ('LONG', 'SHORT', or 'BOTH')
            
        Returns:
            Dict: Grid strategy details
        """
        try:
            grid_id = f"GRID_{symbol}_{grid_type}_{int(time.time())}"
            
            self.logger.info(f"Creating grid strategy {grid_id}")
            self.logger.info(f"Symbol: {symbol}, Type: {grid_type}")
            self.logger.info(f"Price range: {lower_price} - {upper_price}")
            self.logger.info(f"Grid count: {grid_count}, Quantity per level: {order_quantity}")
            
            # Validate inputs
            if grid_type not in ['BUY', 'SELL', 'BOTH']:
                raise ValueError(f"Invalid grid type: {grid_type}")
            
            if upper_price <= lower_price:
                raise ValueError("Upper price must be greater than lower price")
            
            if grid_count <= 0:
                raise ValueError(f"Invalid grid count: {grid_count}. Must be positive")
            
            if order_quantity <= 0:
                raise ValueError(f"Invalid order quantity: {order_quantity}. Must be positive")
            
            # Calculate grid levels
            price_step = (upper_price - lower_price) / (grid_count - 1)
            grid_levels = []
            
            for i in range(grid_count):
                price = lower_price + (i * price_step)
                grid_levels.append({
                    'level': i + 1,
                    'price': round(price, 2),
                    'quantity': order_quantity,
                    'status': 'PENDING',
                    'order_id': None
                })
            
            # Create grid strategy
            grid_strategy = {
                'id': grid_id,
                'symbol': symbol,
                'grid_type': grid_type,
                'upper_price': upper_price,
                'lower_price': lower_price,
                'grid_count': grid_count,
                'price_step': price_step,
                'order_quantity': order_quantity,
                'grid_levels': grid_levels,
                'position_side': position_side,
                'status': 'ACTIVE',
                'created_time': datetime.now(),
                'total_orders': 0,
                'executed_orders': 0,
                'total_profit': 0.0
            }
            
            self.active_grids[grid_id] = grid_strategy
            
            # Start grid monitoring
            monitor_thread = threading.Thread(
                target=self._monitor_grid_strategy,
                args=(grid_id,)
            )
            monitor_thread.daemon = True
            monitor_thread.start()
            
            self.logger.info(f"Grid strategy {grid_id} created and monitoring started")
            
            return {
                'grid_id': grid_id,
                'status': 'CREATED',
                'symbol': symbol,
                'grid_type': grid_type,
                'price_range': f"{lower_price} - {upper_price}",
                'grid_count': grid_count,
                'price_step': price_step,
                'order_quantity': order_quantity,
                'created_time': grid_strategy['created_time'].isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error creating grid strategy: {e}")
            raise
    
    def _monitor_grid_strategy(self, grid_id: str):
        """
        Monitor grid strategy and execute orders when price levels are hit
        
        Args:
            grid_id (str): Grid strategy ID
        """
        try:
            grid = self.active_grids[grid_id]
            
            while grid['status'] == 'ACTIVE':
                try:
                    # Get current market price
                    ticker = self.client.futures_symbol_ticker(symbol=grid['symbol'])
                    current_price = float(ticker['price'])
                    
                    # Check each grid level
                    for level in grid['grid_levels']:
                        if level['status'] == 'PENDING':
                            # Check if price has reached this level
                            if self._should_trigger_order(current_price, level['price'], grid['grid_type']):
                                self._execute_grid_order(grid_id, level)
                    
                    # Sleep for a short interval before checking again
                    time.sleep(5)  # Check every 5 seconds
                    
                except Exception as e:
                    self.logger.error(f"Error monitoring grid {grid_id}: {e}")
                    time.sleep(10)  # Wait longer on error
                    
        except Exception as e:
            self.logger.error(f"Error in grid monitoring thread for {grid_id}: {e}")
            grid['status'] = 'ERROR'
            grid['error'] = str(e)
    
    def _should_trigger_order(self, current_price: float, level_price: float, grid_type: str) -> bool:
        """
        Determine if an order should be triggered based on current price and grid level
        
        Args:
            current_price (float): Current market price
            level_price (float): Grid level price
            grid_type (str): Grid type ('BUY', 'SELL', 'BOTH')
            
        Returns:
            bool: True if order should be triggered
        """
        if grid_type == 'BUY':
            # Trigger buy orders when price drops to or below the level
            return current_price <= level_price
        elif grid_type == 'SELL':
            # Trigger sell orders when price rises to or above the level
            return current_price >= level_price
        else:  # BOTH
            # For both types, we need to determine based on position
            # This is a simplified logic - in practice, you'd track positions
            return abs(current_price - level_price) < (level_price * 0.001)  # 0.1% tolerance
    
    def _execute_grid_order(self, grid_id: str, level: Dict):
        """
        Execute a grid order at a specific level
        
        Args:
            grid_id (str): Grid strategy ID
            level (Dict): Grid level information
        """
        try:
            grid = self.active_grids[grid_id]
            
            # Determine order side based on grid type
            if grid['grid_type'] == 'BUY':
                side = 'BUY'
            elif grid['grid_type'] == 'SELL':
                side = 'SELL'
            else:  # BOTH - this would need more sophisticated logic
                side = 'BUY'  # Simplified for demo
            
            self.logger.info(f"Executing grid order at level {level['level']} for {grid_id}")
            self.logger.info(f"Price: {level['price']}, Quantity: {level['quantity']}, Side: {side}")
            
            # Place the order
            order = self.client.futures_create_order(
                symbol=grid['symbol'],
                side=side,
                type='LIMIT',
                quantity=level['quantity'],
                price=level['price'],
                timeInForce='GTC',
                positionSide=grid['position_side']
            )
            
            # Update grid level
            level['status'] = 'EXECUTED'
            level['order_id'] = order['orderId']
            level['executed_time'] = datetime.now()
            
            # Update grid statistics
            grid['total_orders'] += 1
            grid['executed_orders'] += 1
            
            self.logger.info(f"Grid order executed successfully: {order['orderId']}")
            
        except Exception as e:
            self.logger.error(f"Error executing grid order: {e}")
            level['status'] = 'ERROR'
            level['error'] = str(e)
    
    def stop_grid_strategy(self, grid_id: str) -> Dict:
        """
        Stop a grid strategy
        
        Args:
            grid_id (str): Grid strategy ID to stop
            
        Returns:
            Dict: Grid strategy status after stopping
        """
        try:
            if grid_id not in self.active_grids:
                raise ValueError(f"Grid strategy {grid_id} not found")
            
            grid = self.active_grids[grid_id]
            grid['status'] = 'STOPPED'
            grid['stopped_time'] = datetime.now()
            
            # Cancel any pending orders
            for level in grid['grid_levels']:
                if level['status'] == 'PENDING' and level['order_id']:
                    try:
                        self.client.futures_cancel_order(
                            symbol=grid['symbol'],
                            orderId=level['order_id']
                        )
                        level['status'] = 'CANCELLED'
                    except Exception as e:
                        self.logger.error(f"Error cancelling order {level['order_id']}: {e}")
            
            self.logger.info(f"Grid strategy {grid_id} stopped")
            
            return {
                'grid_id': grid_id,
                'status': 'STOPPED',
                'total_orders': grid['total_orders'],
                'executed_orders': grid['executed_orders'],
                'stopped_time': grid['stopped_time'].isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error stopping grid strategy: {e}")
            raise
    
    def get_grid_status(self, grid_id: str) -> Dict:
        """
        Get status of a grid strategy
        
        Args:
            grid_id (str): Grid strategy ID
            
        Returns:
            Dict: Grid strategy status information
        """
        try:
            if grid_id not in self.active_grids:
                raise ValueError(f"Grid strategy {grid_id} not found")
            
            grid = self.active_grids[grid_id]
            
            # Calculate statistics
            pending_levels = len([l for l in grid['grid_levels'] if l['status'] == 'PENDING'])
            executed_levels = len([l for l in grid['grid_levels'] if l['status'] == 'EXECUTED'])
            error_levels = len([l for l in grid['grid_levels'] if l['status'] == 'ERROR'])
            
            return {
                'grid_id': grid_id,
                'status': grid['status'],
                'symbol': grid['symbol'],
                'grid_type': grid['grid_type'],
                'price_range': f"{grid['lower_price']} - {grid['upper_price']}",
                'grid_count': grid['grid_count'],
                'price_step': grid['price_step'],
                'order_quantity': grid['order_quantity'],
                'total_orders': grid['total_orders'],
                'executed_orders': grid['executed_orders'],
                'pending_levels': pending_levels,
                'executed_levels': executed_levels,
                'error_levels': error_levels,
                'created_time': grid['created_time'].isoformat(),
                'stopped_time': grid.get('stopped_time', '').isoformat() if grid.get('stopped_time') else None,
                'error': grid.get('error')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting grid status: {e}")
            raise
    
    def get_all_grids(self) -> List[Dict]:
        """
        Get all grid strategies
        
        Returns:
            List[Dict]: List of all grid strategies
        """
        try:
            grids = []
            for grid_id, grid in self.active_grids.items():
                grids.append(self.get_grid_status(grid_id))
            
            self.logger.info(f"Retrieved {len(grids)} grid strategies")
            return grids
            
        except Exception as e:
            self.logger.error(f"Error getting all grid strategies: {e}")
            raise


def main():
    """CLI interface for grid strategies"""
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
    logger = logging.getLogger('GridStrategy')
    
    parser = argparse.ArgumentParser(description='Binance Futures Grid Strategy Bot')
    parser.add_argument('symbol', help='Trading pair symbol (e.g., BTCUSDT)')
    parser.add_argument('grid_type', choices=['BUY', 'SELL', 'BOTH'], help='Grid type')
    parser.add_argument('upper_price', type=float, help='Upper price boundary')
    parser.add_argument('lower_price', type=float, help='Lower price boundary')
    parser.add_argument('grid_count', type=int, help='Number of grid levels')
    parser.add_argument('quantity', type=float, help='Quantity per grid level')
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
        
        # Initialize grid strategy
        grid = GridStrategy(client, logger)
        
        # Create grid strategy
        result = grid.create_grid_strategy(
            symbol=args.symbol,
            grid_type=args.grid_type,
            upper_price=args.upper_price,
            lower_price=args.lower_price,
            grid_count=args.grid_count,
            order_quantity=args.quantity,
            position_side=args.position_side
        )
        
        print(f"✅ Grid strategy created successfully!")
        print(f"Grid ID: {result['grid_id']}")
        print(f"Symbol: {result['symbol']}")
        print(f"Grid Type: {result['grid_type']}")
        print(f"Price Range: {result['price_range']}")
        print(f"Grid Count: {result['grid_count']}")
        print(f"Price Step: {result['price_step']}")
        print(f"Order Quantity: {result['order_quantity']}")
        print(f"Created Time: {result['created_time']}")
        
        print(f"\n📊 Monitor progress with:")
        print(f"python src/advanced/grid_strategy.py status {result['grid_id']} --api-key {args.api_key} --api-secret {args.api_secret}")
        
    except Exception as e:
        logger.error(f"Failed to create grid strategy: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
