from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
from pandas import DataFrame
import talib.abstract as ta
import numpy as np
from freqtrade.persistence import Trade
from datetime import datetime, timedelta

class HybridAdvancedStrategy(IStrategy):
    INTERFACE_VERSION = 3

    # Paramètres optimisés
    minimal_roi = {
        "0": 0.10,    # 10% pour tout trade
        "30": 0.05,   # Après 30 min, réduit à 5%
        "60": 0.02,    # Après 1h, réduit à 2%
    }

    stoploss = -0.08  # Stop-loss un peu moins agressif
    timeframe = '5m'
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Paramètres optimisables
    rsi_buy = IntParameter(25, 40, default=35, space='buy')
    rsi_sell = IntParameter(60, 80, default=70, space='sell')
    ema_fast_period = IntParameter(10, 20, default=12, space='buy')
    ema_slow_period = IntParameter(20, 40, default=26, space='buy')
    macd_fast_period = IntParameter(10, 15, default=12, space='buy')
    macd_slow_period = IntParameter(20, 30, default=26, space='buy')
    macd_signal_period = IntParameter(7, 12, default=9, space='buy')

    # Protection contre les marchés volatils
    use_custom_stoploss = True
    protection_params = {
        "cooldown_lookback": 48,  # 4 heures (48 périodes de 5m)
        "stoploss_lookback": 24,  # 2 heures
        "stoploss_min_pct": -0.04, # Stop dynamique minimum
        "stoploss_max_pct": -0.10 # Stop dynamique maximum
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)

        # EMA
        dataframe['ema_fast'] = ta.EMA(dataframe, timeperiod=self.ema_fast_period.value)
        dataframe['ema_slow'] = ta.EMA(dataframe, timeperiod=self.ema_slow_period.value)

        # MACD avec paramètres optimisables
        macd = ta.MACD(
            dataframe,
            fastperiod=self.macd_fast_period.value,
            slowperiod=self.macd_slow_period.value,
            signalperiod=self.macd_signal_period.value
        )
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']

        # Bollinger Bands comme indicateur supplémentaire
        bollinger = ta.BBANDS(dataframe, timeperiod=20)
        dataframe['bb_lower'] = bollinger['lowerband']
        dataframe['bb_middle'] = bollinger['middleband']
        dataframe['bb_upper'] = bollinger['upperband']
        dataframe['bb_percent'] = (dataframe['close'] - dataframe['bb_lower']) / (
            dataframe['bb_upper'] - dataframe['bb_lower'])

        # Volume moyen comme filtre supplémentaire
        dataframe['volume_mean'] = dataframe['volume'].rolling(window=30).mean()

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        
        # Condition principale: RSI bas + croisement EMA + MACD positif
        conditions.append(
            (dataframe['rsi'] < self.rsi_buy.value) &
            (dataframe['ema_fast'] > dataframe['ema_slow']) &
            (dataframe['macd'] > dataframe['macdsignal']) &
            (dataframe['macd'] > 0) &
            (dataframe['volume'] > dataframe['volume_mean'] * 0.8)  # Volume supérieur à 80% de la moyenne
        )

        # Condition alternative: Rebond sur la bande de Bollinger inférieure
        conditions.append(
            (dataframe['close'] < dataframe['bb_lower']) &
            (dataframe['rsi'] < 30) &
            (dataframe['volume'] > dataframe['volume_mean'])
        )

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions),
                'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        
        # Condition principale: RSI haut ou croisement MACD négatif
        conditions.append(
            (dataframe['rsi'] > self.rsi_sell.value) |
            ((dataframe['macd'] < dataframe['macdsignal']) & (dataframe['macd'] > 0))
        )

        # Condition alternative: Atteinte de la bande de Bollinger supérieure
        conditions.append(
            (dataframe['close'] > dataframe['bb_upper']) &
            (dataframe['rsi'] > 70)
        )

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions),
                'exit_long'] = 1

        return dataframe

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        # Protection contre les marchés volatils
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last_candle = dataframe.iloc[-1].squeeze()

        # Stop dynamique basé sur la volatilité récente
        lookback = self.protection_params['stoploss_lookback']
        if len(dataframe) >= lookback:
            recent_candles = dataframe[-lookback:]
            volatility = (recent_candles['high'].max() - recent_candles['low'].min()) / recent_candles['close'].iloc[0]
            
            # Ajuster le stop-loss en fonction de la volatilité
            dynamic_stop = max(
                self.protection_params['stoploss_min_pct'],
                min(
                    self.protection_params['stoploss_max_pct'],
                    -0.5 * volatility
                )
            )
            return dynamic_stop

        return self.stoploss

    def confirm_trade_exit(self, pair: str, trade: Trade, order_type: str, amount: float,
                           rate: float, time_in_force: str, exit_reason: str,
                           current_time: datetime, **kwargs) -> bool:
        # Empêcher la sortie pendant les fortes tendances haussières
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last_candle = dataframe.iloc[-1].squeeze()

        if exit_reason == 'roi' and last_candle['macd'] > last_candle['macdsignal'] and last_candle['ema_fast'] > last_candle['ema_slow']:
            return False  # Annuler la sortie si la tendance est toujours haussière

        return True