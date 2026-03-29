"""
Solar panel power generation simulator.

The module estimates hourly electrical power produced by a solar panel
using historical meteorological data and solar geometry calculations.
"""
import pandas as pd
from timezonefinder import TimezoneFinder
from openmeteopy import OpenMeteo
from openmeteopy.hourly import HourlyHistorical
from openmeteopy.daily import DailyHistorical
from openmeteopy.options import HistoricalOptions
import pvlib
from typeguard import typechecked


class SolarPanelPower:
    """
    Solar panel power generation simulator.

    The class estimates hourly electrical power produced by a solar panel
    using historical meteorological data and solar geometry calculations.
    """

    @typechecked
    def __init__(self, config: dict):
        """
        Initialize the solar panel power calculator.

        The class simulates hourly power generation of a solar panel using
        historical weather data from Open-Meteo and solar position modeling.

        Args:
            config (dict): Configuration dictionary containing location,
                simulation period and solar panel parameters.

        Note:
            Default configuration can be obtained using the method
            `SolarPanelPower.get_default_config()`.

        Example:
            >>> config = {
            ...     "latitude": 54.9874,
            ...     "longitude": 82.8646,
            ...     "start_date": "2025-01-01",
            ...     "end_date": "2026-01-01",
            ...     "tilt_deg": 90,
            ...     "panel_azimuth_deg": 180,
            ...     "area_m2": 0.627,
            ...     "panel_efficiency": 0.1923,
            ...     "dc_efficiency": 1,
            ...     "timezone": "Asia/Novosibirsk"
            ... }

            >>> solar_power = SolarPanelPower(config)
        """
        self.config = config
        self.__default_config = {
            "latitude": 54.9874,                         # Your coordinates
            "longitude": 82.8646,                        # Your coordinates

            "start_date": "2025-01-01",                  # Date range YYYY-MM-DD
            "end_date": "2026-01-01",                    # Date range YYYY-MM-DD

            "tilt_deg": 90,                              # Tilt angle of the solar panel from horizontal (deg). Range 0-90
            "panel_azimuth_deg": 180,                    # Panel azimuth: 180° = south, 90° = east, 270° = west, 0° = north.

            "area_m2": 0.627,                            # Total panel area (m²).
            "panel_efficiency": 0.1923,                  # Module conversion efficiency
            "dc_efficiency": 1,                          # Electrical efficiency of DC system (controller, wiring).

            "timezone": "Asia/Novosibirsk",              # Time zone of the station location (IANA format).
            # "timezone": ""                             # Leave empty ("") to detect timezone automatically from coordinates.
        }

        self.df = pd.DataFrame()

    @typechecked
    def _get_timezone(self) -> str:
        tf = TimezoneFinder()
        if self.config.get("timezone", "") == "":
            tz = tf.timezone_at(lat=self.config["latitude"], lng=self.config["longitude"])
            if tz is None:
                tz = "UTC"
            print(tz)
        else:
            tz = self.config["timezone"]

        return tz

    @typechecked
    def _get_meteo_data(self, tz: str) -> pd.DataFrame:

        options = HistoricalOptions(self.config["latitude"],
                                    self.config["longitude"],
                                    start_date=self.config["start_date"],
                                    end_date=self.config["end_date"],
                                    timezone=tz)
        hourly = HourlyHistorical()
        self.df = OpenMeteo(options, hourly=hourly.all()).get_pandas().reset_index()
        self.df = self.df[[
            "time",
            "shortwave_radiation",
            "temperature_2m",
            "snowfall",
            "precipitation"
        ]]

        self.df["time"] = pd.to_datetime(self.df["time"]).dt.tz_localize(tz)
        self.df = self.df.set_index("time").sort_index()

        daily = DailyHistorical()
        daily_df = OpenMeteo(options, daily=daily.all()).get_pandas().reset_index()
        daily_df = daily_df[["time", "sunrise", "sunset"]]

        daily_df["time"] = pd.to_datetime(daily_df["time"]).dt.tz_localize(tz)
        daily_df = daily_df.set_index("time").sort_index()

        daily_df["sunrise"] = pd.to_datetime(daily_df["sunrise"])
        daily_df["sunset"] = pd.to_datetime(daily_df["sunset"])
        daily_df["sun_duration"] = ((daily_df["sunset"] - daily_df["sunrise"]).dt.total_seconds() / 3600).round(2)

        self.df = self.df.join(
            daily_df,
            on=self.df.index.floor("D")
        )
        self.df = self.df.drop(columns="key_0")

        return self.df

    @typechecked
    def _calc_albedo_series(
        self,
        snow_fresh_albedo: float = 0.75,
        snow_old_albedo: float = 0.55,
        ground_albedo: float = 0.20,
        melt_temp_c: float = 0.5,
        snow_gain_per_cm: float = 0.35,
        cold_decay_per_hour: float = 0.002,
        warm_decay_per_hour: float = 0.02,
    ) -> pd.Series:

        if self.df is None or self.df.empty:
            raise Exception("Сначала получите метеоданные")

        required_cols = ["snowfall", "temperature_2m"]
        for col in required_cols:
            if col not in self.df.columns:
                raise ValueError(f"В self.df нет колонки '{col}'")

        df = self.df.copy()

        snowfall = df["snowfall"].fillna(0).astype(float)
        temp = df["temperature_2m"].astype(float)

        snow_state = 0.0
        albedo_values = []

        for sf, t in zip(snowfall, temp):
            # накапливаем "снежное состояние"
            if sf > 0:
                snow_state += sf * snow_gain_per_cm

            # таяние / старение
            if t > melt_temp_c:
                snow_state -= warm_decay_per_hour * (1 + max(t - melt_temp_c, 0))
            else:
                snow_state -= cold_decay_per_hour

            snow_state = max(0.0, min(1.0, snow_state))

            # интерполяция между землей и снегом
            # 0 -> ground_albedo
            # 1 -> snow_fresh_albedo
            # при частичном снежном покрове получается промежуточное значение
            albedo = ground_albedo + snow_state * (snow_fresh_albedo - ground_albedo)

            # если снег уже "старый", можно слегка ограничить сверху
            if snow_state < 0.4:
                albedo = min(albedo, snow_old_albedo)

            albedo_values.append(round(albedo, 3))

        return pd.Series(albedo_values, index=df.index, name="albedo")

    @typechecked
    def calculate(self):
        """
        Calculate hourly solar panel power generation.

        This method retrieves historical meteorological data from Open-Meteo,
        computes solar position using pvlib, estimates plane-of-array (POA)
        irradiance, and calculates the resulting electrical power produced
        by the solar panel.

        The result is stored in the attribute `self.df`.

        The index of the DataFrame represents hourly timestamps localized
        to the configured timezone.

        Raises:
            ValueError: If configuration parameters are invalid or required meteorological data cannot be retrieved.

        Example:
            >>> solar_power = SolarPanelPower(config)
            >>> solar_power.calculate()
            >>> df = solar_power.get_hourly_power()
        """
        tz = self._get_timezone()

        self._get_meteo_data(tz)

        times = self.df.index

        loc = pvlib.location.Location(self.config["latitude"], self.config["longitude"], tz=tz)
        solpos = loc.get_solarposition(times)
        zenith = solpos["zenith"].astype("float64")
        az_sun = solpos["azimuth"].astype("float64")

        ghi = self.df["shortwave_radiation"].astype("float64")

        sun_up = zenith < 90.0
        valid = sun_up & (ghi > 0.0)

        erbs = pvlib.irradiance.erbs(ghi, zenith, times)
        dni = erbs["dni"].where(valid, 0.0).clip(lower=0)
        dhi = erbs["dhi"].where(valid, 0.0).clip(lower=0)
        ghi_valid = ghi.where(valid, 0.0)

        dni_extra = pvlib.irradiance.get_extra_radiation(times)

        albedo = self._calc_albedo_series()

        poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt=self.config["tilt_deg"],
            surface_azimuth=self.config["panel_azimuth_deg"],
            solar_zenith=zenith,
            solar_azimuth=az_sun,
            dni=dni,
            ghi=ghi_valid,
            dhi=dhi,
            dni_extra=dni_extra,
            albedo=albedo,
            model="haydavies",
        )

        poa_global = poa["poa_global"].where(valid, 0.0)

        T_air = self.df["temperature_2m"]

        NOCT = 45
        gamma = -0.004

        T_module = T_air + (NOCT - 20) / 800 * poa_global

        temp_factor = 1 + gamma * (T_module - 25)

        pv_power_W = (
            poa_global
            * self.config["area_m2"]
            * self.config["panel_efficiency"]
            * self.config["dc_efficiency"]
            * temp_factor
        ).clip(lower=0)

        self.df["power"] = pv_power_W.round(1)

    @typechecked
    def get_default_config(self) -> dict:
        """
        Return the default configuration for the solar panel calculator.

        Returns:
            dict: Default configuration dictionary with all required parameters.

        Example:
            >>> config = SolarPanelPower.get_default_config()
            >>> config["latitude"] = 54.9874
            >>> config["longitude"] = 82.8646
            >>> solar_power = SolarPanelPower(config)
        """
        return self.__default_config

    @typechecked
    def get_hourly_power(self) -> pd.DataFrame:
        """
        Return the calculated hourly power generation time series.

        The method returns the DataFrame generated by `calculate()`.
        The DataFrame uses a timezone-aware datetime index and contains
        hourly values of wind speed and the corresponding turbine power.

        Returns:
            pd.DataFrame: Hourly time series.

        Raises:
            Exception: If the method `calculate()` has not been executed yet
                and the internal DataFrame is empty.

        Example:
            >>> wind = WindTurbinePower(config)
            >>> wind.calculate()
            >>> df = wind.get_hourly_power()
        """
        if self.df is None or self.df.empty:
            raise Exception("Запустите сначала метод calculate")
        return self.df

    @typechecked
    def _calc_metrics(self, df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
        str_output = ""
        data_list = []

        if df is None or df.empty:
            return pd.DataFrame(), str_output

        df = df.copy().sort_index()

        actual_start = df.index.min()
        actual_end = df.index.max()

        total_hours = len(df)
        total_days = round(total_hours / 24, 1)

        generation_hours = int((df["power"] > 0).sum())
        pct_generation_hours = round(generation_hours / total_hours * 100, 2) if total_hours > 0 else 0

        mean_radiation = round(df["shortwave_radiation"].mean(), 2)
        max_radiation = round(df["shortwave_radiation"].max(), 2)

        total_generation_Wh = round(df["power"].sum(), 2)
        mean_power_W = round(df["power"].mean(), 2)
        max_power_W = round(df["power"].max(), 2)

        mean_generation_hours_per_day = round(generation_hours / total_days, 2) if total_days > 0 else 0

        # theoretical_peak_W = (
        #     self.config["area_m2"] * 1000 * self.config["panel_efficiency"] * self.config["dc_efficiency"]
        # )
        # capacity_factor_pct = round(mean_power_W / theoretical_peak_W * 100, 2) if theoretical_peak_W > 0 else 0

        # specific_generation_Wh_m2 = round(total_generation_Wh / self.config["area_m2"], 2) if self.config["area_m2"] > 0 else 0

        sun_hours = df["shortwave_radiation"] > 0
        mean_radiation_sun = round(df.loc[sun_hours, "shortwave_radiation"].mean(), 2) if sun_hours.any() else 0
        mean_power_sun = round(df.loc[sun_hours, "power"].mean(), 2) if sun_hours.any() else 0

        str_output += "\n==============================\n"
        str_output += f'Период: {actual_start.strftime("%Y-%m-%d")} — {actual_end.strftime("%Y-%m-%d")}\n'
        str_output += f"Всего часов: {total_hours}\n"
        str_output += f"Всего дней: {total_days}\n"
        str_output += f"Часы генерации (P > 0): {generation_hours}\n"
        str_output += f"Доля часов генерации: {pct_generation_hours}%\n"
        str_output += f"Суммарная генерация: {total_generation_Wh} Вт·ч\n"
        str_output += f"Максимальная солнечная радиация: {max_radiation} Вт/м²\n"
        str_output += f"Максимальная мощность панели: {max_power_W} Вт\n"
        str_output += f"Среднее число часов генерации в день: {mean_generation_hours_per_day}\n"
        str_output += f"Средняя солнечная радиация (за все часы): {mean_radiation} Вт/м²\n"
        str_output += f"Средняя солнечная радиация (в часы солнца): {mean_radiation_sun} Вт/м²\n"
        str_output += f"Средняя мощность панели (за все часы): {mean_power_W} Вт\n"
        str_output += f"Средняя мощность панели (в часы генерации): {mean_power_sun} Вт\n"

        data_list.append({
            "start_period": actual_start,
            "end_period": actual_end,
            "n_hours_total": total_hours,
            "n_days_total": total_days,
            "generation_hours": generation_hours,
            "pct_generation_hours": pct_generation_hours,
            "total_generation_Wh": total_generation_Wh,
            "max_radiation_Wm2": max_radiation,
            "max_power_W": max_power_W,
            "mean_generation_hours_per_day": mean_generation_hours_per_day,
            "mean_radiation_Wm2": mean_radiation,
            "mean_radiation_sun_Wm2": mean_radiation_sun,
            "mean_power_W": mean_power_W,
            "mean_power_sun_W": mean_power_sun,
            # "capacity_factor_pct": capacity_factor_pct,
            # "specific_generation_Wh_m2": specific_generation_Wh_m2,
        })

        print(str_output)

        df_output = pd.DataFrame(data_list)
        return df_output, str_output

    @typechecked
    def _monthly_range(self) -> tuple[pd.DataFrame, str]:
        if self.df is None or self.df.empty:
            raise Exception("Запустите сначала метод calculate")

        df_list = []
        protocol_output = ""

        grouped = self.df.groupby([self.df.index.year, self.df.index.month], sort=True)

        for (year, month), df_group in grouped:
            df_metrics, str_protocol = self._calc_metrics(df_group)
            if not df_metrics.empty:
                df_metrics["year"] = year
                df_metrics["month"] = month
                df_metrics["period_name"] = f"{year}-{month:02d}"
                df_list.append(df_metrics)

            protocol_output += str_protocol

        if len(df_list) == 0:
            return pd.DataFrame(), protocol_output

        df_output = pd.concat(df_list, ignore_index=True)
        df_output = df_output.sort_values(["year", "month"]).reset_index(drop=True)
        return df_output, protocol_output

    @typechecked
    def _seasonal_range(self) -> tuple[pd.DataFrame, str]:
        if self.df is None or self.df.empty:
            raise Exception("Запустите сначала метод calculate")

        df = self.df.copy()

        def get_season(month: int) -> str:
            if month in [12, 1, 2]:
                return "winter"
            elif month in [3, 4, 5]:
                return "spring"
            elif month in [6, 7, 8]:
                return "summer"
            else:
                return "autumn"

        df["season"] = df.index.month.map(get_season)
        df["season_year"] = df.index.year
        df.loc[df.index.month == 12, "season_year"] = df.loc[df.index.month == 12, "season_year"] + 1

        df_list = []
        protocol_output = ""

        grouped = df.groupby(["season_year", "season"], sort=True)

        for (season_year, season), df_group in grouped:
            df_group = df_group.drop(columns=["season", "season_year"]).copy()

            df_metrics, str_protocol = self._calc_metrics(df_group)
            if not df_metrics.empty:
                df_metrics["season_year"] = season_year
                df_metrics["season"] = season
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

        total_generation = df_output["total_generation_Wh"].sum()
        if total_generation > 0:
            df_output["season_generation_share_pct"] = (
                df_output["total_generation_Wh"] / total_generation * 100
            ).round(2)
        else:
            df_output["season_generation_share_pct"] = 0.0

        return df_output, protocol_output

    @typechecked
    def _save_protocol(self, str_protocol: str, path_protocol: str) -> None:
        with open(path_protocol, "w", encoding="utf-8") as f:
            f.write(str_protocol)

    @typechecked
    def get_all_period_metrics(self, path_protocol: str = "") -> pd.DataFrame:
        """
        Calculate solar generation statistics for the entire simulation period.

        The method computes summary metrics such as total energy production,
        generation hours, radiation statistics and average panel power.

        Args:
            path_protocol (str, optional): Path to a text file where the
                detailed textual report will be saved. If empty, the report
                is not written to a file.

        Returns:
            pd.DataFrame: Table containing calculated metrics for the full
            simulation period.

        Raises:
            Exception: If `calculate()` has not been executed and no data
                is available.

        Example:
            >>> solar_power.calculate()
            >>> metrics_df = solar_power.get_all_period_metrics()
        """
        df, str_protocol = self._calc_metrics(self.df)

        if path_protocol != "":
            self._save_protocol(str_protocol, path_protocol)

        return df

    @typechecked
    def get_monthly_metrics(self, path_protocol: str = "") -> pd.DataFrame:
        """
        Calculate solar generation statistics for each month.

        The simulation period is split into monthly intervals and met rics
        are calculated independently for every month.

        Args:
            path_protocol (str, optional): Path to a file where the textual
                report will be saved. If empty, the report is not saved.

        Returns:
            pd.DataFrame: Table containing metrics for each month of the
            simulation period.

        Raises:
            Exception: If `calculate()` has not been executed.

        Example:
            >>> solar_power.calculate()
            >>> monthly_metrics = solar_power.get_monthly_metrics()
        """
        df, str_protocol = self._monthly_range()

        if path_protocol != "":
            self._save_protocol(str_protocol, path_protocol)

        return df

    @typechecked
    def get_seasonal_metrics(self, path_protocol: str = "") -> pd.DataFrame:
        """
        Calculate solar generation statistics grouped by seasons.

        Seasons are defined using meteorological convention:

            - Winter: December – February
            - Spring: March – May
            - Summer: June – August
            - Autumn: September – November

        Args:
            path_protocol (str, optional): Path to a file where the textual
                report will be saved.

        Returns:
            pd.DataFrame: Table containing metrics for each season.

        Raises:
            Exception: If `calculate()` has not been executed.

        Example:
            >>> solar_power.calculate()
            >>> seasonal_metrics = solar_power.get_seasonal_metrics()
        """
        df, str_protocol = self._seasonal_range()

        if path_protocol != "":
            self._save_protocol(str_protocol, path_protocol)

        return df
