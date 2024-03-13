import unittest
from unittest.mock import patch, call

import pandas as pd

from pymt5bot.__main__ import TradingBot, is_time_to_trade


class TestTradingBot(unittest.TestCase):

    # Decoradores para hacer mock de mt5.copy_rates_from_pos y trading_bot.calculate_RSI
    @patch('pymt5bot.__main__.TradingBot.calculate_RSI')
    @patch('pymt5bot.__main__.TradingBot.get_rates_mt')
    @patch('pymt5bot.__main__.TradingBot.open_trade')
    @patch('pymt5bot.__main__.config')
    @patch('pymt5bot.__main__.is_time_to_trade')
    def test_buy_condition(self, mock_config, mock_open_trade, mock_copy_rates, mock_calculate_RSI):
        # Configuramos el mock
        data = {'close': [1.08, 1.085]}
        df = pd.DataFrame(data)
        mock_calculate_RSI.return_value = pd.Series([0, 19])  # RSI = 19
        mock_copy_rates.return_value = df
        mock_time_to_trade.return_value = True

        mock_config.return_value = {'magic_number': 0,
                                    'symbol': 'EURUSD',
                                    'lot': 0.01,
                                    'timeframe': 'M5',
                                    'rsi_period': 14,
                                    'rsi_overbought': 80,
                                    'rsi_oversold': 20,
                                    'rsi_exit_long': 60,
                                    'rsi_exit_short': 40,
                                    'middle_long': 30,
                                    'middle_short': 70,
                                    'sleep_time': 300,
                                    'hours_of_operation': {'start': '00:00', 'end': '23:00', 'no_trade_interval': 3600}}

        TradingBot().start_trading(max_iterations=1)

        mock_open_trade.assert_called_once_with("buy", "EURUSD", 0.01)

    @patch('pymt5bot.__main__.TradingBot.get_rates_mt')
    @patch('pymt5bot.__main__.TradingBot.open_trade')
    @patch('pymt5bot.__main__.TradingBot.close_trade')
    @patch('pymt5bot.__main__.is_time_to_trade')
    @patch('pymt5bot.__main__.sleep_time', new=0)
    @patch('pymt5bot.__main__.rsi_overbought', new=70)
    @patch('pymt5bot.__main__.middle_short', new=65)
    @patch('pymt5bot.__main__.rsi_exit_short', new=50)
    def test_two_buy_conditions(self, mock_time_to_trade, mock_close_trade, mock_open_trade, mock_copy_rates):
        # Configuramos los mocks
        data = {'close': [1.08, 1.085, 1.09]}
        df = pd.DataFrame(data)
        mock_copy_rates.return_value = df
        mock_time_to_trade.return_value = True

        def calculate_RSI_side_effect(*args, **kwargs):
            call_count = mock_copy_rates.call_count

            # Valor de RSI diferente para cada iteración
            if call_count == 1:
                return pd.Series([0, 71])
            elif call_count == 2:
                return pd.Series([0, 66])
            elif call_count == 3:
                return pd.Series([0, 71])
            elif call_count == 4:
                return pd.Series([0, 64])
            elif call_count == 5:
                return pd.Series([0, 71])
            elif call_count == 6:
                return pd.Series([0, 72])
            else:
                return pd.Series([50, 49])

        with patch('pymt5bot.__main__.TradingBot.calculate_RSI', side_effect=calculate_RSI_side_effect):
            TradingBot().start_trading(max_iterations=7)

        mock_close_trade.assert_has_calls([call("buy", "EURUSD", 0.01, mock_open_trade())])

    def test_is_time_to_trade(self):
        res = is_time_to_trade('23:30', '23:59')
        assert res is False
