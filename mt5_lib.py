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


# Function to retrieve the pip_size of a symbol from MT5
def get_pip_size(symbol):
    """
    Function to retrieve the pip size of a symbol from MetaTrader 5
    :param symbol: string of the symbol to be queried
    :return: float of the pip size
    """
    # Get the symbol information
    symbol_info = MetaTrader5.symbol_info(symbol)
    tick_size = symbol_info.trade_tick_size
    pip_size = tick_size * 10
    # Return the pip size
    return pip_size


# Function to retrieve the base currency of a symbol from MT5
def get_base_currency(symbol):
    """
    Function to retrieve the base currency of a symbol from MetaTrader 5
    :param symbol: string of the symbol to be queried
    :return: string of the base currency
    """
    # Get the symbol information
    symbol_info = MetaTrader5.symbol_info(symbol)
    # Return the base currency
    return symbol_info.currency_base


# Function to retrieve the exchange rate of a symbol from MT5
def get_exchange_rate(symbol):
    """
    Function to retrieve the exchange rate of a symbol from MetaTrader 5
    :param symbol: string of the symbol to be queried
    :return: float of the exchange rate
    """
    # Get the symbol information
    symbol_info = MetaTrader5.symbol_info(symbol)
    # Return the exchange rate
    return symbol_info.bid



# Function to place an order on MT5
def place_order(order_type, symbol, volume, stop_loss, take_profit, comment, direct=False, stop_price=0.00):
    """
    Function to place a trade on MetaTrader 5. Function checks the order first, as recommended by most traders. If it
    passes the check, proceeds to place order
    :param order_type: String. Options are SELL_STOP, BUY_STOP
    :param symbol: String of the symbol to be traded
    :param volume: String or Float of the volume to be purchased
    :param stop_loss: String or Float of Stop_Loss price
    :param take_profit: String or Float of Take_Profit price
    :param comment: String of a comment.
    :param direct: Boolean. Defaults to False. When true, bypasses the trade check
    :param stop_price: String or Float of the Stop Price
    :return: Trade Outcome
    """
    # Massage the volume, stop_loss, take_profit and stop_prices
    # Volume can only be up to 2 decimal places on MT5
    volume = float(volume)
    volume = round(volume, 2)
    # Stop Loss should be a float, no more than 4 decimal places
    stop_loss = float(stop_loss)
    stop_loss = round(stop_loss, 4)
    # Take Profit should be a float, no more than 4 decimal places
    take_profit = float(take_profit)
    take_profit = round(take_profit, 4)
    # Stop Price should be a float, no more than 4 decimal places
    stop_price = float(stop_price)
    stop_price = round(stop_price, 4)
    # Set up the order request dictionary. This will be sent to MT5
    request = {
        "symbol": symbol,
        "volume": volume,
        "sl": stop_loss,
        "tp": take_profit,
        "type_time": MetaTrader5.ORDER_TIME_GTC,
        "comment": comment
    }

    # Create the order type based upon provided values.
    if order_type == "SELL_STOP":
        # Update the request dictionary
        request['type'] = MetaTrader5.ORDER_TYPE_SELL_STOP
        request['action'] = MetaTrader5.TRADE_ACTION_PENDING
        request['type_filling'] = MetaTrader5.ORDER_FILLING_RETURN
        # If the stop_price is 0, this is an error
        if stop_price <= 0:
            raise ValueError("Stop Price cannot be zero")
        else:
            request['price'] = stop_price
    # Update in the case of a BUY_STOP
    elif order_type == "BUY_STOP":
        # Update the request dictionary
        request['type'] = MetaTrader5.ORDER_TYPE_BUY_STOP
        request['action'] = MetaTrader5.TRADE_ACTION_PENDING
        request['type_filling'] = MetaTrader5.ORDER_FILLING_RETURN
        # Check the stop price
        if stop_price <= 0:
            raise ValueError("Stop Price cannot be zero")
        else:
            request['price'] = stop_price
    else:
        # This function can be expanded to accept all different types of values for buying/selling
        raise ValueError(f"Incorrect value for Order Type: {order_type}")

    # If direct is True, go straight to adding the order
    if direct is True:
        # Send the order to MT5
        order_result = MetaTrader5.order_send(request)
        # Notify based on the return outcomes
        if order_result[0] == 10009:
            print(f"Order for {symbol} successful")
            return order_result[2]
        # Notify the user if AutoTrading has been left on in MetaTrader 5
        elif order_result[0] == 10027:
            print("Turn off Algo Trading on MT5 Terminal")
            raise Exception("Turn off Algo Trading on MT5 Terminal")
        else:
            # General catch all statement
            print(f"Error placing order. Error Code {order_result[0]}, Error Details: {order_result}")
            raise Exception("An error occurred placing an order")
    # If direct turned off, check the order first
    else:
        # Check the order
        result = MetaTrader5.order_check(request)
        # If check passes, place an order
        if result[0] == 0:
            print(f"Order check for {symbol} successful. Placing the order") #<- This can be commented out.
            # Place the order (little bit of recursion)
            place_order(
                order_type=order_type,
                symbol=symbol,
                volume=volume,
                stop_price=stop_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                comment=comment,
                direct=True
            )
        # Let the user know if an invalid price has been passed
        elif result[0] == 100015:
            print(f"Invalid price passed for {symbol}")
        # Let user know if any other errors occurred
        else:
            print(f"Order check failed. Details: {result}")

