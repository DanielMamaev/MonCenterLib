from math import sqrt, exp, pi
from scipy.stats import chi2
from typeguard import typechecked

from moncenterlib.stats.stats_gost_R_8_736_2011.basic_stats import calc_basic_stats
from moncenterlib.stats.stats_gost_R_8_736_2011.dataclasses import PearsonInterval, PearsonNormalityResult

@typechecked
def _recommended_interval_count(n: int) -> int:
    """
    7. Доверительные границы случайной погрешности
    7.4 При числе результатов измерений n > 50

    Определить рекомендуемое число интервалов для критерия Пирсона
    в зависимости от числа результатов измерений.

    Args:
        n (int): количество результатов измерений

    Raises:
        ValueError: Для критерия Пирсона по ГОСТ ожидается n >= 40

    Returns:
        int: Рекомендуемое число интервалов по таблице В.1.

    Example:
        >>> _recommended_interval_count(40)
        8
        >>> _recommended_interval_count(600)
        13
    """
    if 40 <= n <= 100:
        return 8
    if 100 < n <= 500:
        return 10
    if 500 < n <= 1000:
        return 13
    if 1000 < n <= 10000:
        return 17
    raise ValueError("Для критерия Пирсона по ГОСТ ожидается n >= 40")

@typechecked
def _normal_pdf(y: float) -> float:
    """
    7. Доверительные границы случайной погрешности
    7.4 При числе результатов измерений n > 50

    Расчет плотности нормального распределения 

    Args:
        y (float): стандартизованная координата середины интервала

    Returns:
        float: вычисленное значение плотности нормального распределения 

    Example:
        >>> _normal_pdf(0.0)
        0.3989422804014327
    """
    return (1.0 / sqrt(2.0 * pi)) * exp(-(y ** 2) / 2.0)

@typechecked
def pearson_chi_square_normality(
    values: list,
    alpha: float = 0.05,
    r: int | None = None,
) -> PearsonNormalityResult:
    """
    7. Доверительные границы случайной погрешности
    7.4 При числе результатов измерений n > 50

    Проверка нормальности по критерию Пирсона.

    Args:
        values (list): список результатов измерений
        alpha (float, optional): уровень значимости. Defaults to 0.05.
        r (int | None, optional): число интервалов. Если не задано,
            выбирается автоматически. Defaults to None.

    Raises:
        ValueError: Критерий Пирсона по п. 7.4 применяют при n > 50
        ValueError: alpha должно быть в интервале (0, 1)
        ValueError: Среднее квадратическое отклонение S равно 0
        ValueError: Число интервалов r должно быть не меньше 4
        ValueError: Все значения одинаковы, критерий неприменим

    Returns:
        PearsonNormalityResult: Итог проверки по критерию Пирсона,
            содержащий статистику хи-квадрат, критическое значение,
            степени свободы, интервалы и признак `passed`.

    Example:
        >>> result = pearson_chi_square_normality(list(range(1, 52)))
        >>> result.passed
        True
    """
    n = len(values)
    if n <= 50:
        raise ValueError("Критерий Пирсона по п. 7.4 применяют при n > 50")

    if not (0 < alpha < 1):
        raise ValueError("alpha должно быть в интервале (0, 1)")

    stats = calc_basic_stats(values)
    x_mean = stats.x_mean
    S = stats.S

    if S == 0:
        raise ValueError("Среднее квадратическое отклонение S равно 0")

    if r is None:
        r = _recommended_interval_count(n)

    if r < 4:
        raise ValueError("Число интервалов r должно быть не меньше 4")

    x_min = min(values)
    x_max = max(values)

    if x_max == x_min:
        raise ValueError("Все значения одинаковы, критерий неприменим")

    h = (x_max - x_min) / r

    # Границы интервалов
    edges = [x_min + i * h for i in range(r + 1)]
    edges[-1] = x_max  # чтобы последний интервал точно заканчивался в xmax

    observed = [0] * r

    # Раскладываем значения по интервалам.
    # Все интервалы полуоткрытые [a, b), последний [a, b].
    for x in values:
        if x == x_max:
            observed[-1] += 1
            continue

        idx = int((x - x_min) / h)
        if idx < 0:
            idx = 0
        elif idx >= r:
            idx = r - 1
        observed[idx] += 1

    intervals: list[PearsonInterval] = []
    chi2_value = 0.0

    for i in range(r):
        left = edges[i]
        right = edges[i + 1]
        center = (left + right) / 2.0

        y = (center - x_mean) / S
        expected = n * (h / S) * _normal_pdf(y)

        if expected <= 0:
            contribution = float("inf")
        else:
            contribution = ((observed[i] - expected) ** 2) / expected

        chi2_value += contribution

        intervals.append(
            PearsonInterval(
                index=i + 1,
                left=left,
                right=right,
                center=center,
                observed=observed[i],
                expected=expected,
                y=y,
                contribution=contribution,
            )
        )

    df = r - 3
    if df <= 0:
        raise ValueError("Недопустимое число степеней свободы: df = r - 3 должно быть > 0")

    # В приложении В ГОСТ используется двусторонняя проверка:
    # статистика должна лежать между нижним и верхним квантилями.
    chi2_low = float(chi2.ppf(alpha / 2.0, df))
    chi2_high = float(chi2.ppf(1.0 - alpha / 2.0, df))
    passed = bool(chi2_low <= chi2_value <= chi2_high)

    return PearsonNormalityResult(
        n=n,
        r=r,
        h=h,
        x_mean=x_mean,
        S=S,
        chi2_value=float(chi2_value),
        df=df,
        alpha=alpha,
        chi2_low=chi2_low,
        chi2_high=chi2_high,
        passed=passed,
        intervals=intervals,
    )

