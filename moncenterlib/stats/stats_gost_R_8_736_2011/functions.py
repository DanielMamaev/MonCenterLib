"""
text
"""

from math import sqrt
from moncenterlib.stats.stats_gost_R_8_736_2011.dataclasses import BasicStats

def calc_basic_stats(values: list) -> BasicStats:
    """
    Пункт 5. Оценка измеряемой величины и среднее квадратическое отклонение.

    Args:
        values (list): список результатов измерений

    Raises:
        ValueError: "Нужно минимум 2 значения"

    Returns:
        BasicStats: Результат расчета основных статистических характеристик выборки.
            См. описание класса BasicStats.
    Example:
        >>> result = calc_basic_stats([1.2, 1.3, 1.4, 1.5])
        >>> result.x_mean
        1.35
    """
    if len(values) < 2:
        raise ValueError("Нужно минимум 2 значения")

    n = len(values)

    # 5.1 среднее арифметическое значение исправленных результатов измерений
    x_mean = sum(values) / n

    # 5.3 Среднее квадратическое отклонение S
    S = sqrt(sum((x - x_mean) ** 2 for x in values) / (n - 1))

    # 5.4 Среднее квадратическое отклонение среднего арифметического (оценки измеряемой величины)
    S_x_mean = S / sqrt(n)

    # Приложение Б. Смещенное среднее квадратическое отклонение
    S_biased = sqrt(sum((x - x_mean) ** 2 for x in values) / n)

    return BasicStats(n=n, x_mean=x_mean, S=S, S_x_mean=S_x_mean, S_biased=S_biased)


