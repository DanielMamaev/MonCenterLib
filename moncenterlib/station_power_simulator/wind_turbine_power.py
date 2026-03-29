"""
Wind turbine power generation simulator.

The module estimates hourly electrical power output of a wind turbine
using historical weather data and turbine performance parameters.
"""
from typeguard import typechecked
import pandas as pd
import numpy as np
from timezonefinder import TimezoneFinder
from openmeteopy import OpenMeteo
from openmeteopy.hourly import HourlyHistorical
from openmeteopy.options import HistoricalOptions


class WindTurbinePower:
    """
    Wind turbine power generation simulator.

    The class estimates hourly electrical power output of a wind turbine
    using historical weather data and turbine performance parameters.
    """
    @typechecked
    def __init__(self, config: dict) -> None:
        """
        Initialize the wind turbine power calculator.

        The class simulates hourly electrical power generation of a wind turbine
        using historical meteorological data from Open-Meteo.

        Args:
            config (dict): Configuration dictionary containing turbine parameters,
                geographic location and simulation period.

        Note:
            Default configuration can be obtained using:

            >>> WindTurbinePower.get_default_config()

        Example:
            >>> config = WindTurbinePower.get_default_config()
            >>> config["latitude"] = 54
            >>> wind = WindTurbinePower(config)
        """
        self.df: pd.DataFrame = pd.DataFrame()
        self.__default_config = {
            "latitude": 54.9874,             # Your coordinates
            "longitude": 82.8646,            # Your coordinates

            "start_date": "2025-01-01",      # Date range YYYY-MM-DD
            "end_date": "2026-01-01",        # Date range YYYY-MM-DD

            "diameter": 0.66,                # Rotor diameter (m)

            "blade_length": 1.5,             # Blade length (m). If you have a Vertical Axis (VAWT), set blade_length > 0.
            # "blade_length": 0,             # If you have a Horizontal Axis (HAWT), set blade_length = 0
            "rated_power": 450,              # Nominal power (W)
            "rated_speed": 11,               # Nominal wind speed (m/s)

            "cut_in": 1.3,                   # Starting wind speed (m/s)
            "cut_out": 45,                   # Maximum wind speed (m/s)

            "cp": 0.25,                      # Aerodynamic power coefficient of rotor (Betz limit ≈ 0.59). Range 0.25 – 0.45
            "turbine_efficiency": 0.8,       # Mechanical efficiency: gearbox, bearings, generator. Range 0.7 – 0.9

            "dc_efficiency": 1,              # Electrical efficiency of DC conversion (controller / wiring losses). Range 0.7–0.95

            "timezone": "Asia/Novosibirsk",  # Time zone of the station location (IANA format).
            # "timezone": ""                 # Leave empty ("") to detect timezone automatically from coordinates.
        }

        self.config = config

    @typechecked
    def get_hourly_power(self) -> pd.DataFrame:
        """
        Return the calculated hourly wind turbine power time series.

        Returns:
            pd.DataFrame: Hourly time series with wind speed and turbine power.

        Raises:
            Exception: If `calculate()` has not been executed and
                the internal DataFrame is empty.

        Example:
            >>> wind.calculate()
            >>> df = wind.get_hourly_power()
        """
        if self.df is None or self.df.empty:
            raise Exception("Запустите сначала метод calculate")
        return self.df

    @typechecked
    def calculate(self):
        """
        Calculate hourly wind turbine power generation.

        This method retrieves historical weather data from Open-Meteo,
        estimates air density using temperature, pressure and humidity,
        and computes turbine power using the wind power equation.

        The calculated power output is stored in `self.df`.

        The resulting DataFrame contains a timezone-aware datetime index.

        Raises:
            Exception: If meteorological data cannot be retrieved.

        Example:
            >>> wind = WindTurbinePower(config)
            >>> wind.calculate()
            >>> df = wind.get_hourly_power()
        """
        # Определение временной зоны по координатам
        tf = TimezoneFinder()
        if self.config.get("timezone", "") == "":
            tz = tf.timezone_at(lat=self.config["latitude"], lng=self.config["longitude"])
            if tz is None:
                tz = "UTC"
            print(tz)
        else:
            tz = self.config["timezone"]

        # Получение метеорологических данных
        options = HistoricalOptions(self.config["latitude"],
                                    self.config["longitude"],
                                    start_date=self.config["start_date"],
                                    end_date=self.config["end_date"],
                                    timezone=tz)
        hourly = HourlyHistorical()
        self.df = OpenMeteo(options, hourly=hourly.all()).get_pandas().reset_index()
        self.df = self.df[["time", "temperature_2m", "relativehumidity_2m", "surface_pressure", "windspeed_10m"]]
        self.df["time"] = pd.to_datetime(self.df["time"])
        self.df["windspeed_10m"] = (self.df["windspeed_10m"] / 3.6).round(1)

        # Расчет площади ротора
        if self.config["blade_length"] == 0:
            A = np.pi * (self.config["diameter"] / 2) ** 2
        else:
            A = self.config["diameter"] * self.config["blade_length"]

        # Расчет плотности воздуха
        T = self.df["temperature_2m"]
        RH = self.df["relativehumidity_2m"]
        P = self.df["surface_pressure"]

        Tk = T + 273.15
        # давление насыщенного пара
        es = 6.112 * np.exp((17.67 * T) / (T + 243.5))
        # давление пара
        e = RH / 100 * es
        # плотность воздуха
        rho = ((P - e) * 100) / (287.05 * Tk) + (e * 100) / (461.5 * Tk)
        # self.df["air_density"] = rho

        # Расчет мощности ветрогеератора

        V = self.df["windspeed_10m"]
        # физическая мощность
        power = 0.5 * rho * A * V**3 * self.config["cp"] * self.config["turbine_efficiency"] * self.config["dc_efficiency"]

        # ограничения турбины
        power = np.where(V < self.config["cut_in"], 0, power)
        power = np.where(V >= self.config["rated_speed"], self.config["rated_power"], power)
        power = np.where(V >= self.config["cut_out"], 0, power)

        power = np.minimum(power, self.config["rated_power"])
        self.df["power"] = power.round(1)

        self.df = self.df[["time", "windspeed_10m", "power"]]

        self.df = self.df.set_index("time")
        self.df.index = self.df.index.tz_localize(tz)

    @typechecked
    def get_default_config(self) -> dict:
        """
        Return the default configuration for the wind turbine calculator.

        Returns:
            dict: Dictionary containing default parameters for turbine
            configuration, location and simulation period.

        Example:
            >>> config = WindTurbinePower.get_default_config()
            >>> wind = WindTurbinePower(config)
        """
        return self.__default_config

    @typechecked
    def _calc_metrics(self, df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
        str_output = ""
        data_list = []

        if df is None or df.empty:
            # print("\n===============\nНет данных за период")
            return pd.DataFrame(), str_output

        actual_start = pd.Timestamp(df.index[0])
        actual_end = pd.Timestamp(df.index[-1])
        str_output += "\n==============================\n"
        str_output += "Высота на уровнем земли: 10 м\n"
        str_output += f'Период: {actual_start.strftime("%Y-%m-%d")} — {actual_end.strftime("%Y-%m-%d")}\n'

        mean_windspeed_10m = round(df["windspeed_10m"].mean(), 1)
        mean_power_10m = round(df["power"].mean(), 1)

        data, str_out = self._get_stats(df, "windspeed_10m", "power")
        data["start_period"] = actual_start.strftime("%Y-%m-%d")
        data["end_period"] = actual_end.strftime("%Y-%m-%d")
        data["mean_windspeed"] = mean_windspeed_10m
        data["mean_power"] = mean_power_10m
        data_list.append(data)
        str_output += str_out
        str_output += f"Средняя скорость ветра - {mean_windspeed_10m} м/с \n" + \
            f"Средняя мощность ветрогенератора - {mean_power_10m} Вт*ч \n"

        print(str_output)

        df_output = pd.DataFrame(data_list)
        df_output["start_period"] = pd.to_datetime(df_output["start_period"])
        df_output["end_period"] = pd.to_datetime(df_output["end_period"])
        return df_output, str_output

    @typechecked
    def _monthly_range(self, step: int = 1) -> tuple[pd.DataFrame, str]:
        if self.df is None or self.df.empty:
            raise Exception("Запустите сначала метод calculate")

        tz = self.df.index.tz

        start_date = pd.to_datetime(self.config["start_date"]).tz_localize(tz)
        end_date = pd.to_datetime(self.config["end_date"]).tz_localize(tz)

        start_year = start_date.year
        end_year = end_date.year

        df_list = []
        protocol_output = ""

        for year in range(start_year, end_year + 1):
            for month in range(1, 13, step):

                period_start = pd.Timestamp(year=year, month=month, day=1, tz=tz)
                period_end = period_start + pd.DateOffset(months=step)

                actual_start = max(period_start, start_date)
                actual_end = min(period_end, end_date + pd.Timedelta(days=1))

                df_filtered = self.df[
                    (self.df.index >= actual_start) &
                    (self.df.index < actual_end)
                ]

                df_metrics, str_protocol = self._calc_metrics(df_filtered)

                if not df_metrics.empty:
                    df_list.append(df_metrics)

                protocol_output += str_protocol

        if df_list:
            df_output = pd.concat(df_list, ignore_index=True)
        else:
            df_output = pd.DataFrame()

        return df_output, protocol_output

    @typechecked
    def _seasonal_range(self) -> tuple[pd.DataFrame, str]:
        if self.df is None or self.df.empty:
            raise Exception("Запустите сначала метод calculate")

        df = self.df.copy()
        df["month"] = df.index.month
        df["year"] = df.index.year

        # Название сезона
        def get_season(month):
            if month in [12, 1, 2]:
                return "winter"
            elif month in [3, 4, 5]:
                return "spring"
            elif month in [6, 7, 8]:
                return "summer"
            else:
                return "autumn"

        df["season"] = df["month"].apply(get_season)

        # Сезонный год:
        # декабрь относится к зиме следующего года
        df["season_year"] = df["year"]
        df.loc[df["month"] == 12, "season_year"] = df.loc[df["month"] == 12, "year"] + 1

        df_list = []
        protocol_output = ""

        grouped = df.groupby(["season_year", "season"], sort=True)

        for (season_year, season), df_group in grouped:
            df_group = df_group.sort_values("time")

            df_metrics, str_protocol = self._calc_metrics(df_group)

            if not df_metrics.empty:
                df_metrics["season"] = season
                df_metrics["season_year"] = season_year
                df_list.append(df_metrics)

            protocol_output += f"\n===== {season} {season_year} =====\n"
            protocol_output += str_protocol

        if len(df_list) == 0:
            return pd.DataFrame(), protocol_output

        df_output = pd.concat(df_list, ignore_index=True)

        season_order = {"winter": 1, "spring": 2, "summer": 3, "autumn": 4}
        df_output["season_order"] = df_output["season"].map(season_order)
        df_output = df_output.sort_values(["season_year", "season_order"]).reset_index(drop=True)
        df_output = df_output.drop(columns=["season_order"])

        return df_output, protocol_output

    @typechecked
    def _save_protocol(self, str_protocol: str, path_protocol: str):
        with open(path_protocol, 'w', encoding="utf-8") as f:
            f.write(str_protocol)

    @typechecked
    def get_all_period_metrics(self, path_protocol: str = "") -> pd.DataFrame:
        """
        Calculate wind turbine statistics for the entire simulation period.

        The method computes wind regime statistics and turbine generation
        metrics for the full dataset.

        Args:
            path_protocol (str, optional): Path to a file where the textual
                report will be saved. If empty, the report is not written.

        Returns:
            pd.DataFrame: Table containing calculated metrics for the full
            simulation period.

        Example:
            >>> wind.calculate()
            >>> metrics = wind.get_all_period_metrics()
        """
        df, str_protocol = self._calc_metrics(self.df)
        if path_protocol != "":
            self._save_protocol(str_protocol, path_protocol)

        return df

    @typechecked
    def get_monthly_metrics(self, step: int = 1, path_protocol: str = "") -> pd.DataFrame:
        """
        Calculate wind turbine statistics aggregated by monthly periods.

        The simulation range is divided into intervals of `step` months,
        and metrics are calculated for each period.

        Args:
            step (int, optional): Number of months per aggregation period.
                For example, ``1`` means monthly statistics and ``3`` means
                quarterly statistics.
            path_protocol (str, optional): Path to a file where the textual
                report will be saved.

        Returns:
            pd.DataFrame: Table containing metrics for each calculated period.

        Example:
            >>> wind.calculate()
            >>> monthly_metrics = wind.get_monthly_metrics()
        """
        df, str_protocol = self._monthly_range(step)
        if path_protocol != "":
            self._save_protocol(str_protocol, path_protocol)

        return df

    @typechecked
    def get_seasonal_metrics(self, path_protocol: str = "") -> pd.DataFrame:
        """
        Calculate wind turbine statistics grouped by seasons.

        Seasons follow the meteorological definition:

            - Winter: December – February
            - Spring: March – May
            - Summer: June – August
            - Autumn: September – November

        Args:
            path_protocol (str, optional): Path to a file where the textual
                report will be saved.

        Returns:
            pd.DataFrame: Table containing calculated metrics for each season.

        Example:
            >>> wind.calculate()
            >>> seasonal_metrics = wind.get_seasonal_metrics()
        """
        df, str_protocol = self._seasonal_range()
        if path_protocol != "":
            self._save_protocol(str_protocol, path_protocol)
        return df

    @typechecked
    def _get_stats(self, df: pd.DataFrame, wind_col: str, power_col: str) -> tuple[dict, str]:
        if df is None or df.empty:
            raise Exception("Запустите сначала метод calculate")

        V = df[wind_col].astype(float)
        P = df[power_col].astype(float)

        cut_in = float(self.config["cut_in"])
        rated = float(self.config["rated_speed"])
        cut_out = float(self.config["cut_out"])

        n = len(V)
        if n == 0:
            print(f"\n=== {wind_col} ===")
            print("Нет данных")
            return {}, ""

        # Маски режимов
        m_below = V < cut_in
        m_between = (V >= cut_in) & (V < rated)
        m_rated = (V >= rated) & (V < cut_out)
        m_above = V >= cut_out

        # Доли времени (%)
        pct_below = m_below.mean() * 100
        pct_between = m_between.mean() * 100
        pct_rated = m_rated.mean() * 100
        pct_above = m_above.mean() * 100

        # Часы генерации
        gen_hours = int((P > 0).sum())

        # Срабатывания cut-out (переход в зону >= cut_out)
        above = m_above.astype(int)
        cutout_events = int((above.diff() == 1).sum())

        # Часы в cut-out
        cutout_hours = int(m_above.sum())

        # Печать отчёта
        str_output = f"Всего часов: {n} \n" + \
            f"Ниже cut-in: {pct_below:.2f}% \n" + \
            f"Между cut-in и rated: {pct_between:.2f}% \n" + \
            f"На номинале (по скорости): {pct_rated:.2f}% \n" + \
            f"Выше cut-out: {pct_above:.2f}% \n" + \
            f"Часы генерации (P > 0): {gen_hours} \n" + \
            f"Часы в cut-out: {cutout_hours} \n" + \
            f"Срабатывания cut-out: {cutout_events} \n"

        return {
            "n_hours_total": n,
            "n_days_total": round(n/24, 1),
            "pct_below_cut_in": round(pct_below, 1),
            "pct_between_cut_in_rated": round(pct_between, 1),
            "pct_rated_nominal": round(pct_rated, 1),
            "pct_above_cut_out": round(pct_above, 1),
            "generation_hours": gen_hours,
            "cutout_hours": cutout_hours,
            "cutout_events": cutout_events,
        }, str_output
