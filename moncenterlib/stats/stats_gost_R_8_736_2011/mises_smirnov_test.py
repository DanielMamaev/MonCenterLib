from math import sqrt, erf, log
from typeguard import typechecked
from moncenterlib.stats.stats_gost_R_8_736_2011.tables import TABLE_G3
from moncenterlib.stats.stats_gost_R_8_736_2011.dataclasses import MisesSmirnovNormalityResult, MisesSmirnovRow
from moncenterlib.stats.stats_gost_R_8_736_2011.basic_stats import calc_basic_stats


@typechecked
def _normal_cdf(x: float, mean: float, std: float) -> float:
    """
    Нормальная функция распределения F(x) для N(mean, std^2).
    """
    z = (x - mean) / (std * sqrt(2.0))
    return 0.5 * (1.0 + erf(z))

@typechecked
def _get_g3_value(x: float) -> float:
    """
    Получить значение a(x) по таблице Г.3.
    Если x попадает между узлами таблицы, используется линейная интерполяция.

    Для x <= 0 возвращается 0.0.
    Для x >= 2.59 возвращается последнее табличное значение 0.956.
    """
    if x <= 0.0:
        return 0.0

    max_x = max(TABLE_G3.keys())
    if x >= max_x:
        return TABLE_G3[max_x]

    x1 = int(x * 100) / 100.0
    x2 = round(x1 + 0.01, 2)

    y1 = TABLE_G3[round(x1, 2)]
    y2 = TABLE_G3[round(x2, 2)]

    if x2 == x1:
        return y1

    k = (x - x1) / (x2 - x1)
    return y1 + k * (y2 - y1)

@typechecked
def mises_smirnov_omega2_normality(
    values: list,
    alpha: float = 0.1,
) -> MisesSmirnovNormalityResult:
    """
    Приложение Г. Проверка гипотезы о нормальности распределения
    результатов измерений при n > 50 по критерию ω² Мизеса—Смирнова.

    По ГОСТ после вычисления статистики nΩ² по формуле (Г.1)
    по таблице Г.3 определяют значение a(x) и сравнивают его с 1 - alpha:
    - если a(x) > 1 - alpha, гипотезу отвергают;
    - если a(x) <= 1 - alpha, гипотезу не отвергают.

    Args:
        values (list[float]): список результатов измерений
        alpha (float, optional): уровень значимости. Обычно 0.1 или 0.2.

    Raises:
        ValueError: Критерий ω² по приложению Г применим только при n > 50
        ValueError: alpha должно быть в интервале (0, 1)
        ValueError: Среднее квадратическое отклонение S равно 0

    Returns:
        MisesSmirnovNormalityResult: итог проверки и промежуточные значения.

    Example:
        >>> result = mises_smirnov_omega2_normality(list(range(1, 60)))
        >>> result.passed
        True
    """
    n = len(values)
    if n <= 50:
        raise ValueError("Критерий ω² по приложению Г применим только при n > 50")

    if not (0 < alpha < 1):
        raise ValueError("alpha должно быть в интервале (0, 1)")

    stats = calc_basic_stats(values)
    x_mean = stats.x_mean
    S = stats.S

    if S == 0:
        raise ValueError("Среднее квадратическое отклонение S равно 0")

    sorted_values = sorted(values)

    # Защита от log(0)
    eps = 1e-15

    rows: list[MisesSmirnovRow] = []
    total = 0.0

    for j, x_j in enumerate(sorted_values, start=1):
        F_xj = _normal_cdf(x_j, x_mean, S)
        F_xj = min(max(F_xj, eps), 1.0 - eps)

        a_j = (2.0 * j - 1.0) / (2.0 * n)

        ln_F_xj = log(F_xj)
        one_minus_a_j = 1.0 - a_j
        one_minus_F_xj = 1.0 - F_xj
        ln_one_minus_F_xj = log(one_minus_F_xj)

        term = a_j * ln_F_xj + one_minus_a_j * ln_one_minus_F_xj
        total += term

        rows.append(
            MisesSmirnovRow(
                j=j,
                x_j=x_j,
                F_xj=F_xj,
                a_j=a_j,
                ln_F_xj=ln_F_xj,
                one_minus_a_j=one_minus_a_j,
                one_minus_F_xj=one_minus_F_xj,
                ln_one_minus_F_xj=ln_one_minus_F_xj,
                term=term,
            )
        )

    n_omega2 = -n - 2.0 * total
    a_value = _get_g3_value(n_omega2)
    threshold = 1.0 - alpha
    passed = a_value <= threshold

    return MisesSmirnovNormalityResult(
        n=n,
        x_mean=x_mean,
        S=S,
        alpha=alpha,
        threshold=threshold,
        n_omega2=n_omega2,
        a_value=a_value,
        passed=passed,
        rows=rows,
    )