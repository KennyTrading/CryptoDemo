import time 
from enum import Enum 
from typing import DefaultDict, Deque, List, Dict, Tuple, Optional 
from sortedcontainers import SortedList
from  collections import deque, defaultdict 
from decimal import Decimal  
from matplotlib import pyplot as plt 

"""
Price/Time Priority matching algorithm. Orders are first filled based on the price, then based on the arrival time.  FIFO.  
Market Buy/Sell orders are special cases for limit orders. Market Buy has a price of infinity, while Market Sell has a price of 0.    

"""
class Side(Enum): 
    BUY = 0
    SELL = 1 

class Order:
    """
    Order Object
    """

    # order_id: client_id (the guy who place it)
    def __init__(self, order_id, order_type, instmt, price, qty, side):
        self.order_id = order_id 
        self.order_type = order_type 
        self.instmt = instmt 
        self.price = price 
        self.qty = qty 
        self.side = side  

    def __str__(self):
        return "{0},{1},{2},{3},{4},{5}".format(self.order_id, self.order_type, self.instmt, self.price, self.qty, self.side)
    
    def __repr__(self):
        return self.__str__()

class Trade: 
    def __init__(self, trade_id, taker_id, maker_id, instmt, trade_price, trade_qty, trade_side):
        self.trade_id = trade_id
        self.taker_id = taker_id 
        self.maker_id = maker_id 
        self.instmt = instmt 
        self.trade_price = trade_price 
        self.trade_qty = trade_qty 
        self.trade_side = trade_side # trade_side is the same as the taker side 

    def __str__(self):
        return  "{0},{1},{2},{3},{4}".format(self.trade_id, self.instmt, self.trade_price, self.trade_qty, self.trade_side) 

    def __repr__(self):
        return self.__str__()

