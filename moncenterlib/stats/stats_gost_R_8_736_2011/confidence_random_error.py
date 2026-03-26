from scipy.stats import t
from typeguard import typechecked
from moncenterlib.stats.stats_gost_R_8_736_2011.dataclasses import RandomErrorConfidenceResult
from moncenterlib.stats.stats_gost_R_8_736_2011.basic_stats import calc_basic_stats


@typechecked
def _student_t_value(p_conf: float, n: int) -> float:
    """
    Приложение Д. Коэффициент Стьюдента t
    для доверительной вероятности P и числа результатов измерений n.

    Args:
        p_conf (float): доверительная вероятность, например 0.95 или 0.99
        n (int): число результатов измерений

    Raises:
        ValueError: n должно быть не меньше 2
        ValueError: p_conf должно быть в интервале (0, 1)

    Returns:
        float: коэффициент Стьюдента t
    """
    if n < 2:
        raise ValueError("n должно быть не меньше 2")
    if not (0 < p_conf < 1):
        raise ValueError("p_conf должно быть в интервале (0, 1)")

    df = n - 1
    # Двусторонний доверительный интервал:
    # P(|T| <= t) = p_conf
    return float(t.ppf((1.0 + p_conf) / 2.0, df=df))

@typechecked
def confidence_random_error(
    values: list,
    p_conf: float = 0.95,
) -> RandomErrorConfidenceResult:
    """
    7.5 Доверительные границы случайной погрешности измеряемой величины.

    Вычисляет доверительную границу случайной погрешности по формуле:
        delta = t * S_x_mean

    Args:
        values (list[float]): список результатов измерений
        p_conf (float, optional): доверительная вероятность P. Defaults to 0.95.

    Raises:
        ValueError: n должно быть не меньше 2
        ValueError: p_conf должно быть в интервале (0, 1)
        ValueError: Среднее квадратическое отклонение S_x_mean равно 0

    Returns:
        RandomErrorConfidenceResult: результат расчета по п. 7.5

    Example:
        >>> result = confidence_random_error([10.1, 10.2, 10.0, 10.3], p_conf=0.95)
        >>> result.delta
        0.2
    """
    stats = calc_basic_stats(values)

    if stats.S_x_mean == 0:
        raise ValueError("Среднее квадратическое отклонение S_x_mean равно 0")

    t_value = _student_t_value(p_conf=p_conf, n=stats.n)
    delta = t_value * stats.S_x_mean

    return RandomErrorConfidenceResult(
        n=stats.n,
        p_conf=p_conf,
        df=stats.n - 1,
        x_mean=stats.x_mean,
        S=stats.S,
        S_x_mean=stats.S_x_mean,
        t_value=t_value,
        delta=delta,
    )