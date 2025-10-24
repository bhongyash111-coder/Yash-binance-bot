"""
OCO (One-Cancels-Other) Orders Module for Binance Futures Trading Bot
Handles OCO orders that combine limit and stop orders
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException


class OCOOrderHandler:
    """
    Handles OCO (One-Cancels-Other) order operations for Binance Futures
    """
    
    def __init__(self, client: Client, logger: logging.Logger):
        self.client = client
        self.logger = logger
    
    def place_oco_order(self, symbol: str, side: str, quantity: float, 
                       limit_price: float, stop_price: float, stop_limit_price: float,
                       position_side: str = "BOTH") -> Dict:
        """
        Place an OCO order (One-Cancels-Other)
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTCUSDT')
            side (str): 'BUY' or 'SELL'
            quantity (float): Order quantity
            limit_price (float): Limit order price
            stop_price (float): Stop price trigger
            stop_limit_price (float): Stop limit order price
            position_side (str): Position side ('LONG', 'SHORT', or 'BOTH')
            
        Returns:
            Dict: OCO order response from Binance API
        """
        try:
            self.logger.info(f"Placing OCO {side} order for {quantity} {symbol}")
            self.logger.info(f"Limit price: {limit_price}, Stop price: {stop_price}, Stop limit: {stop_limit_price}")
            self.logger.info(f"Position side: {position_side}")
            
            # Validate inputs
            if side not in ['BUY', 'SELL']:
                raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")
            
            if quantity <= 0:
                raise ValueError(f"Invalid quantity: {quantity}. Must be positive")
            
            if limit_price <= 0 or stop_price <= 0 or stop_limit_price <= 0:
                raise ValueError("All prices must be positive")
            
            # Validate price relationships based on side
            if side == 'BUY':
                if stop_price >= limit_price:
                    raise ValueError("For BUY orders: stop_price should be < limit_price")
                if stop_limit_price >= stop_price:
                    raise ValueError("For BUY orders: stop_limit_price should be < stop_price")
            else:  # SELL
                if stop_price <= limit_price:
                    raise ValueError("For SELL orders: stop_price should be > limit_price")
                if stop_limit_price <= stop_price:
                    raise ValueError("For SELL orders: stop_limit_price should be > stop_price")
            
            # Place the OCO order
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='OCO',
                quantity=quantity,
                price=limit_price,
                stopPrice=stop_price,
                stopLimitPrice=stop_limit_price,
                positionSide=position_side
            )
            
            # Log successful order placement
            self.logger.info(f"OCO order placed successfully: {order['orderId']}")
            self.logger.info(f"Order status: {order['status']}")
            self.logger.info(f"Limit order ID: {order.get('orderListId', 'N/A')}")
            
            # Log full order details
            self.logger.debug(f"Full OCO order response: {json.dumps(order, indent=2)}")
            
            return order
            
        except BinanceAPIException as e:
            error_msg = f"Binance API error placing OCO order: {e}"
            self.logger.error(error_msg)
            raise
        except BinanceOrderException as e:
            error_msg = f"Binance order error placing OCO order: {e}"
            self.logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error placing OCO order: {e}"
            self.logger.error(error_msg)
            raise
    
    def get_oco_order_status(self, symbol: str, order_list_id: int) -> Dict:
        """
        Get status of an OCO order
        
        Args:
            symbol (str): Trading pair symbol
            order_list_id (int): OCO order list ID
            
        Returns:
            Dict: OCO order status information
        """
        try:
            order = self.client.futures_get_order(symbol=symbol, orderId=order_list_id)
            self.logger.info(f"Retrieved OCO order status for {order_list_id}")
            return order
        except Exception as e:
            self.logger.error(f"Error getting OCO order status: {e}")
            raise
    
    def cancel_oco_order(self, symbol: str, order_list_id: int) -> Dict:
        """
        Cancel an OCO order
        
        Args:
            symbol (str): Trading pair symbol
            order_list_id (int): OCO order list ID to cancel
            
        Returns:
            Dict: Cancellation response
        """
        try:
            self.logger.info(f"Cancelling OCO order {order_list_id} for {symbol}")
            
            result = self.client.futures_cancel_order(symbol=symbol, orderId=order_list_id)
            
            self.logger.info(f"OCO order {order_list_id} cancelled successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error cancelling OCO order: {e}")
            raise
    
    def create_take_profit_stop_loss(self, symbol: str, side: str, quantity: float,
                                   current_price: float, take_profit_pct: float = 0.02,
                                   stop_loss_pct: float = 0.01) -> Dict:
        """
        Create a take-profit and stop-loss OCO order based on percentage
        
        Args:
            symbol (str): Trading pair symbol
            side (str): 'BUY' or 'SELL'
            quantity (float): Order quantity
            current_price (float): Current market price
            take_profit_pct (float): Take profit percentage (e.g., 0.02 for 2%)
            stop_loss_pct (float): Stop loss percentage (e.g., 0.01 for 1%)
            
        Returns:
            Dict: OCO order response
        """
        try:
            self.logger.info(f"Creating take-profit/stop-loss OCO order for {symbol}")
            self.logger.info(f"Current price: {current_price}, TP: {take_profit_pct*100}%, SL: {stop_loss_pct*100}%")
            
            if side == 'BUY':
                # For long position: take profit above, stop loss below
                limit_price = current_price * (1 + take_profit_pct)
                stop_price = current_price * (1 - stop_loss_pct)
                stop_limit_price = stop_price * 0.99  # Slightly below stop price
            else:  # SELL
                # For short position: take profit below, stop loss above
                limit_price = current_price * (1 - take_profit_pct)
                stop_price = current_price * (1 + stop_loss_pct)
                stop_limit_price = stop_price * 1.01  # Slightly above stop price
            
            self.logger.info(f"Calculated prices - Limit: {limit_price}, Stop: {stop_price}, Stop Limit: {stop_limit_price}")
            
            return self.place_oco_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                limit_price=limit_price,
                stop_price=stop_price,
                stop_limit_price=stop_limit_price
            )
            
        except Exception as e:
            self.logger.error(f"Error creating take-profit/stop-loss OCO: {e}")
            raise
    
    def get_oco_orders(self, symbol: Optional[str] = None) -> list:
        """
        Get all OCO orders
        
        Args:
            symbol (str, optional): Filter by symbol
            
        Returns:
            list: List of OCO orders
        """
        try:
            if symbol:
                orders = self.client.futures_get_open_orders(symbol=symbol)
            else:
                orders = self.client.futures_get_open_orders()
            
            # Filter for OCO orders
            oco_orders = [order for order in orders if order.get('type') == 'OCO']
            
            self.logger.info(f"Retrieved {len(oco_orders)} OCO orders")
            return oco_orders
        except Exception as e:
            self.logger.error(f"Error getting OCO orders: {e}")
            raise


def main():
    """CLI interface for OCO orders"""
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
    logger = logging.getLogger('OCOOrderHandler')
    
    parser = argparse.ArgumentParser(description='Binance Futures OCO Order Bot')
    parser.add_argument('symbol', help='Trading pair symbol (e.g., BTCUSDT)')
    parser.add_argument('side', choices=['BUY', 'SELL'], help='Order side')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('limit_price', type=float, help='Limit order price')
    parser.add_argument('stop_price', type=float, help='Stop price trigger')
    parser.add_argument('stop_limit_price', type=float, help='Stop limit order price')
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
        
        # Initialize OCO order handler
        handler = OCOOrderHandler(client, logger)
        
        # Place OCO order
        order = handler.place_oco_order(
            symbol=args.symbol,
            side=args.side,
            quantity=args.quantity,
            limit_price=args.limit_price,
            stop_price=args.stop_price,
            stop_limit_price=args.stop_limit_price,
            position_side=args.position_side
        )
        
        print(f"✅ OCO order placed successfully!")
        print(f"Order ID: {order['orderId']}")
        print(f"Status: {order['status']}")
        print(f"Limit Price: ${args.limit_price}")
        print(f"Stop Price: ${args.stop_price}")
        print(f"Stop Limit Price: ${args.stop_limit_price}")
        
    except Exception as e:
        logger.error(f"Failed to place OCO order: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
