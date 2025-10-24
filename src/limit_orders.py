"""
Limit Orders Module for Binance Futures Trading Bot
Handles limit orders with specific price execution
"""

import logging
import json
from datetime import datetime
from typing import Dict, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException


class LimitOrderHandler:
    """
    Handles limit order operations for Binance Futures
    """
    
    def __init__(self, client: Client, logger: logging.Logger):
        self.client = client
        self.logger = logger
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float,
                         time_in_force: str = "GTC", position_side: str = "BOTH") -> Dict:
        """
        Place a limit order with specific price
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTCUSDT')
            side (str): 'BUY' or 'SELL'
            quantity (float): Order quantity
            price (float): Order price
            time_in_force (str): Time in force ('GTC', 'IOC', 'FOK')
            position_side (str): Position side ('LONG', 'SHORT', or 'BOTH')
            
        Returns:
            Dict: Order response from Binance API
        """
        try:
            self.logger.info(f"Placing limit {side} order for {quantity} {symbol} at {price}")
            self.logger.info(f"Time in force: {time_in_force}, Position side: {position_side}")
            
            # Validate inputs
            if side not in ['BUY', 'SELL']:
                raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")
            
            if quantity <= 0:
                raise ValueError(f"Invalid quantity: {quantity}. Must be positive")
            
            if price <= 0:
                raise ValueError(f"Invalid price: {price}. Must be positive")
            
            if time_in_force not in ['GTC', 'IOC', 'FOK']:
                raise ValueError(f"Invalid time in force: {time_in_force}")
            
            # Place the limit order
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce=time_in_force,
                positionSide=position_side
            )
            
            # Log successful order placement
            self.logger.info(f"Limit order placed successfully: {order['orderId']}")
            self.logger.info(f"Order status: {order['status']}")
            self.logger.info(f"Order price: {order['price']}")
            self.logger.info(f"Order quantity: {order['origQty']}")
            
            # Log full order details
            self.logger.debug(f"Full order response: {json.dumps(order, indent=2)}")
            
            return order
            
        except BinanceAPIException as e:
            error_msg = f"Binance API error placing limit order: {e}"
            self.logger.error(error_msg)
            raise
        except BinanceOrderException as e:
            error_msg = f"Binance order error placing limit order: {e}"
            self.logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error placing limit order: {e}"
            self.logger.error(error_msg)
            raise
    
    def modify_limit_order(self, symbol: str, order_id: int, quantity: Optional[float] = None,
                          price: Optional[float] = None) -> Dict:
        """
        Modify an existing limit order
        
        Args:
            symbol (str): Trading pair symbol
            order_id (int): Order ID to modify
            quantity (float, optional): New quantity
            price (float, optional): New price
            
        Returns:
            Dict: Modified order response
        """
        try:
            self.logger.info(f"Modifying limit order {order_id} for {symbol}")
            
            # Get current order details
            current_order = self.client.futures_get_order(symbol=symbol, orderId=order_id)
            
            # Use current values if not provided
            new_quantity = quantity if quantity is not None else float(current_order['origQty'])
            new_price = price if price is not None else float(current_order['price'])
            
            # Cancel the existing order
            self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
            self.logger.info(f"Cancelled order {order_id}")
            
            # Place new order with modified parameters
            new_order = self.client.futures_create_order(
                symbol=symbol,
                side=current_order['side'],
                type='LIMIT',
                quantity=new_quantity,
                price=new_price,
                timeInForce=current_order['timeInForce'],
                positionSide=current_order['positionSide']
            )
            
            self.logger.info(f"Order modified successfully: {new_order['orderId']}")
            return new_order
            
        except Exception as e:
            self.logger.error(f"Error modifying limit order: {e}")
            raise
    
    def cancel_limit_order(self, symbol: str, order_id: int) -> Dict:
        """
        Cancel a limit order
        
        Args:
            symbol (str): Trading pair symbol
            order_id (int): Order ID to cancel
            
        Returns:
            Dict: Cancellation response
        """
        try:
            self.logger.info(f"Cancelling limit order {order_id} for {symbol}")
            
            result = self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
            
            self.logger.info(f"Order {order_id} cancelled successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error cancelling limit order: {e}")
            raise
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict:
        """
        Get status of a limit order
        
        Args:
            symbol (str): Trading pair symbol
            order_id (int): Order ID
            
        Returns:
            Dict: Order status information
        """
        try:
            order = self.client.futures_get_order(symbol=symbol, orderId=order_id)
            self.logger.info(f"Retrieved order status for {order_id}")
            return order
        except Exception as e:
            self.logger.error(f"Error getting order status: {e}")
            raise
    
    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """
        Get all open limit orders
        
        Args:
            symbol (str, optional): Filter by symbol
            
        Returns:
            list: List of open orders
        """
        try:
            if symbol:
                orders = self.client.futures_get_open_orders(symbol=symbol)
            else:
                orders = self.client.futures_get_open_orders()
            
            self.logger.info(f"Retrieved {len(orders)} open orders")
            return orders
        except Exception as e:
            self.logger.error(f"Error getting open orders: {e}")
            raise


def main():
    """CLI interface for limit orders"""
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
    logger = logging.getLogger('LimitOrderHandler')
    
    parser = argparse.ArgumentParser(description='Binance Futures Limit Order Bot')
    parser.add_argument('symbol', help='Trading pair symbol (e.g., BTCUSDT)')
    parser.add_argument('side', choices=['BUY', 'SELL'], help='Order side')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('price', type=float, help='Order price')
    parser.add_argument('--api-key', required=True, help='Binance API key')
    parser.add_argument('--api-secret', required=True, help='Binance API secret')
    parser.add_argument('--testnet', action='store_true', default=True, help='Use testnet')
    parser.add_argument('--time-in-force', default='GTC', choices=['GTC', 'IOC', 'FOK'],
                       help='Time in force')
    parser.add_argument('--position-side', default='BOTH', 
                       choices=['LONG', 'SHORT', 'BOTH'], help='Position side')
    
    args = parser.parse_args()
    
    try:
        # Initialize client
        if args.testnet:
            client = Client(args.api_key, args.api_secret, testnet=True)
        else:
            client = Client(args.api_key, args.api_secret)
        
        # Initialize limit order handler
        handler = LimitOrderHandler(client, logger)
        
        # Place limit order
        order = handler.place_limit_order(
            symbol=args.symbol,
            side=args.side,
            quantity=args.quantity,
            price=args.price,
            time_in_force=args.time_in_force,
            position_side=args.position_side
        )
        
        print(f"✅ Limit order placed successfully!")
        print(f"Order ID: {order['orderId']}")
        print(f"Status: {order['status']}")
        print(f"Price: ${order['price']}")
        print(f"Quantity: {order['origQty']}")
        print(f"Time in Force: {order['timeInForce']}")
        
    except Exception as e:
        logger.error(f"Failed to place limit order: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
