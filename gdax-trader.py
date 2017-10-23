#!/usr/bin/env python

import argparse
import json
import os
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

market_fees = 0.25          # coinbase per-transaction fee in dollars
min_profit_margin = 2.00    # minimum price increase before we sell

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

def buy_order(price, size, buy_type='limit', product_id='BTC-USD'):
    ''' Buys product, defaults to limit order of BTC'''
    order_result = client.buy(type=buy_type,
               price=price, # USD
               size=size,   # BTC
               product_id='BTC-USD')
    logging.info(order_result)
    if 'id' in order_result:
        return order_result['id']

def sell_order(price, size, sell_type='limit', product_id='BTC-USD'):
    ''' Buys product, defaults to limit order of BTC'''
    order_result = client.sell(type=sell_type,
               price=price, # USD
               size=size,   # BTC
               product_id='BTC-USD')
    logging.info(order_result)
    return order_result['id']

def min_profit_buy(size):
    ticker = client.get_product_ticker(product_id='BTC-USD')
    ask = ticker['ask']
    min_ask = float(ask) * .98
    order_result = buy_order(round(min_ask, 2), size)
    logging.info(order_result)

logging.info('USD Balance: {0}'.format(get_balance(accounts, 'USD')))
logging.info('BTC Balance: {0}'.format(get_balance(accounts, 'BTC')))


if __name__ == "__main__":
    mongo_client = MongoClient('mongodb://localhost:27017/')
    db = mongo_client.cryptocurrency_database
    BTC_collection = db.BTC_collection

    class MyWebsocketClient(gdax.WebsocketClient):

        def __init__(self):
            super(MyWebsocketClient, self ).__init__()
            self.url = "wss://ws-feed.gdax.com"
            self.message_type = "subscribe"
            self.channels = ['ticker']
            self.products = ["BTC-USD"]
            self.mongo_collection = BTC_collection
            self.should_print = True

        def on_message(self, msg):
            if 'price' in json.dumps(msg, indent=4, sort_keys=True):
                price = msg['price']
                print round(float(price), 2)

        def on_close(self):
            print("-- Goodbye! --")

    wsClient = MyWebsocketClient()
    wsClient.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        wsClient.close()

    if wsClient.error:
        sys.exit(1)
    else:
        sys.exit(0)
