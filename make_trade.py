import mt5_lib

from helper_functions import calc_lot_size


# Function to make a trade
def make_trade(balance, comment, amount_to_risk, symbol, take_profit, stop_loss, stop_price):
    """
    Function to make a trade once a price signal is retrieved.
    :param balance: float of current balance / or static balance
    :param amount_to_risk: float of the amount to risk (expressed as decimal)
    :param take_profit: float of take_profit price
    :param stop_loss: float of stop_loss price
    :param stop_price: float of stop_price
    :param symbol: string of the symbol being traded
    :return: trade_outcome
    """
    # Format all values
    balance = float(balance)
    balance = round(balance, 2)
    take_profit = float(take_profit)
    take_profit = round(take_profit, 4)
    stop_loss = float(stop_loss)
    stop_loss = round(stop_loss, 4)
    stop_price = float(stop_price)
    stop_price = round(stop_price, 4)

    # Pseudo code
    # 1. Determine lot size
    lot_size = calc_lot_size(
        balance=balance,
        risk_amount=amount_to_risk,
        stop_loss=stop_loss,
        stop_price=stop_price,
        symbol=symbol
    )
    # 2. Send trade to MT5
    # Determine trade type
    if stop_price > stop_loss:
        trade_type = "BUY_STOP"
    else:
        trade_type = "SELL_STOP"
    # Send to MT5
    trade_outcome = mt5_lib.place_order(
        order_type=trade_type,
        symbol=symbol,
        volume=lot_size,
        stop_loss=stop_loss,
        stop_price=stop_price,
        take_profit=take_profit,
        comment=comment,
        direct=False
    )
    # Return the trade outcome to user
    return trade_outcome
