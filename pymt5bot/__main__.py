import warnings

import MetaTrader5 as mt5
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import pandas as pd

import json
import os
from datetime import datetime
import time as t
import sys
import signal

import logging
from ta.momentum import RSIIndicator

logging.basicConfig(filename='output.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_config(name):
    config_path = os.path.join(os.path.dirname(__file__), 'configs', name)
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config


config = load_config("config.json")
creds = load_config("login.json")

magic_number = config["magic_number"]
symbol = config["symbol"]
lot = config["lot"]
timeframe = config["timeframe"]
rsi_period = config["rsi_period"]
rsi_overbought = config["rsi_overbought"]
rsi_oversold = config["rsi_oversold"]
rsi_exit_long = config["rsi_exit_long"]
rsi_exit_short = config["rsi_exit_short"]
middle_long = config["middle_long"]
middle_short = config["middle_short"]

sleep_time = config["sleep_time"]
hours_of_operation = config['hours_of_operation']
start_time = hours_of_operation['start']
end_time = hours_of_operation['end']
no_trade_interval = hours_of_operation['no_trade_interval']

logging.info("Symbol: %s", symbol)
logging.info("Lot: %s", lot)
logging.info("Timeframe: %s", timeframe)
logging.info("RSI Period: %s", rsi_period)
logging.info("RSI Overbought: %s", rsi_overbought)
logging.info("RSI Oversold: %s", rsi_oversold)
logging.info("RSI Exit Long: %s", rsi_exit_long)
logging.info("RSI Exit Short: %s", rsi_exit_short)
logging.info("Middle Long: %s", middle_long)
logging.info("Middle Short: %s", middle_short)
logging.info("Sleep Time: %s", sleep_time)
logging.info("Start Time: %s", start_time)
logging.info("End Time: %s", end_time)


def signal_handler(sig, frame):
    logging.info('Deteniendo el bot de trading...')
    mt5.shutdown()
    sys.exit(0)


def get_time():
    current_date_time = datetime.now()
    current_date = current_date_time.strftime("%Y-%m-%d")
    current_time = current_date_time.strftime("%H:%M:%S")
    current_time_and_day = [current_time, current_date]
    return current_time_and_day


from datetime import datetime

def is_time_to_trade(start_time, end_time):
    now = datetime.now().time()
    start_time = datetime.strptime(start_time, "%H:%M").time()
    end_time = datetime.strptime(end_time, "%H:%M").time()
    return start_time <= now <= end_time



def parse_timeframe(t):
    timeframe_mapping = {
        "h1": mt5.TIMEFRAME_H1,
        "d1" : mt5.TIMEFRAME_D1,
        "m1": mt5.TIMEFRAME_M1,
        "m15": mt5.TIMEFRAME_M15,
        "m5": mt5.TIMEFRAME_M5
    }
    lowercase_timeframe = t.lower()
    if lowercase_timeframe in timeframe_mapping:
        return timeframe_mapping[lowercase_timeframe]
    else:
        raise ValueError("Marco de tiempo no válido")


class TradingBot:
    def __init__(self):
        self.crossed_middle_long = False
        self.crossed_middle_short = False
        self.current_position = None
        self.opened_positions = []

    def add_position(self, position_id):
        self.opened_positions.append(position_id)
        self.print_opened_positions()

    def print_opened_positions(self):
        logging.info("Opened Positions:")
        for position in self.opened_positions:
            logging.info(position)
    @staticmethod
    def calculate_RSI(prices, period=14):
        rsi_series = RSIIndicator(prices["close"], window=period, fillna=True).rsi()
        prices["RSI"] = rsi_series
        return prices["RSI"]

    @staticmethod
    def open_trade(action, symbol, lot):
        if action == "buy":
            trade_type = mt5.ORDER_TYPE_BUY
        elif action == "sell":
            trade_type = mt5.ORDER_TYPE_SELL
        else:
            logging.info("Acción de trade no reconocida.")
            return False
        price = mt5.symbol_info_tick(symbol).ask

        # Definición de la solicitud de trade
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": trade_type,
            "deviation": 20,
            "price": price,
            "magic": magic_number,
            "comment": "python script trade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Enviar solicitud de trade
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print("2. order_send failed, retcode={}".format(result.retcode))
            result_dict=result._asdict()
            for field in result_dict.keys():
                print("{}={}".format(field, result_dict[field]))
        return result.order

    @staticmethod
    def get_rates_mt():
        rates = mt5.copy_rates_from_pos(symbol, parse_timeframe(timeframe), 0, rsi_period + 100)
        if rates is None:
            raise Exception("copy_rates_from_pos() failed, error code =", mt5.last_error())
        df = pd.DataFrame(rates)
        df['close'] = df['close'].astype(float)
        return df

    @staticmethod
    def close_trade(action, symbol, lot, position_id):
        t.sleep(1)
        if action == 'buy':
            trade_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask
        elif action == 'sell':
            trade_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid

        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": trade_type,
            "position": position_id,
            "price": price,
            "deviation": 20,
            "stoplimit": 0.0,
            "sl": 0.0,
            "tp": 0.0,
            "magic": magic_number,
            "comment": "python script close",
            "type_time": mt5.ORDER_TIME_GTC,  # Good till cancelled
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Enviar la solicitud de cierre
        result = mt5.order_send(close_request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logging.info("2. order_send failed, retcode={}".format(result.retcode))
            result_dict=result._asdict()
            for field in result_dict.keys():
                logging.info("{}={}".format(field, result_dict[field]))
        return result

    def start_trading(self, max_iterations=None):
        it_count = 0
        while True:
            if is_time_to_trade(start_time, end_time):
                df = self.get_rates_mt()
                rsi = self.calculate_RSI(df).iloc[-1]
                logging.info(f"RSI Actual: {rsi}. Hora: {get_time()}")

                if self.current_position is None:
                    if rsi < rsi_oversold:
                        logging.info("Condiciones de sobreventa, abriendo trade en largo (compra).")
                        position_id = self.open_trade("buy", symbol, lot)
                        self.current_position = "long"
                        logging.info(f"Posición abierta con position_id {position_id}")
                        self.add_position(position_id)

                    elif rsi > rsi_overbought:
                        logging.info("Condiciones de sobrecompra, abriendo trade en corto (venta).")
                        position_id = self.open_trade("sell", symbol, lot)
                        self.current_position = "short"
                        logging.info(f"Posición abierta con position_id {position_id}")
                        self.add_position(position_id)

                elif self.current_position == "long":
                    if rsi < rsi_oversold and self.crossed_middle_long:
                        logging.info("Condiciones de sobreventa, abriendo otro trade en largo (compra).")
                        position_id = self.open_trade("buy", symbol, lot)
                        logging.info(f"Posición abierta con id {position_id}")
                        self.add_position(position_id)
                        self.crossed_middle_long = False
                    elif middle_long < rsi < rsi_exit_long:
                        self.crossed_middle_long = True
                        logging.info(f"RSI ha cruzado el punto intermedio desde abajo hacia arriba")
                    elif rsi > rsi_exit_long:
                        for position_id in self.opened_positions[:]:
                            logging.info(f"Salir de posicion en largo con id {position_id}")
                            self.close_trade("sell", symbol, lot, position_id)
                            self.opened_positions.remove(position_id)
                        self.current_position = None
                        self.crossed_middle_long = False
                elif self.current_position == "short":
                    if rsi > rsi_overbought and self.crossed_middle_short:
                        logging.info("Condiciones de sobrecompra, abriendo otro trade en corto (venta).")
                        position_id = self.open_trade("sell", symbol, lot)
                        logging.info(f"Posicion abierta con id {position_id}")
                        self.add_position(position_id)
                        self.crossed_middle_short = False
                    elif middle_short > rsi > rsi_exit_short:
                        self.crossed_middle_short = True
                        logging.info(f"RSI ha cruzado el punto intermedio desde arriba hacia abajo")
                    elif rsi < rsi_exit_short:
                        for position_id in self.opened_positions[:]:
                            logging.info(f"Salir de posicion en corto con id {position_id}")
                            self.close_trade("buy", symbol, lot, position_id)
                            self.opened_positions.remove(position_id)
                        self.current_position = None
                        self.crossed_middle_short = False

                it_count += 1
                if max_iterations is not None and it_count >= max_iterations:
                    break
                t.sleep(sleep_time)
            else:
                t.sleep(no_trade_interval)


if __name__ == '__main__':

    if not mt5.initialize():
        logging.info("initialize() failed, error code =", mt5.last_error())
        quit()

    if not mt5.login(creds["login"], password=creds["password"], server=creds["server"]):
        logging.info("Login error, error code =", mt5.last_error())
        quit()
    print("Se está ejecutando el bot, puedes consultar los logs en output.log")
    print("Para terminar el programa, presione Ctrl+C")
    TradingBot().start_trading()