class OrderBook: 
    """
    An OrderBook has data members of sorted lists Asks and Bids.  
    Ask is a sorted Ascending list by price. The first order in the Ask has the lowest price (best ask)
    Bid is a sorted Descending list by price. The first order in the Bid has the highest price (best bid)  
    Price/Time priority. When we use a queue structure, the new order with the same price will always behind the old order.
    method: 
        Add orders to the orderbook
        Cancel orders from the orderbook


    bids: SortedList[Order]
    asks: SortedList[Order]
    orders: Dict[OrderId, Order]
    trades: Dict[TradeId, Trade]
    """


    def __init__(self, instmt = "", bids = [], asks = []):
        self._order_id = 0
        self._trade_id = 0
        self.bids = SortedList(bids, key = lambda order: -order.price) # Descending, the front element is the best bid (highest price)
        self.asks = SortedList(asks, key = lambda order: order.price)  # Ascending, the front element is the best ask (lowest price)
        self.trades: Deque = deque([], maxlen=10000)
        self.depth = {}
        self.instmt = instmt 
    
    def Add(self, order): # Add an order to the orderbook. First try match it, if can be filled, return the trades and add the remaining portion to the orderbook.   
        if order.side == Side.BUY:
            temp_trades = [] # incremental trades 
            while self.asks: 
                ask = self.asks[0]

                if ask.price > order.price: 
                    break 

                # fully fill 
                if ask.qty > order.qty: 
                    self._trade_id += 1
                    new_trade = Trade(self._trade_id, order.order_id, ask.order_id, order.instmt, ask.price, order.qty, order.side)
                    self.trades.append(new_trade)
                    temp_trades.append(new_trade)

                    ask.qty -= order.qty 
                    order.qty = 0
                    break 
                # clear the level 1 ask, partial fill the order 
                elif ask.qty < order.qty: 
                    self._trade_id += 1

                    new_trade = Trade(self._trade_id, order.order_id, ask.order_id, ask.instmt, ask.price, ask.qty, order.side)
                    self.trades.append(new_trade)
                    temp_trades.append(new_trade)
                    order.qty -= ask.qty 
                    self.asks.remove(ask)

                # ask.qty == order.qty 
                else:
                    self._trade_id += 1
                    new_trade = Trade(self._trade_id, order.order_id, ask.order_id, ask.instmt, ask.price, ask.qty, order.side)
                    self.trades.append(new_trade)
                    temp_trades.append(new_trade)
                    self.asks.remove(ask)
                    order.qty = 0
                    break
                
            if order.qty > 0:
                self.bids.add(order)
            
            return temp_trades

        elif order.side == Side.SELL:
            temp_trades = []
            while self.bids: 
                bid = self.bids[0]
                if bid.price < order.price: 
                    break 
                # Fully Fill 
                if bid.qty > order.qty: 
                    self._trade_id += 1
                    new_trade = Trade(self._trade_id, order.order_id, bid.order_id, order.instmt, bid.price, order.qty, order.side)
                    self.trades.append(new_trade)
                    temp_trades.append(new_trade)

                    bid.qty -= order.qty 
                    order.qty = 0 
                    break 

                elif bid.qty < order.qty: 
                    self._trade_id += 1
                    new_trade = Trade(self._trade_id, order.order_id, bid.order_id, order.instmt, bid.price, bid.qty, order.side)
                    self.trades.append(new_trade)                    
                    temp_trades.append(new_trade)
                    order.qty -= bid.qty 
                    self.bids.remove(bid)

                else:

                    self._trade_id += 1
                    new_trade = Trade(self._trade_id, order.order_id, bid.order_id, order.instmt, bid.price, bid.qty, order.side)
                    self.trades.append(new_trade)    
                    temp_trades.append(new_trade)
                    self.bids.remove(bid)
                    order.qty = 0 
                    break

            if order.qty > 0:
                self.asks.add(order)
            return temp_trades  
        else: 
            raise ValueError("Invalid Order Side")  

    def Cancel(self, order):
        if order.side == Side.BUY:
            self.bids.remove(order)
        elif order.side == Side.SELL:
            self.asks.remove(order)

    def Update(self, order):
        SIDE = order.side
        for existing_order in self.bids + self.asks:
            if order.price == existing_order.price and order.order_id == existing_order.order_id:
                if order.qty > 0: 
                    existing_order.qty = order.qty   
                else:
                    if SIDE:
                        self.bids.remove(existing_order)
                    else: 
                        self.asks.remove(existing_order)

    def show_orderbook(self):
        
        print('----OrderBook----')
        print('Ticker: ',self.instmt)
        print('-----------------')
        print('Ask--------------')
        for a in self.asks[::-1]:
            print("{0}, {1}".format(a.price, a.qty))
        
        print('Ask--------------')
        print('Bid--------------')

        for b in self.bids:
            print("{0}, {1}".format(b.price, b.qty))
        print('Bid--------------')
        print('-----------------')
        print('\n')

if __name__ == '__main__':
    ask_order1 = Order(5, "Limit","AAPL",205.0,10,Side.SELL)
    ask_order2 = Order(6, "Limit","AAPL",206.0,10,Side.SELL)
    ask_order3 = Order(7, "Limit","AAPL",205.0,5,Side.SELL)
    ask_order4 = Order(8, "Limit","AAPL",210.0,7,Side.SELL)

    bid_order1 = Order(1,"Limit","AAPL",200.0,10,Side.BUY)
    bid_order2 = Order(2, "Limit","AAPL",201.0,10,Side.BUY)
    bid_order3 = Order(3, "Limit","AAPL",201.0,5,Side.BUY)
    bid_order4 = Order(4, "Limit","AAPL",201.0,7,Side.BUY)




    bids = [bid_order1, bid_order2, bid_order3, bid_order4]
    asks = [ask_order1, ask_order2, ask_order3, ask_order4]

    ob = OrderBook('AAPL',bids,asks)
    print('Before:')
    ob.show_orderbook()
    
    trades = (ob.Add(Order(9, "Limit", "AAPL", 206, 25, Side.BUY)))

    print("Trades:")
    for t in trades:
        print(t)
    print('\n')

    ob.show_orderbook()
    order_update = Order(5, "Limit", "AAPL", 205, 100, Side.SELL)
    ob.Update(order_update)
    ob.show_orderbook()


