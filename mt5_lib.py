import MetaTrader5
import pandas
import datetime
from dateutil.relativedelta import relativedelta


# Function to start MetaTrader 5
def start_mt5(project_settings):
    """
    Function to start MetaTrader 5
    :param project_settings: json object with username, password, server, terminal64.exe location
    :return: Boolean: True = started, False = not started
    """
    # Ensure that all variables are set to the correct type
    username = project_settings['mt5']['username']
    username = int(username)
    password = project_settings['mt5']['password']
    server = project_settings['mt5']['server']
    mt5_pathway = project_settings['mt5']['mt5_pathway']

    # Attempt to initialize MT5
    mt5_init = False
    try:
        mt5_init = MetaTrader5.initialize(
            login=username,
            password=password,
            server=server,
            path=mt5_pathway
        )
    except Exception as e:
        print(f"Error initializing MetaTrader 5: {e}")
        # I cover more advanced error handling in other courses, which are useful for troubleshooting
        mt5_init = False

    # If MT5 initialized, attempt to login to MT5
    mt5_login = False
    if mt5_init:
        try:
            mt5_login = MetaTrader5.login(
                login=username,
                password=password,
                server=server
            )
        except Exception as e:
            print(f"Error logging into MetaTrader 5: {e}")
            mt5_login = False

    # Return the outcome to the user
    if mt5_login:
        return True
    # Default fail condition of not logged in
    return False


# Function to initalize a symbol
def initialize_symbol(symbol, symbol_names):
    """
    MT5 requires symbols to be initialized before they can be queried. This function does that.
    :param symbol: string of symbol (include the symbol name for raw if needed. For instance, IC Markets uses .a to
    indicate raw)
    :return: Boolean. True if initialized, False if not.
    """
    # Check if symbol exists on MT5
    # Get all symbols from MT5

    if symbol in symbol_names:
        try:
            MetaTrader5.symbol_select(symbol, True)  # <- arguments cannot be declared here or will throw an error
            return True
        except Exception as e:
            print(f"Error enabling {symbol}. {e}")
            # Subscribe to channel where I'll go more indepth of error handling.
            return False
    else:
        print(f"Symbol {symbol} does not exist. Please update symbol name.")
        return False


# Function to enable all the symbols in settings.json. This means you can trade more than one currency pair!
def enable_all_symbols(symbol_array):
    """
    Function to enable a list of symbols
    :param symbol_array: list of symbols.
    :return: Boolean. True if enabled, False if not.
    """
    all_symbols = MetaTrader5.symbols_get()
    print(f"Number of symbols supported: {len(all_symbols)}")
    symbol_names = [symbol.name for symbol in all_symbols]

    # Iterate through the list and enable
    for symbol in symbol_array:
        init = initialize_symbol(symbol=symbol, symbol_names=symbol_names)
        if init is False:
            return False

    # Default to return True
    return True


# Function to convert a timeframe string into a MetaTrader 5 friendly format
def set_query_timeframe(timeframe):
    if timeframe == 'M1':
        return MetaTrader5.TIMEFRAME_M1
    elif timeframe == 'M15':
        return MetaTrader5.TIMEFRAME_M15
    elif timeframe == 'H1':
        return MetaTrader5.TIMEFRAME_H1
    elif timeframe == 'H4':
        return MetaTrader5.TIMEFRAME_H4
    elif timeframe == 'daily':
        return MetaTrader5.TIMEFRAME_D1
    elif timeframe == 'weekly':
        return MetaTrader5.TIMEFRAME_W1
    elif timeframe == 'monthly':
        return MetaTrader5.TIMEFRAME_MN1
    else:
        raise ValueError


# Function to query historic candlestick data from MT5
def get_candlesticks(symbol, timeframe, number_of_candles):
    """
    Function to retrieve a user-defined number of candles from MetaTrader 5. Initial upper range set to
    50,000 as more requires changes to MetaTrader 5 defaults.
    :param symbol: string of the symbol being retrieved
    :param timeframe: string of the timeframe being retrieved
    :param number_of_candles: integer of number of candles to retrieve. Limited to 50,000
    :return: dataframe of the candlesticks
    """
    # Check that the number of candles is <= 50,000
    if number_of_candles > 50000:
        raise ValueError("No more than 50000 candles can be retrieved at this time")
    # Convert the timeframe into MT5 friendly format
    mt5_timeframe = set_query_timeframe(timeframe=timeframe)
    # Retrieve the data
    candles = MetaTrader5.copy_rates_from_pos(symbol, mt5_timeframe, 1, number_of_candles)
    # Convert to a dataframe
    dataframe = pandas.DataFrame(candles)
    # Add a 'Human Time' column
    dataframe['human_time'] = pandas.to_datetime(dataframe['time'], unit='s')
    return dataframe
