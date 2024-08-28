import os
import time

import pandas as pd
import yaml

import ema_cross_strategy
import mt5_lib


# Function to import settings from settings.json
def get_project_settings(settings_filepath):
    """
    Function to import settings from settings.json
    :param settings_filepath: path to settings.json
    :return: settings as a dictionary object
    """
    # Test the filepath to make sure it exists
    if os.path.exists(settings_filepath):
        with open(settings_filepath, mode='r') as settings_file:

            # Read the information
            project_settings = yaml.safe_load(settings_file)
            # Return the project settings
        return project_settings
    # Notify user if settings.json doesn't exist
    else:
        raise ImportError(f"{settings_filepath} does not exist at provided location")


# Function to start up MT5
def startup(project_settings):
    """
    Function to run through the process of starting up MT5 and initializing symbols
    :param project_settings: json object of project settings
    :return: Boolean. True. Startup successful. False. Error in starting up.
    """
    pd.set_option('display.max_columns', None)
    start_up = mt5_lib.start_mt5(project_settings=project_settings)
    if start_up:
        print("MT5 startup successful")

        init_symbols = mt5_lib.enable_all_symbols(symbol_array=project_settings["mt5"]["symbols"])
        if init_symbols:
            return True
        else:
            print(f"Error initializing symbols")
            return False

        return True
    else:
        print(f"Error starting MT5")
        return False


EMA_0_PERIOD = 2
EMA_1_PERIOD = 5
EMA_2_PERIOD = 10
NUMBER_OF_CANDLES = 1000
SETTINGS_FILEPATH = "settings.yaml"
OUTPUT_FOLDER = "data"
BALANCE = 100_000
AMOUNT_TO_RISK = 0.01


# Function to run the strategy
def run_strategy(project_settings, comment):
    """
    Function to run the strategy for the trading bot
    :param project_settings: JSON of project settings
    :return: Boolean. Strategy ran successfully with no errors=True. Else False.
    """
    # Extract the symbols to be traded
    symbols = project_settings["mt5"]["symbols"]
    # Extract the timeframe to be traded
    timeframe = project_settings["mt5"]["timeframe"]
    # Strategy Risk Management
    # Get a list of open orders
    # orders = mt5_lib.get_all_open_orders()
    # # Iterate through the open orders and cancel
    # for order in orders:
    #     mt5_lib.cancel_order(order)
    # Run through the strategy of the specified symbols
    for symbol in symbols:
        # Strategy Risk Management
        # Cancel any open orders related to the symbol and strategy
        mt5_lib.cancel_filtered_orders(
            symbol=symbol,
            comment=comment
        )
        data = ema_cross_strategy.ema_cross_strategy(symbol=symbol, timeframe=timeframe,
                                                     number_of_candles=NUMBER_OF_CANDLES, ema_one=EMA_1_PERIOD,
                                                     ema_two=EMA_2_PERIOD,
                                                     balance=BALANCE,
                                                     amount_to_risk=AMOUNT_TO_RISK,
                                                     comment=comment)
        if data:
            print(f"\nTrade Made on {symbol}")
        else:
            print(".", end="")
        #     # print(f"No trade for {symbol}")
    # Return True. Previous code will throw a breaking error if anything goes wrong.
    return True


# Main function
if __name__ == '__main__':
    project_settings = get_project_settings(settings_filepath=SETTINGS_FILEPATH)
    symbols = project_settings["mt5"]["symbols"]
    if not symbols:
        print("No symbols found")
        print("Bye")
        exit(1)
    started = startup(project_settings=project_settings)
    if not started:
        print("Bye")
        exit(1)
    print("-" * 100)
    print()
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"Symbols being traded")
    for tick_symbol in symbols:
        print(f"\t{tick_symbol}")
    print("-" * 100)
    print()
    current_time = 0
    previous_time = 0
    timeframe = project_settings["mt5"]["timeframe"]
    comment = f"EMA{EMA_1_PERIOD}-EMA{EMA_2_PERIOD} CROSS STRATEGY"
    tick_symbol = symbols[0]
    while True:
        time_candle = mt5_lib.get_candlesticks(tick_symbol, timeframe=timeframe, number_of_candles=1)
        if time_candle.empty:
            print(f"No candles could be retrieved for {tick_symbol}- probably all exchanges are closed")
            time.sleep(10)
            continue
        current_time = time_candle['time'].values
        tick_title = f"{tick_symbol}@{time_candle['close'].values[0]:.5f}"
        if current_time == previous_time:
            print(".", end="")
            time.sleep(1)
            continue
        print(f"\n{current_time}: **New candle** {tick_title} ", end="")
        previous_time = current_time
        run_strategy(project_settings=project_settings, comment=comment)
