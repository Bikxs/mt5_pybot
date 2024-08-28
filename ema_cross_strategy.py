import os.path
import warnings

import indicator_lib
import mt5_lib
from make_trade import make_trade

warnings.simplefilter(action='ignore', category=FutureWarning)


# Main EMA Cross Strategy Function
def ema_cross_strategy(symbol, timeframe, number_of_candles, ema_one, ema_two, balance, amount_to_risk, comment):
    """
    Main EMA Cross Strategy Function
    :param symbol:
    :param timeframe:
    :param ema_one:
    :param ema_two:
    :return:
    """
    # Retreive data -> get_data()
    # Calculate indicators -> calc_indicators()
    # Determine trades -> det_trade()
    # Make trade -> make_trade()

    if ema_one == ema_two:
        print("We cannot have EMA_ONE equal to EMA_TWO")
        return None

    # Step 1: Retrieve data
    data = get_data(
        symbol=symbol,
        timeframe=timeframe,
        number_of_candles=number_of_candles
    )
    # Step 2: Pass data to calculate indicators
    data = calc_indicators(
        dataframe=data,
        ema_one=ema_one,
        ema_two=ema_two
    )
    # Step 3: Calculate trade events
    data = det_trade(
        dataframe=data,
        ema_one=ema_one,
        ema_two=ema_two
    )
    # Step 4: check the last line of data frame
    trade_event = data.tail(1).copy().to_dict('records')[0]
    take_profit = trade_event['take_profit']
    stop_loss = trade_event['stop_loss']
    stop_price = trade_event['stop_price']
    trade_outcome = False
    if trade_event['ema_cross']:
        print()
        print(data.tail(3))
        data.to_csv(os.path.join("data", f'{symbol}-{comment}.csv'))
        if take_profit > 0 and stop_loss > 0 and stop_price > 0:
            print(f"{comment}: Signal found :-)")
            trade_outcome = make_trade(
                balance=balance,
                comment=comment,
                amount_to_risk=amount_to_risk,
                symbol=symbol,
                take_profit=take_profit,
                stop_loss=stop_loss,
                stop_price=stop_price,
            )

    return trade_outcome


# Function to retrieve data for strategy
def get_data(symbol, timeframe, number_of_candles):
    """
    Function to retrieve data from MT5. Data is in the form of candlesticks and should be returned as a
    dataframe
    :param symbol: string of the symbol to be retrieved
    :param timeframe: string of the timeframe to be queried
    :return: dataframe
    """
    # Note, this function can be expanded to retrieve data from other exchanges also.
    data = mt5_lib.get_candlesticks(symbol=symbol, timeframe=timeframe, number_of_candles=number_of_candles)
    # No further computation for this function
    # Return dataframe
    return data


# Function to calculate indicators
def calc_indicators(dataframe, ema_one, ema_two):
    """
    Function to calculate the indicators for a strategy
    :param dataframe: dataframe of the raw data
    :param ema_one: integer for the first ema
    :param ema_two: integer for the second ema
    :return: dataframe with updated columns
    """
    # Pass the dataframe to calculate ema_one
    data = indicator_lib.calc_ema(
        dataframe=dataframe,
        ema_size=ema_one
    )
    # Pass the dataframe to calculate ema_two
    data = indicator_lib.calc_ema(
        dataframe=dataframe,
        ema_size=ema_two
    )
    # Pass the dataframe with both EMA's to the ema_cross calculator
    data = indicator_lib.calc_ema_cross(
        dataframe=data,
        ema_one=ema_one,
        ema_two=ema_two
    )
    # Return the dataframe with all indicators
    return data


# Function to calculate trade values
def det_trade(dataframe, ema_one, ema_two):
    """
    Function to calculate the trade values for the strategy. For the EMA Cross strategy, rules are as follows:
    1. For each trade, stop_loss is the corresponding highest EMA (i.e. if ema_one is 50 and ema_two is 200, stop_loss
    is ema_200)
    2. For a BUY (GREEN Candle), the entry price (stop_price) is the high of the previous completed candle
    3. For a SELL (RED Candle), the entry price (stop_price) is the low of the previous completed candle
    4. The take_profit is the absolute distance between the stop_price and stop_loss, added to a BUY stop_price and
    subtracted from a SELL stop_price
    :param dataframe: dataframe of data with indicators
    :param ema_one: integer of EMA size
    :param ema_two: integer of EMA size
    :return: dataframe with trade values added
    """
    # Get the EMA column names
    ema_one_column = "ema_" + str(ema_one)
    ema_two_column = "ema_" + str(ema_two)
    # Choose largest EMA to work with
    if ema_one > ema_two:
        ema_column = ema_one_column
        min_value = ema_one
    elif ema_two > ema_one:
        ema_column = ema_two_column
        min_value = ema_two
    else:
        raise ValueError("EMA values are the same!")

    # Add take_profit, stop_loss, stop_price columns to dataframe
    dataframe['take_profit'] = 0.00
    dataframe['stop_price'] = 0.00
    dataframe['stop_loss'] = 0.00

    # Copy the dataframe to reduce warnings
    dataframe_copy = dataframe.copy()

    # Iterate through the copied dataframe and calculate trade values when EMA Cross occurs
    for i in range(len(dataframe_copy)):
        # Skip rows until past EMA calculations
        if i <= min_value:
            continue
        else:
            # Find when an EMA cross is True
            if dataframe_copy.loc[i, 'ema_cross']:
                # Determine if a GREEN candle
                if dataframe_copy.loc[i-1, 'open'] < dataframe_copy.loc[i-1, 'close']:
                    # If GREEN, calculate trade values
                    # stop_loss = column of largest EMA
                    stop_loss = dataframe_copy.loc[i-1, ema_column]
                    # stop_price (Entry Price) = high of most recent complete candle
                    stop_price = dataframe_copy.loc[i-1, 'high']
                    # take_profit = distance between stop_price and stop_loss added to stop_price
                    distance = stop_price - stop_loss
                    take_profit = stop_price + distance
                # If the row is not GREEN then it is RED
                else:
                    # If RED, calculate trade values
                    # stop_loss = column of largest EMA
                    stop_loss = dataframe_copy.loc[i-1, ema_column]
                    # stop_price (Entry Price) = low of most recent complete candle
                    stop_price = dataframe_copy.loc[i-1, 'low']
                    # take_profit = distance between stop_loss and stop_price, subtracted from stop_price
                    distance = stop_loss - stop_price
                    take_profit = stop_price - distance
                # Add the calculated values back to the dataframe
                dataframe_copy.loc[i, 'stop_loss'] = stop_loss
                dataframe_copy.loc[i, 'stop_price'] = stop_price
                dataframe_copy.loc[i, 'take_profit'] = take_profit
    # Return the completed dataframe
    return dataframe_copy
