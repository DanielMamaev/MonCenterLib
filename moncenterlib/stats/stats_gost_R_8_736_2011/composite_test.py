from moncenterlib.stats.stats_gost_R_8_736_2011.dataclasses import (
    CompositeCriterion1Result,
    CompositeCriterion2Result,
    CompositeNormalityResult)
from moncenterlib.stats.stats_gost_R_8_736_2011.tables import TABLE_B1, TABLE_B2, TABLE_B3
from moncenterlib.stats.stats_gost_R_8_736_2011.basic_stats import calc_basic_stats

def _get_b1_limits(n: int, q_percent: int) -> tuple[float, float]:
    """
    7. Доверительные границы случайной погрешности
    7.3 При числе результатов измерений 15 < n <= 50

    Получить нижнюю и верхнюю границы для критерия 1 приложения Б по таблице Б.1.
    Если число результатов измерений отсутствует в таблице, границы вычисляются
    линейной интерполяцией между ближайшими табличными значениями.
    Для промежуточных n используется линейная интерполяция.

    Args:
        n (int): количество результатов измерений
        q_percent (int): уровень значимости 1 или 5. Это значит (1 и 99) или (5 и 95)

    Raises:
        ValueError: q_percent должно быть 1 или 5. (1 и 99, 5 и 95)
        ValueError: Для указанного n нет данных в TABLE_B1
        RuntimeError: Не удалось интерполировать значения TABLE_B1

    Returns:
        tuple[float, float]: Кортеж `(d_low, d_high)` с нижней и верхней
            доверительными границами для критерия 1 приложения Б.

    Example:
        >>> _get_b1_limits(16, 5)
        (0.7236, 0.8884)
        >>> _get_b1_limits(17, 5)
        (0.72496, 0.88608)
    """
    if q_percent not in (1, 5):
        raise ValueError("q_percent должно быть 1 или 5. (1 и 99, 5 и 95)")

    keys = sorted(TABLE_B1.keys())

    if n < keys[0] or n > keys[-1]:
        raise ValueError(f"Для n={n} нет данных в TABLE_B1")

    if n in TABLE_B1:
        row = TABLE_B1[n][q_percent]
        return row["low"], row["high"]

    for i in range(len(keys) - 1):
        n1, n2 = keys[i], keys[i + 1]
        if n1 < n < n2:
            row1 = TABLE_B1[n1][q_percent]
            row2 = TABLE_B1[n2][q_percent]

            k = (n - n1) / (n2 - n1)

            low = row1["low"] + k * (row2["low"] - row1["low"])
            high = row1["high"] + k * (row2["high"] - row1["high"])

            return low, high

    raise RuntimeError("Не удалось интерполировать значения TABLE_B1")


def _get_b2_params(n: int, q_percent: int) -> tuple[int, float]:
    """
    7. Доверительные границы случайной погрешности
    7.3 При числе результатов измерений 15 < n <= 50

    Получить параметры `m` и `P` из таблицы Б.2 для критерия 2 приложения Б.
    По числу результатов измерений функция находит подходящий диапазон `n`
    и возвращает допустимое число превышений порога и соответствующее
    табличное значение вероятности.

    Args:
        n (int): количество результатов измерений
        q_percent (int): уровень значимости 1, 2 или 5

    Raises:
        ValueError: "q_percent должно быть 1, 2 или 5"
        ValueError: Для указанного n нет данных в TABLE_B2

    Returns:
        tuple[int, float]: Кортеж `(m, P)`, где `m` - число разностей, а `P` - табличное значение вероятности.

    Example:
        >>> _get_b2_params(18, 5)
        (1, 0.98)
        >>> _get_b2_params(24, 1)
        (2, 0.98)
    """
    if q_percent not in (1, 2, 5):
        raise ValueError("q_percent должно быть 1, 2 или 5")

    for (n_min, n_max), params_by_q in TABLE_B2.items():
        if n_min <= n <= n_max:
            row = params_by_q[q_percent]
            return row["m"], row["P"]

    raise ValueError(f"Для n={n} нет данных в TABLE_B2")


