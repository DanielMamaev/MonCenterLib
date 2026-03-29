"""
Energy balance simulator for autonomous stations.

The module evaluates whether a set of energy sources
(solar panels, wind turbines, etc.) can support a constant load,
optionally including battery storage simulation.
"""
import pandas as pd
from typeguard import typechecked
from moncenterlib.station_power_simulator.solar_power import SolarPanelPower
from moncenterlib.station_power_simulator.wind_turbine_power import WindTurbinePower


class PowerBalanceAnalyzer:
    """
    Energy balance simulator for autonomous stations.

    The class evaluates whether a set of energy sources
    (solar panels, wind turbines, etc.) can support a constant load,
    optionally including battery storage simulation.
    """

    @typechecked
    def _save_protocol(self, str_protocol: str, path_protocol: str):
        with open(path_protocol, "w", encoding="utf-8") as f:
            f.write(str_protocol)


    @staticmethod
    @typechecked
    def combine_power(sources: list[SolarPanelPower | WindTurbinePower]) -> pd.DataFrame:
        """
        Combine power generation from multiple energy sources.

        The method takes a list of power source objects (e.g. solar panels,
        wind turbines), extracts their hourly power time series, and returns
        the total generated power.

        Each source must contain a DataFrame `df` with a column named "power"
        and a timezone-aware datetime index.

        Args:
            sources (list[SolarPanelPower | WindTurbinePower]): List of energy
                source objects that already executed their `calculate()` method.

        Returns:
            pd.DataFrame: DataFrame containing total station power generation
            with a datetime index.

        Raises:
            ValueError: If the source list is empty or if a source does not
            contain valid power data.

        Example:
            >>> solar.calculate()
            >>> wind.calculate()
            >>> df_station = PowerBalanceAnalyzer.combine_power([solar, wind])
        """
        if not sources:
            raise ValueError("Список источников пуст")

        dfs = []

        for i, src in enumerate(sources):
            if not hasattr(src, "df"):
                raise ValueError(f"Источник {src} не имеет df")

            if src.df is None or src.df.empty:
                raise ValueError(f"Источник {src} не содержит данных")

            if "power" not in src.df.columns:
                raise ValueError(f"В df источника {src} нет колонки 'power'")

            df = src.df[["power"]].copy()
            df = df.rename(columns={"power": f"power_{i}"})
            dfs.append(df)

        df_total = pd.concat(dfs, axis=1).fillna(0.0)
        df_total["power"] = df_total.sum(axis=1)
        return df_total[["power"]]

    @typechecked
    def calc_power_balance(
        self,
        input_df: pd.DataFrame,
        load_power_w: float,
        path_protocol: str = ""
    ) -> tuple[pd.DataFrame, dict]:
        """
        Evaluate whether generation covers a constant load.

        The method compares hourly generated power with a constant load
        and calculates deficit, surplus and system coverage metrics.

        Args:
            input_df (pd.DataFrame): DataFrame containing generation time series.
                Must contain a datetime index and a column with power values.
            load_power_w (float): Constant load power (W).
            path_protocol (str, optional): Path to a text file where the
                summary report will be saved.

        Returns:
            tuple[pd.DataFrame, dict]:
                - DataFrame: Hourly balance table containing generation, load, deficit, and surplus.
                - dict: Summary metrics describing system performance.

        Example:
            >>> analyzer = PowerBalanceAnalyzer()
            >>> df_station = analyzer.combine_power([solar, wind])
            >>> df_balance, metrics = analyzer.calc_power_balance(
            ...     df_station,
            ...     load_power_w=1.5
            ... )
        """

        df = input_df.copy()

        df["load_w"] = float(load_power_w)
        df["power_w"] = df["power"].astype(float)

        df["surplus_w"] = (df["power_w"] - df["load_w"]).clip(lower=0)
        df["deficit_w"] = (df["load_w"] - df["power_w"]).clip(lower=0)
        df["covered"] = df["deficit_w"] == 0

        n = len(df)
        hours_deficit = int((~df["covered"]).sum())
        hours_covered = int(df["covered"].sum())

        total_load_Wh = float(df["load_w"].sum())
        total_gen_Wh = float(df["power_w"].sum())
        total_deficit_Wh = float(df["deficit_w"].sum())
        total_surplus_Wh = float(df["surplus_w"].sum())

        mean_deficit_W = float(df.loc[df["deficit_w"] > 0, "deficit_w"].mean()) if hours_deficit else 0.0

        metrics = {
            "load_power_W": float(load_power_w),
            "n_hours": n,
            "hours_covered": hours_covered,
            "hours_deficit": hours_deficit,
            "pct_covered": round(hours_covered / n * 100, 2),
            "total_load_Wh": round(total_load_Wh, 1),
            "total_gen_Wh": round(total_gen_Wh, 1),
            "total_deficit_Wh": round(total_deficit_Wh, 1),
            "total_surplus_Wh": round(total_surplus_Wh, 1),
            "mean_deficit_W_when_deficit": round(mean_deficit_W, 1),
        }

        actual_start = df.index[0]
        actual_end = df.index[-1]

        str_protocol = ""
        str_protocol += "\n==============================\n"
        str_protocol += f'Период: {actual_start.strftime("%Y-%m-%d")} — {actual_end.strftime("%Y-%m-%d")}\n'
        str_protocol += f"Мощность нагрузки: {metrics['load_power_W']} Вт\n"
        str_protocol += f"Покрыто часов: {metrics['hours_covered']} из {metrics['n_hours']} ({metrics['pct_covered']}%)\n"
        str_protocol += f"Потребление нагрузки: {metrics['total_load_Wh']} Вт·ч\n"
        str_protocol += f"Генерация станции: {metrics['total_gen_Wh']} Вт·ч\n"
        str_protocol += f"Излишек генерации: {metrics['total_surplus_Wh']} Вт·ч\n"
        str_protocol += f"Дефицит: {metrics['total_deficit_Wh']} Вт·ч\n"
        str_protocol += f"Средний дефицит (в часы дефицита): {metrics['mean_deficit_W_when_deficit']} Вт\n"

        print(str_protocol)

        if path_protocol != "":
            self._save_protocol(str_protocol, path_protocol)

        return df, metrics

    @typechecked
    def calc_power_balance_with_battery(
        self,
        input_df: pd.DataFrame,
        load_power_w: float,
        battery_capacity_Wh: float,
        initial_soc_Wh: float | None = None,
        charge_efficiency: float = 1.0,
        discharge_efficiency: float = 1.0,
        min_soc_Wh: float = 0.0,
        path_protocol: str = ""
    ) -> tuple[pd.DataFrame, dict]:
        """
        Simulate power balance of a station with a battery storage system.

        The method performs an hourly simulation of station operation,
        considering generation, constant load and battery charge/discharge
        behavior.

        Battery state-of-charge (SOC) is updated at each time step and
        system shutdown events are detected when generation and battery
        energy are insufficient to cover the load.

        Args:
            input_df (pd.DataFrame): DataFrame containing station generation
                time series with a datetime index and a "power" column.
            load_power_w (float): Constant station load (W).
            battery_capacity_Wh (float): Total battery energy capacity (Wh).
            initial_soc_Wh (float, optional): Initial battery state of charge (Wh).
                If None, the battery starts fully charged.
            charge_efficiency (float, optional): Battery charging efficiency.
                Defaults to 1.0.
            discharge_efficiency (float, optional): Battery discharging efficiency.
                Defaults to 1.0.
            min_soc_Wh (float, optional): Minimum allowed battery state of charge.
                The battery cannot discharge below this level.
            path_protocol (str, optional): Path to a text file where the
                summary report will be saved.

        Returns:
            tuple[pd.DataFrame, dict]:

            - DataFrame: Hourly simulation results including generation,
              load, battery state-of-charge, and system status.
            - dict: Summary metrics including battery usage statistics and
              system shutdown events.

        Example:
            >>> analyzer = PowerBalanceAnalyzer()
            >>> df_station = analyzer.combine_power([solar, wind])
            >>> df_sim, metrics = analyzer.calc_power_balance_with_battery(
            ...     input_df=df_station,
            ...     load_power_w=1.5,
            ...     battery_capacity_Wh=35
            ... )
        """

        df = input_df.copy()

        if df is None or df.empty:
            raise ValueError("input_df пуст")

        if initial_soc_Wh is None:
            initial_soc_Wh = battery_capacity_Wh

        if not (0 <= initial_soc_Wh <= battery_capacity_Wh):
            raise ValueError("initial_soc_Wh должен быть в диапазоне [0, battery_capacity_Wh]")

        df["load_w"] = float(load_power_w)
        df["gen_w"] = df["power"].astype(float)

        # при часовом шаге W == Wh за шаг
        df["load_Wh"] = df["load_w"]
        df["gen_Wh"] = df["gen_w"]
        df["net_Wh"] = df["gen_Wh"] - df["load_Wh"]

        soc = float(initial_soc_Wh)
        eps = 1e-9

        soc_list = []
        charge_to_battery_list = []
        discharge_from_battery_list = []
        system_on_list = []

        first_shutdown_time = None

        for time, row in df.iterrows():
            net = float(row["net_Wh"])

            charge_to_battery = 0.0
            discharge_from_battery = 0.0
            system_on = True

            if net >= 0:
                # избыток -> в АКБ
                energy_to_store = net * charge_efficiency
                available_space = battery_capacity_Wh - soc
                actual_charge = min(energy_to_store, available_space)

                soc += actual_charge
                charge_to_battery = actual_charge

            else:
                # дефицит -> из АКБ
                demand_from_battery = abs(net) / discharge_efficiency if discharge_efficiency > 0 else abs(net)
                available_from_battery = max(soc - min_soc_Wh, 0.0)
                actual_discharge = min(demand_from_battery, available_from_battery)

                soc -= actual_discharge
                discharge_from_battery = actual_discharge

                supplied_from_battery = actual_discharge * discharge_efficiency
                unmet_load = max(abs(net) - supplied_from_battery, 0.0)

                if unmet_load > eps:
                    system_on = False
                    if first_shutdown_time is None:
                        first_shutdown_time = time

            soc_list.append(round(soc, 6))
            charge_to_battery_list.append(round(charge_to_battery, 6))
            discharge_from_battery_list.append(round(discharge_from_battery, 6))
            system_on_list.append(system_on)

        df["battery_soc_Wh"] = soc_list
        df["charge_to_battery_Wh"] = charge_to_battery_list
        df["discharge_from_battery_Wh"] = discharge_from_battery_list
        df["system_on"] = system_on_list

        # интервалы отключений/включений
        events = []
        prev_state = True
        shutdown_time = None

        for time, row in df.iterrows():
            current_state = bool(row["system_on"])

            # выключение
            if prev_state is True and current_state is False:
                shutdown_time = time

            # включение
            elif prev_state is False and current_state is True:
                restore_time = time
                duration_hours = int((restore_time - shutdown_time) / pd.Timedelta(hours=1))
                events.append({
                    "shutdown_time": shutdown_time,
                    "restore_time": restore_time,
                    "duration_hours": duration_hours
                })
                shutdown_time = None

            prev_state = current_state

        # если период закончился в выключенном состоянии
        if shutdown_time is not None:
            restore_time = pd.NaT
            duration_hours = int((df.index[-1] - shutdown_time) / pd.Timedelta(hours=1)) + 1
            events.append({
                "shutdown_time": shutdown_time,
                "restore_time": restore_time,
                "duration_hours": duration_hours
            })

        df_events = pd.DataFrame(events)

        metrics = {
            "load_power_W": float(load_power_w),
            "battery_capacity_Wh": float(battery_capacity_Wh),
            "initial_soc_Wh": float(initial_soc_Wh),
            "final_soc_Wh": round(float(df["battery_soc_Wh"].iloc[-1]), 2),
            "n_hours": int(len(df)),
            "hours_system_on": int(df["system_on"].sum()),
            "hours_system_off": int((~df["system_on"]).sum()),
            "pct_system_on": round(df["system_on"].mean() * 100, 2),
            "total_generation_Wh": round(float(df["gen_Wh"].sum()), 2),
            "total_load_Wh": round(float(df["load_Wh"].sum()), 2),
            "first_shutdown_time": first_shutdown_time,
            "battery_was_enough": first_shutdown_time is None,
            "events": df_events
        }

        actual_start = df.index[0]
        actual_end = df.index[-1]

        str_protocol = ""

        str_protocol += "\n==============================\n"
        str_protocol += f'Период: {actual_start.strftime("%Y-%m-%d")} — {actual_end.strftime("%Y-%m-%d")}\n'
        str_protocol += f"Нагрузка: {metrics['load_power_W']} Вт\n"
        str_protocol += f"Ёмкость аккумулятора: {metrics['battery_capacity_Wh']} Вт·ч\n"
        str_protocol += f"Начальный заряд АКБ: {metrics['initial_soc_Wh']} Вт·ч\n"
        str_protocol += f"Конечный заряд АКБ: {metrics['final_soc_Wh']} Вт·ч\n"
        str_protocol += f"Система работала: {metrics['hours_system_on']} из {metrics['n_hours']} часов ({metrics['pct_system_on']}%)\n"
        str_protocol += f"Суммарная генерация: {metrics['total_generation_Wh']} Вт·ч\n"
        str_protocol += f"Суммарная нагрузка: {metrics['total_load_Wh']} Вт·ч\n"

        if metrics["battery_was_enough"]:
            str_protocol += "Вывод: станция с аккумулятором обеспечивает бесперебойную работу на всём интервале.\n"
        else:
            str_protocol += f"Вывод: были отключения. Первый момент отключения: {metrics['first_shutdown_time']} \n"

            if not df_events.empty:
                str_protocol += "\nИнтервалы отключений:\n"
                for i, row in df_events.iterrows():
                    shutdown = row["shutdown_time"]
                    restore = row["restore_time"]
                    duration = row["duration_hours"]

                    if pd.isna(restore):
                        str_protocol += f"{i+1}. Выключение: {shutdown}, восстановление: нет, длительность: {duration} ч\n"
                    else:
                        str_protocol += f"{i+1}. Выключение: {shutdown}, включение: {restore}, длительность: {duration} ч\n"


        print(str_protocol)

        if path_protocol != "":
            self._save_protocol(str_protocol, path_protocol)

        return df, metrics
