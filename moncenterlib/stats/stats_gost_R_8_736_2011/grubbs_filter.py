
from math import sqrt
from scipy.stats import t
from typeguard import typechecked
from moncenterlib.stats.stats_gost_R_8_736_2011.dataclasses import GrubbsCheck, GrubbsResult
from moncenterlib.stats.stats_gost_R_8_736_2011.basic_stats import calc_basic_stats

@typechecked
def _grubbs_critical_value(n, alpha=0.05) -> float:
    """
    Вычисление критического значения через распределение Стьюдента.
    На основе этого формируется таблица критических значений G_T для критерия Граббса.
    Таблицу А.1 можно не использовать.
    alpha = 0.01, если очень осторожно удалять выбросы.
    alpha = 0.05, стандартное значение 

    Raises:
        ValueError: "Для критерия Граббса нужно минимум 3 значения"
        ValueError: "alpha должно быть в интервале (0, 1)"

    Returns:
        float: Критическое значение критерия Граббса для заданного числа результатов измерений и уровня значимости alpha.
    
    Example:
        >>> _grubbs_critical_value(5)
        1.7
    """
    if n < 3:
        raise ValueError("Для критерия Граббса нужно минимум 3 значения")
    if not (0 < alpha < 1):
        raise ValueError("alpha должно быть в интервале (0, 1)")

    t_value = t.ppf(1 - alpha / (2 * n), df=n - 2)
    return ((n - 1) / sqrt(n)) * sqrt(t_value**2 / (n - 2 + t_value**2))

@typechecked
def grubbs_filter(values: list, alpha: float = 0.05) -> GrubbsResult:
    """
    Пункт 6. Исключение грубых погрешностей.
    Итеративное удаление выбросов по критерию Граббса.
    alpha = 0.01, если очень осторожно удалять выбросы.
    alpha = 0.05, стандартное значение 

    Args:
        values (list): список результатов измерений
        alpha (float, optional): Уровень значимости. Defaults to 0.05.

    Returns:
        GrubbsResult: Результат фильтрации, содержащий очищенный список значений,
        удаленные выбросы и результаты каждой итерации проверки по критерию Граббса.
        См. описание класса GrubbsResult
    
    Example:
        >>> result = grubbs_filter([10.1, 10.2, 10.3, 15.0])
        >>> result.cleaned_values
        [10.1, 10.2, 10.3]
    """

    data = list(values)
    removed: list = []
    checks: list[GrubbsCheck] = []

    while True:
        n = len(data)
        if n < 3:
            break

        stats = calc_basic_stats(data)
        x_mean = stats.x_mean

        if stats.S == 0:
            break

        x_min = min(data)
        x_max = max(data)
        g_min = abs(x_mean - x_min) / stats.S
        g_max = abs(x_max - x_mean) / stats.S
        g_crit = _grubbs_critical_value(n, alpha=alpha)

        checks.append(
            GrubbsCheck(
                n=n,
                x_mean=x_mean,
                S=stats.S,
                x_min=x_min,
                x_max=x_max,
                g_min=g_min,
                g_max=g_max,
                g_crit=g_crit,
            )
        )

        remove_min = g_min > g_crit
        remove_max = g_max > g_crit

        if not (remove_min or remove_max):
            break

        if remove_max and remove_min:
            if g_max >= g_min:
                data.remove(x_max)
                removed.append(x_max)
            else:
                data.remove(x_min)
                removed.append(x_min)
        elif remove_max:
            data.remove(x_max)
            removed.append(x_max)
        else:
            data.remove(x_min)
            removed.append(x_min)

    return GrubbsResult(cleaned_values=data, removed=removed, checks=checks)
