"""
Market Orders Module for Binance Futures Trading Bot
Handles immediate execution orders at current market price
"""

import logging
import json
from datetime import datetime
from typing import Dict, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException


class MarketOrderHandler:
    """
    Handles market order operations for Binance Futures
    """
    
    def __init__(self, client: Client, logger: logging.Logger):
        self.client = client
        self.logger = logger
    
    def place_market_order(self, symbol: str, side: str, quantity: float, 
                          position_side: str = "BOTH") -> Dict:
        """
        Place a market order for immediate execution
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTCUSDT')
            side (str): 'BUY' or 'SELL'
            quantity (float): Order quantity
            position_side (str): Position side ('LONG', 'SHORT', or 'BOTH')
            
        Returns:
            Dict: Order response from Binance API
        """
        try:
            self.logger.info(f"Placing market {side} order for {quantity} {symbol}")
            self.logger.info(f"Position side: {position_side}")
            
            # Validate inputs
            if side not in ['BUY', 'SELL']:
                raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")
            
            if quantity <= 0:
                raise ValueError(f"Invalid quantity: {quantity}. Must be positive")
            
            # Place the market order
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity,
                positionSide=position_side
            )
            
            # Log successful order placement
            self.logger.info(f"Market order placed successfully: {order['orderId']}")
            self.logger.info(f"Order status: {order['status']}")
            self.logger.info(f"Executed quantity: {order['executedQty']}")
            self.logger.info(f"Average price: {order.get('avgPrice', 'N/A')}")
            
            # Log full order details
            self.logger.debug(f"Full order response: {json.dumps(order, indent=2)}")
            
            return order
            
        except BinanceAPIException as e:
            error_msg = f"Binance API error placing market order: {e}"
            self.logger.error(error_msg)
            raise
        except BinanceOrderException as e:
            error_msg = f"Binance order error placing market order: {e}"
            self.logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error placing market order: {e}"
            self.logger.error(error_msg)
            raise
    
    def get_market_price(self, symbol: str) -> float:
        """
        Get current market price for a symbol
        
        Args:
            symbol (str): Trading pair symbol
            
        Returns:
            float: Current market price
        """
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            self.logger.info(f"Current market price for {symbol}: {price}")
            return price
        except Exception as e:
            self.logger.error(f"Failed to get market price for {symbol}: {e}")
            raise
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if symbol exists and is tradeable
        
        Args:
            symbol (str): Trading pair symbol
            
        Returns:
            bool: True if symbol is valid and tradeable
        """
        try:
            exchange_info = self.client.futures_exchange_info()
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol and s['status'] == 'TRADING':
                    self.logger.info(f"Symbol {symbol} is valid and tradeable")
                    return True
            self.logger.warning(f"Symbol {symbol} not found or not tradeable")
            return False
        except Exception as e:
            self.logger.error(f"Error validating symbol {symbol}: {e}")
            return False


def main():
    """CLI interface for market orders"""
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
    logger = logging.getLogger('MarketOrderHandler')
    
    parser = argparse.ArgumentParser(description='Binance Futures Market Order Bot')
    parser.add_argument('symbol', help='Trading pair symbol (e.g., BTCUSDT)')
    parser.add_argument('side', choices=['BUY', 'SELL'], help='Order side')
    parser.add_argument('quantity', type=float, help='Order quantity')
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
        
        # Initialize market order handler
        handler = MarketOrderHandler(client, logger)
        
        # Validate symbol
        if not handler.validate_symbol(args.symbol):
            print(f"Error: Symbol {args.symbol} is not valid or not tradeable")
            sys.exit(1)
        
        # Get current market price
        current_price = handler.get_market_price(args.symbol)
        print(f"Current {args.symbol} price: ${current_price:,.2f}")
        
        # Place market order
        order = handler.place_market_order(
            symbol=args.symbol,
            side=args.side,
            quantity=args.quantity,
            position_side=args.position_side
        )
        
        print(f"✅ Market order placed successfully!")
        print(f"Order ID: {order['orderId']}")
        print(f"Status: {order['status']}")
        print(f"Executed Quantity: {order['executedQty']}")
        print(f"Average Price: ${order.get('avgPrice', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Failed to place market order: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
