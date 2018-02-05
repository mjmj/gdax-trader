#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import json
import logging
import sys
import time

import gdax

from pymongo import MongoClient


parser = argparse.ArgumentParser()
parser.add_argument("API_URL", default="https://api-public.sandbox.gdax.com",
                               help="Specify https://api.gdax.com OR \
                                 https://api-public.sandbox.gdax.com")
args = parser.parse_args()

root = logging.getLogger()
root.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

APIURL = args.API_URL
STREAM_URL = "wss://ws-feed.gdax.com"

if APIURL == 'https://api.gdax.com':
    KEY = os.environ.get('COINBASE_KEY')
    SECRET = os.environ.get('COINBASE_SECRET')
    PASSPHRASE = os.environ.get('COINBASE_PASSPHRASE')
    logging.info('Using PROD! - Now we\'re trading for real!')
elif APIURL == 'https://api-public.sandbox.gdax.com':
    KEY = os.environ.get('COINBASE_SANDBOX_KEY')
    SECRET = os.environ.get('COINBASE_SANDBOX_SECRET')
    PASSPHRASE = os.environ.get('COINBASE_SANDBOX_PASSPHRASE')
    logging.info('Using the SANDBOX - Nothing you do here matters.')
else:
    # warn if these aren't set and exit out
    logging.info('Please set COINBASE_KEY, COINBASE_SECRET and COINBASE_PASSPHRASE as environment variables')

public_client = gdax.PublicClient()
client = gdax.AuthenticatedClient(KEY, SECRET, PASSPHRASE, api_url=APIURL)
accounts = client.get_accounts()

def get_balance(accounts, currency):
    for k in accounts:
        if k['currency'] == currency:
            return k['balance']

def get_order(order_id):
    client.get_order(order_id)

def get_account(account):
    client.get_account(account)

def cancel_all_orders():
    logging.info("Cancelling all orders")
    products = public_client.get_products()
    for product in products:
        client.cancel_all(product=product['id'])
    logging.info("Orders Canceled")

def buy(price, size, buy_type='limit', product_id='BTC-USD'):
    ''' Buys product, defaults to limit order of BTC'''
    order_result = client.buy(type=buy_type,
               price=price, # USD
               size=size,   # BTC
               product_id='BTC-USD')
    logging.info(order_result)
    if 'id' in order_result:
        return order_result['id']

def sell(price, size, sell_type='limit', product_id='BTC-USD'):
    ''' Buys product, defaults to limit order of BTC'''
    order_result = client.sell(type=sell_type,
               price=price, # USD
               size=size,   # BTC
               product_id='BTC-USD')
    logging.info(order_result)
    if 'id' in order_result:
        return order_result['id']

def min_profit_buy(size):
    ticker = client.get_product_ticker(product_id='BTC-USD')
    ask = ticker['ask']
    min_ask = float(ask) * .98
    order_result = buy(round(min_ask, 2), size)
    logging.info(order_result)

logging.info('USD Balance: {0}'.format(get_balance(accounts, 'USD')))
logging.info('BTC Balance: {0}'.format(get_balance(accounts, 'BTC')))


if __name__ == "__main__":
    mongo_client = MongoClient('mongodb://localhost:27017/')
    db = mongo_client.cryptocurrency_database
    BTC_collection = db.BTC_collection

    market_fee = 0.25         # coinbase per-transaction fee in dollars
    min_profit_margin = .15    # percent change to perform a buy/sell
    bankroll = 500            # USD to begin trade with

    class MyWebsocketClient(gdax.WebsocketClient):

        def __init__(self):
            super(MyWebsocketClient, self ).__init__()
            self.url = STREAM_URL
            self.message_type = "subscribe"
            self.channels = ['ticker']
            self.products = ["BTC-USD"]
            self.mongo_collection = BTC_collection
            self.should_print = True
            self.price = 0
            self.initial_price = 0

        def on_message(self, msg):
            if 'price' in json.dumps(msg, indent=4, sort_keys=True):
                price = msg['price']
                self.price = round(float(price), 2)

        def on_close(self):
            print("-- Goodbye! --")

        def percent_change(self, initial_price, current_price):
            change = (current_price - initial_price) / 100
            print 'Percent Change: {0}'.format(round(change, 2))
            return change

        def price_change(self, initial_price, current_price):
            price_difference = current_price - initial_price
            print 'Price Change: {0}'.format(round(price_difference, 2))
            return price_difference

        def perform_trade(self, trade_direction, percent_change):
            '''
            trade_direction can be buy or sell

            We will trade the same percent of our bankroll
            that the bitcoin price just changed between our waiting
            period.
            '''
            global bankroll
            trade_size = round((bankroll * percent_change) / 100, 2)
            print 'Performing a {0} of ${1}'.format(trade_direction, trade_size)
            if trade_direction == 'buy':
                buy(c.price, trade_size)
            elif trade_direction == 'sell':
                sell(c.price, trade_size)
            bankroll = bankroll - trade_size
            print 'Remainig bankroll of {0}'.format(bankroll)

        def calc_profits():
            ''' function to show number of trades and total profits'''
            pass


    c = MyWebsocketClient()
    c.start()

    try:
        if not c.price:
            time.sleep(5)
            c.initial_price = c.price
            print 'Initial price {0}'.format(c.initial_price)
        while True:
            time.sleep(1)
            ## calculate price change and it's percent of change since initial price
            ## or last trade
            if c.price:
                ### sit at watch the price change
                print 'Latest BTC price: {0}'.format(c.price)
                print 'Initial price {0}'.format(c.initial_price)
                percent_change = c.percent_change(c.initial_price, c.price)
                price_change = c.price_change(c.initial_price, c.price)

                ## Make trades that meet our min profit
                if percent_change >= min_profit_margin + market_fee:
                    c.perform_trade('sell', percent_change)
                elif percent_change <= (min_profit_margin * -1) + market_fee:
                    c.perform_trade('buy', percent_change)
    except KeyboardInterrupt:
        c.close()


    if c.error:
        sys.exit(1)
    else:
        sys.exit(0)
