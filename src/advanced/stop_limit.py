"""
Stop-Limit Orders Module for Binance Futures Trading Bot
Handles stop-limit orders that trigger when stop price is reached
"""

import logging
import json
from datetime import datetime
from typing import Dict, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException


class StopLimitHandler:
    """
    Handles stop-limit order operations for Binance Futures
    """
    
    def __init__(self, client: Client, logger: logging.Logger):
        self.client = client
        self.logger = logger
    
    def place_stop_limit_order(self, symbol: str, side: str, quantity: float,
                              stop_price: float, limit_price: float,
                              position_side: str = "BOTH") -> Dict:
        """
        Place a stop-limit order
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTCUSDT')
            side (str): 'BUY' or 'SELL'
            quantity (float): Order quantity
            stop_price (float): Stop price trigger
            limit_price (float): Limit order price
            position_side (str): Position side ('LONG', 'SHORT', or 'BOTH')
            
        Returns:
            Dict: Stop-limit order response from Binance API
        """
        try:
            self.logger.info(f"Placing stop-limit {side} order for {quantity} {symbol}")
            self.logger.info(f"Stop price: {stop_price}, Limit price: {limit_price}")
            self.logger.info(f"Position side: {position_side}")
            
            # Validate inputs
            if side not in ['BUY', 'SELL']:
                raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")
            
            if quantity <= 0:
                raise ValueError(f"Invalid quantity: {quantity}. Must be positive")
            
            if stop_price <= 0 or limit_price <= 0:
                raise ValueError("Stop price and limit price must be positive")
            
            # Validate price relationships based on side
            if side == 'BUY':
                if stop_price >= limit_price:
                    raise ValueError("For BUY orders: stop_price should be < limit_price")
            else:  # SELL
                if stop_price <= limit_price:
                    raise ValueError("For SELL orders: stop_price should be > limit_price")
            
            # Place the stop-limit order
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='STOP',
                quantity=quantity,
                price=limit_price,
                stopPrice=stop_price,
                timeInForce='GTC',
                positionSide=position_side
            )
            
            # Log successful order placement
            self.logger.info(f"Stop-limit order placed successfully: {order['orderId']}")
            self.logger.info(f"Order status: {order['status']}")
            self.logger.info(f"Stop price: {order['stopPrice']}")
            self.logger.info(f"Limit price: {order['price']}")
            
            # Log full order details
            self.logger.debug(f"Full stop-limit order response: {json.dumps(order, indent=2)}")
            
            return order
            
        except BinanceAPIException as e:
            error_msg = f"Binance API error placing stop-limit order: {e}"
            self.logger.error(error_msg)
            raise
        except BinanceOrderException as e:
            error_msg = f"Binance order error placing stop-limit order: {e}"
            self.logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error placing stop-limit order: {e}"
            self.logger.error(error_msg)
            raise
    
    def create_stop_loss_order(self, symbol: str, side: str, quantity: float,
                             current_price: float, stop_loss_pct: float = 0.02,
                             position_side: str = "BOTH") -> Dict:
        """
        Create a stop-loss order based on percentage
        
        Args:
            symbol (str): Trading pair symbol
            side (str): 'BUY' or 'SELL'
            quantity (float): Order quantity
            current_price (float): Current market price
            stop_loss_pct (float): Stop loss percentage (e.g., 0.02 for 2%)
            position_side (str): Position side
            
        Returns:
            Dict: Stop-loss order response
        """
        try:
            self.logger.info(f"Creating stop-loss order for {symbol}")
            self.logger.info(f"Current price: {current_price}, Stop loss: {stop_loss_pct*100}%")
            
            if side == 'BUY':
                # For long position: stop loss below current price
                stop_price = current_price * (1 - stop_loss_pct)
                limit_price = stop_price * 0.99  # Slightly below stop price
            else:  # SELL
                # For short position: stop loss above current price
                stop_price = current_price * (1 + stop_loss_pct)
                limit_price = stop_price * 1.01  # Slightly above stop price
            
            self.logger.info(f"Calculated stop price: {stop_price}, Limit price: {limit_price}")
            
            return self.place_stop_limit_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                stop_price=stop_price,
                limit_price=limit_price,
                position_side=position_side
            )
            
        except Exception as e:
            self.logger.error(f"Error creating stop-loss order: {e}")
            raise
    
    def create_take_profit_order(self, symbol: str, side: str, quantity: float,
                               current_price: float, take_profit_pct: float = 0.02,
                               position_side: str = "BOTH") -> Dict:
        """
        Create a take-profit order based on percentage
        
        Args:
            symbol (str): Trading pair symbol
            side (str): 'BUY' or 'SELL'
            quantity (float): Order quantity
            current_price (float): Current market price
            take_profit_pct (float): Take profit percentage (e.g., 0.02 for 2%)
            position_side (str): Position side
            
        Returns:
            Dict: Take-profit order response
        """
        try:
            self.logger.info(f"Creating take-profit order for {symbol}")
            self.logger.info(f"Current price: {current_price}, Take profit: {take_profit_pct*100}%")
            
            if side == 'BUY':
                # For long position: take profit above current price
                stop_price = current_price * (1 + take_profit_pct)
                limit_price = stop_price * 1.01  # Slightly above stop price
            else:  # SELL
                # For short position: take profit below current price
                stop_price = current_price * (1 - take_profit_pct)
                limit_price = stop_price * 0.99  # Slightly below stop price
            
            self.logger.info(f"Calculated stop price: {stop_price}, Limit price: {limit_price}")
            
            return self.place_stop_limit_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                stop_price=stop_price,
                limit_price=limit_price,
                position_side=position_side
            )
            
        except Exception as e:
            self.logger.error(f"Error creating take-profit order: {e}")
            raise
    
    def modify_stop_limit_order(self, symbol: str, order_id: int, 
                               new_stop_price: Optional[float] = None,
                               new_limit_price: Optional[float] = None) -> Dict:
        """
        Modify an existing stop-limit order
        
        Args:
            symbol (str): Trading pair symbol
            order_id (int): Order ID to modify
            new_stop_price (float, optional): New stop price
            new_limit_price (float, optional): New limit price
            
        Returns:
            Dict: Modified order response
        """
        try:
            self.logger.info(f"Modifying stop-limit order {order_id} for {symbol}")
            
            # Get current order details
            current_order = self.client.futures_get_order(symbol=symbol, orderId=order_id)
            
            # Use current values if not provided
            new_stop = new_stop_price if new_stop_price is not None else float(current_order['stopPrice'])
            new_limit = new_limit_price if new_limit_price is not None else float(current_order['price'])
            
            # Cancel the existing order
            self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
            self.logger.info(f"Cancelled order {order_id}")
            
            # Place new order with modified parameters
            new_order = self.client.futures_create_order(
                symbol=symbol,
                side=current_order['side'],
                type='STOP',
                quantity=current_order['origQty'],
                price=new_limit,
                stopPrice=new_stop,
                timeInForce=current_order['timeInForce'],
                positionSide=current_order['positionSide']
            )
            
            self.logger.info(f"Stop-limit order modified successfully: {new_order['orderId']}")
            return new_order
            
        except Exception as e:
            self.logger.error(f"Error modifying stop-limit order: {e}")
            raise
    
    def cancel_stop_limit_order(self, symbol: str, order_id: int) -> Dict:
        """
        Cancel a stop-limit order
        
        Args:
            symbol (str): Trading pair symbol
            order_id (int): Order ID to cancel
            
        Returns:
            Dict: Cancellation response
        """
        try:
            self.logger.info(f"Cancelling stop-limit order {order_id} for {symbol}")
            
            result = self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
            
            self.logger.info(f"Stop-limit order {order_id} cancelled successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error cancelling stop-limit order: {e}")
            raise
    
    def get_stop_limit_orders(self, symbol: Optional[str] = None) -> list:
        """
        Get all stop-limit orders
        
        Args:
            symbol (str, optional): Filter by symbol
            
        Returns:
            list: List of stop-limit orders
        """
        try:
            if symbol:
                orders = self.client.futures_get_open_orders(symbol=symbol)
            else:
                orders = self.client.futures_get_open_orders()
            
            # Filter for stop-limit orders
            stop_orders = [order for order in orders if order.get('type') == 'STOP']
            
            self.logger.info(f"Retrieved {len(stop_orders)} stop-limit orders")
            return stop_orders
        except Exception as e:
            self.logger.error(f"Error getting stop-limit orders: {e}")
            raise


def main():
    """CLI interface for stop-limit orders"""
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
    logger = logging.getLogger('StopLimitHandler')
    
    parser = argparse.ArgumentParser(description='Binance Futures Stop-Limit Order Bot')
    parser.add_argument('symbol', help='Trading pair symbol (e.g., BTCUSDT)')
    parser.add_argument('side', choices=['BUY', 'SELL'], help='Order side')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('stop_price', type=float, help='Stop price trigger')
    parser.add_argument('limit_price', type=float, help='Limit order price')
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
        
        # Initialize stop-limit handler
        handler = StopLimitHandler(client, logger)
        
        # Place stop-limit order
        order = handler.place_stop_limit_order(
            symbol=args.symbol,
            side=args.side,
            quantity=args.quantity,
            stop_price=args.stop_price,
            limit_price=args.limit_price,
            position_side=args.position_side
        )
        
        print(f"✅ Stop-limit order placed successfully!")
        print(f"Order ID: {order['orderId']}")
        print(f"Status: {order['status']}")
        print(f"Stop Price: ${order['stopPrice']}")
        print(f"Limit Price: ${order['price']}")
        print(f"Quantity: {order['origQty']}")
        
    except Exception as e:
        logger.error(f"Failed to place stop-limit order: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