def _criterion_b1(values: list[float], q_percent: int = 5) -> CompositeCriterion1Result:
    """
    7. Доверительные границы случайной погрешности
    7.3 При числе результатов измерений 15 < n <= 50

    Выполнить проверку по критерию 1 приложения Б для оценки нормальности
    распределения результатов измерений при `15 < n <= 50`.
    Функция вычисляет отношение `d~`, получает доверительные границы из
    таблицы Б.1 и возвращает результат проверки.

    Args:
        values (list[float]): список результатов измерений
        q_percent (int, optional): уровень значимости 1 или 5. Defaults to 5.

    Raises:
        ValueError: Критерий Б.1 применим только при 15 < n <= 50
        ValueError: Смещенное СКО равно 0
        ValueError: "q_percent должно быть 1 или 5. (1 и 99, 5 и 95)"
        ValueError: Для указанного n нет данных в TABLE_B1
        RuntimeError: Не удалось интерполировать значения TABLE_B1

    Returns:
        CompositeCriterion1Result: Результат проверки критерия 1. См. описание класса CompositeCriterion1Result.

    Example:
        >>> result = _criterion_b1(list(range(1, 17)), 5)
        >>> result.passed
        True
    """
    n = len(values)
    if not (15 < n <= 50):
        raise ValueError("Критерий Б.1 применим только при 15 < n <= 50")

    S_biased = calc_basic_stats(values).S_biased
    if S_biased == 0:
        raise ValueError("Смещенное СКО равно 0")

    x_mean = sum(values) / n
    d = sum(abs(x - x_mean) for x in values) / (n * S_biased)

    d_low, d_high = _get_b1_limits(n, q_percent)
    passed = d_low < d <= d_high

    return CompositeCriterion1Result(d=d, d_low=d_low, d_high=d_high, passed=passed)


def _criterion_b2(values: list[float], q_percent: int = 5) -> CompositeCriterion2Result:
    """
    7. Доверительные границы случайной погрешности
    7.3 При числе результатов измерений 15 < n <= 50

    Выполнить проверку по критерию 2 приложения Б для оценки нормальности
    распределения результатов измерений при `15 < n <= 50`.
    Функция определяет допустимое число превышений по таблице Б.2, вычисляет
    порог через таблицу Б.3 и возвращает результат проверки.

    Args:
        values (list[float]): список результатов измерений
        q_percent (int, optional): уровень значимости 1, 2 или 5. Defaults to 5.

    Raises:
        ValueError: Критерий Б.2 применим только при 15 < n <= 50
        ValueError: "q_percent должно быть 1, 2 или 5"
        ValueError: Для указанного n нет данных в TABLE_B2
        ValueError: Для P={p_table}% нет данных в TABLE_B3

    Returns:
        CompositeCriterion2Result: Результат проверки критерия 2. См. описание класса CompositeCriterion2Result.

    Example:
        >>> result = _criterion_b2(list(range(1, 17)), 5)
        >>> result.passed
        True
    """
    n = len(values)
    if not (15 < n <= 50):
        raise ValueError("Критерий Б.2 применим только при 15 < n <= 50")

    stats = calc_basic_stats(values)
    m, p_table = _get_b2_params(n, q_percent)

    if p_table not in TABLE_B3:
        raise ValueError(f"Для P={p_table}% нет данных в TABLE_B3")

    z_value = TABLE_B3[p_table]
    threshold = z_value * stats.S
    exceed_count = sum(1 for x in values if abs(x - stats.x_mean) > threshold)
    passed = exceed_count <= m

    return CompositeCriterion2Result(
        threshold=threshold,
        exceed_count=exceed_count,
        allowed_exceed_count=m,
        p_value_table=p_table,
        z_value=z_value,
        passed=passed,
    )


def check_normality_composite(values: list, q1_percent: int = 5, q2_percent: int = 5) -> CompositeNormalityResult:
    """
    7. Доверительные границы случайной погрешности
    7.3 При числе результатов измерений 15 < n <= 50

    Нормальность принимается только если одновременно выполнены критерий 1
    и критерий 2.

    Args:
        values (list): список результатов измерений
        q1_percent (int, optional): уровень значимости для критерия 1.
            Defaults to 5.
        q2_percent (int, optional): уровень значимости для критерия 2.
            Defaults to 5.

    Raises:
        ValueError: Составной критерий применим только при 15 < n <= 50

    Returns:
        CompositeNormalityResult: Итог проверки нормальности, содержащий
            основные статистики, результаты критериев Б.1 и Б.2 и общий
            признак `passed`. См. описание класса CompositeNormalityResult.

    Example:
        >>> result = check_normality_composite(list(range(1, 17)))
        >>> result.passed
        True
    """
    n = len(values)
    if not (15 < n <= 50):
        raise ValueError("Составной критерий применим только при 15 < n <= 50")

    stats = calc_basic_stats(values)
    c1 = _criterion_b1(values, q_percent=q1_percent)
    c2 = _criterion_b2(values, q_percent=q2_percent)

    return CompositeNormalityResult(
        n=n,
        x_mean=stats.x_mean,
        S=stats.S,
        S_biased=stats.S_biased,
        criterion_1=c1,
        criterion_2=c2,
        passed=(c1.passed and c2.passed),
    )



