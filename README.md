# gdax-trader
Bitcoin trading bot that accepts a minimum profit to trade on, then waits for a price swing of that much to trade a proportal amount of the bankroll that is set. So if you provide $100 bankroll and bitcoin price swings 5%, the bot will trade $5 of your bankroll either buy or sell depending on what the swing was. Trade interval is configurable. This bot is a work in progress and I intended on adding trade signals to it for bitcoin price prediction such as a Bayesian regression.

## Requirements

* [Python](https://www.python.org/) 2.7.x
* [MongoDB](http://www.mongodb.org/) 3.4.9

## Install dependencies
```sh
    $ git clone https://github.com/mjmj/gdax-trader.git
    $ cd gdax-trader
    $ pip install -e .
```
Note: I installed gdax manually since their pip version was old as of 10-22-17.
Visit: https://github.com/danpaquin/gdax-python

## Create an api key at GDAX
https://support.gdax.com/customer/en/portal/articles/2425383-how-can-i-create-an-api-key-for-gdax-

## Set PROD secrets as environment variables

``` export COINBASE_KEY='' && export COINBASE_SECRET='' && COINBASE_PASSPHRASE='' ```

## Set Sandbox secrets as environment variables

```export COINBASE_SANDBOX_KEY='' && export COINBASE_SANDBOX_SECRET='' && COINBASE_SANDBOX_PASSPHRASE=''```

## Start Mongo locally
```sh
  $ brew services start mongodb
```

## Run in Prod (live trades will happen!)
gdax-trader will look for prod environment variables

```python gdax-trader.py https://api.gdax.com```

## Run in GDAX Sandbox
gdax-trader will look for sandbox environment variables

```ipython gdax-trader.py https://api.gdax.com```

## License

This project is licensed under the terms of the MIT license. See [LICENSE](https://github.com/stavros0/bitcoin-price-prediction/blob/master/LICENSE) for more information.
