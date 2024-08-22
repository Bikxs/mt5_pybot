import os

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
            print(f"Error intializing symbols")
            return False

        return True
    else:
        print(f"Error starting MT5")
        return False


EMA_0_PERIOD = 20
EMA_1_PERIOD = 50
EMA_2_PERIOD = 200
NUMBER_OF_CANDLES = 2000
TIMEFRAME = "M1"
SETTINGS_FILEPATH = "settings.yaml"
OUTPUT_FOLDER = "data"

# Main function
if __name__ == '__main__':
    project_settings = get_project_settings(settings_filepath=SETTINGS_FILEPATH)
    started = startup(project_settings=project_settings)
    if not started:
        print("Bye")
        exit(1)
    symbols = project_settings["mt5"]["symbols"]

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    for symbol in symbols:
        print(f"{symbol}")
        df = ema_cross_strategy.ema_cross_strategy(symbol=symbol, timeframe=TIMEFRAME,
                                                   number_of_candles=NUMBER_OF_CANDLES, ema_one=EMA_1_PERIOD,
                                                   ema_two=EMA_2_PERIOD)

        filename = os.path.join(OUTPUT_FOLDER, f"EMA_{EMA_1_PERIOD}_{EMA_2_PERIOD}_CROSS_STRATEGY_{symbol}.csv")
        df.to_csv(filename)
        print(f"Saved {filename}")