# Function to Cancel an order on MT5
def cancel_order(order_number):
    """
    Function to cancel an order identified by an order number
    :param order_number: int representing the order number from MT5
    :return: Boolean. True = cancelled. False == Not Cancelled.
    """
    # Create the request
    request = {
        "action": MetaTrader5.TRADE_ACTION_REMOVE,
        "order": order_number,
        "comment": "order removed"
    }
    # Attempt to send the order to MT5
    try:
        order_result = MetaTrader5.order_send(request)
        if order_result[0] == 10009:
            print(f"Order {order_number} successfully cancelled")
            return True
        # You can put custom error handling if needed
        else:
            print(f"Order {order_number} unable to be cancelled")
            return False
    except Exception as e:
        # This represents an issue with MetaTrader 5 terminal, so stop
        print(f"Error cancelling order {order_number}. Error: {e}")
        raise Exception


# Function to retrieve all currently open orders on MetaTrader 5
def get_all_open_orders():
    """
    Function to retrieve all open orders from MetaTrader 5
    :return: list of open orders
    """
    return MetaTrader5.orders_get()


# Function to retrieve a filtered list of open orders from MT5
def get_filtered_list_of_orders(symbol, comment):
    """
    Function to retrieve a filtered list of open orders from MT5. Filtering is performed
    on symbol and comment
    :param symbol: string of the symbol being traded
    :param comment: string of the comment
    :return: (filtered) list of orders
    """
    # Retrieve a list of open orders, filtered by symbol
    open_orders_by_symbol = MetaTrader5.orders_get(symbol)
    # Check if any orders were retrieved (there may be none)
    if open_orders_by_symbol is None or len(open_orders_by_symbol) == 0:
        return []

    # Convert the retrieved orders into a dataframe
    open_orders_dataframe = pandas.DataFrame(
        list(open_orders_by_symbol),
        columns=open_orders_by_symbol[0]._asdict().keys()
    )
    # From the open orders dataframe, filter orders by comment
    open_orders_dataframe = open_orders_dataframe[open_orders_dataframe['comment'] == comment]
    # Create a list to store the open order numbers
    open_orders = []
    # Iterate through the dataframe and add order numbers to the list
    for order in open_orders_dataframe['ticket']:
        open_orders.append(order)
    # Return the open orders
    return open_orders


# Function to cancel orders based upon filters
def cancel_filtered_orders(symbol, comment):
    """
    Function to cancel a list of filtered orders. Based upon two filters: symbol and comment string.
    :param symbol: string of symbol
    :param comment: string of the comment
    :return: Boolean. True = orders cancelled, False = issue with cancellation
    """
    # Retreive a list of the orders based upon the filter
    orders = get_filtered_list_of_orders(
        symbol=symbol,
        comment=comment
    )
    if len(orders) > 0:
        # Iterate through and cancel
        for order in orders:
            cancel_outcome = cancel_order(order)
            if cancel_outcome is not True:
                return False
        # At conclusion of iteration, return true
        return True
    else:
        return True