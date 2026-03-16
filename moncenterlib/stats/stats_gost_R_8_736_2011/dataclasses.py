from dataclasses import dataclass


@dataclass
class BasicStats:
    """
    5. Оценка измеряемой величины и среднее квадратическое отклонение.
        - n - количество результатов измерений
        - x_mean - среднее арифметческое значение
        - S - Среднее квадратическое отклонение S 
        - S_x_mean - среднее квадратическое отклонение среднего арифметического
        - S_biased - смещенное среднее квадратическое отклонение S* 
    """
    n: int
    x_mean: float
    S: float
    S_x_mean: float
    S_biased: float


@dataclass
class GrubbsCheck:
    """
    6. Исключение грубых погрешностей.
        - n - количество результатов измерений
        - x_mean - среднее арифметческое значение
        - S - среднее квадратическое отклонение S
        - x_min - минимальный результат измерений
        - x_max - максимальный результат измерений
        - g_min - вычисленный критерий Граббса для минимального результата измерения
        - g_max - вычисленный критерий Граббса для максимального результата измерения
        - g_crit - теоретический критерий Граббса
    """
    n: int
    x_mean: float
    S: float
    x_min: float
    x_max: float
    g_min: float
    g_max: float
    g_crit: float


@dataclass
class GrubbsResult:
    """
    6. Исключение грубых погрешностей.
        - cleaned_values - список отфильтрованных результатов измерений
        - removed - список удаленных результатов измерений
        - checks - список результатов каждой итерации проверки по критерию Граббса.
    """
    cleaned_values: list
    removed: list
    checks: list[GrubbsCheck]


@dataclass
class CompositeCriterion1Result:
    """
    7. Доверительные границы случайной погрешности.
    7.3 При числе результатов измерений 15 < n <= 50.
    Критерий 1, приложение Б.
        - d - отношение d~
        - d_low - нижний квантиль распределения
        - d_high - верхний квантиль распределения
        - passed - результат проверки критерия: True, если критерий выполнен, иначе False
    """
    d: float
    d_low: float
    d_high: float
    passed: bool


@dataclass
class CompositeCriterion2Result:
    """
    7. Доверительные границы случайной погрешности.
    7.3 При числе результатов измерений 15 < n <= 50.
    Критерий 2, приложение Б.
        - threshold - пороговое значение z_p/2 * S
        - exceed_count - количество |x_i - x_mean|, которые превысили порог threshold
        - allowed_exceed_count - значение m разностей из таблицы Б.2
        - p_value_table - значение вероятности из таблицы Б.2
        - z_value - верхний квантиль распределения нормированной функции Лапласа, таблица Б.3
        - passed - результат проверки критерия: True, если критерий выполнен, иначе False
    """
    threshold: float
    exceed_count: int
    allowed_exceed_count: int
    p_value_table: float
    z_value: float
    passed: bool


@dataclass
class CompositeNormalityResult:
    """
    7. Доверительные границы случайной погрешности.
    7.3 При числе результатов измерений 15 < n <= 50.
    Результат проверки гипотезы о нормальности распределения результатов измерений.
        - n - количество результатов измерений
        - x_mean - среднее арифметическое значение
        - S - среднее квадратическое отклонение S
        - S_biased - ссмещенное среднее квадратическое отклонение S*
        - criterion_1 - результат проверки по критерию 1 приложения Б
        - criterion_2 - результат проверки по критерию 2 приложения Б
        - passed - булев признак того, что оба критерия выполнены
    """
    n: int
    x_mean: float
    S: float
    S_biased: float
    criterion_1: CompositeCriterion1Result
    criterion_2: CompositeCriterion2Result
    passed: bool


@dataclass
class PearsonInterval:
    """
    7. Доверительные границы случайной погрешности.
    7.4 При числе результатов измерений n > 50.
        - index - номер интервала i
        - left - левая граница интервала
        - right - правая граница интервала
        - center - середина интервала x_i0
        - observed - число  результатов  измерений, попавших  в  каждый интервал, ~n_i
        - expected - число результатов измерений, которое должно было бы нахо­диться в интервале, n_i
        - y - вероятность попадания результатов измерений в i-й интервал
        - contribution - вычисленное значение К. Пирсона
    """
    index: int
    left: float
    right: float
    center: float
    observed: int
    expected: float
    y: float
    contribution: float


@dataclass
class PearsonNormalityResult:
    """
    7. Доверительные границы случайной погрешности.
    7.4 При числе результатов измерений n > 50.
    Результат проверки гипотезы о нормальности распределения результатов измерений.
        - n - количество результатов измерений
        - r - число интервалов группировки
        - h - ширина интервала группировки
        - x_mean - среднее арифметическое значение
        - S - среднее квадратическое отклонение S
        - chi2_value - вычисленное значение критерия Пирсона
        - df - число степеней свободы
        - alpha - уровень значимости
        - chi2_low - нижняя критическая граница для критерия chi^2
        - chi2_high - верхняя критическая граница для критерия chi^2
        - passed - булев признак того, что гипотеза о нормальности не отвергается
        - intervals - список интервалов группировки и параметров расчета критерия Пирсона
    """
    n: int
    r: int
    h: float
    x_mean: float
    S: float
    chi2_value: float
    df: int
    alpha: float
    chi2_low: float
    chi2_high: float
    passed: bool
    intervals: list[PearsonInterval]


@dataclass
class MisesSmirnovRow:
    """
    Приложение Г. Промежуточные значения для расчета критерия ω².
        - j - номер упорядоченного результата измерения
        - x_j - значение результата измерения
        - a_j - коэффициент (2j - 1) / (2n)
        - F_xj - значение теоретической функции нормального распределения F(x_j)
        - ln_F_xj - ln(F(x_j))
        - one_minus_a_j - 1 - a_j
        - one_minus_F_xj - 1 - F(x_j)
        - ln_one_minus_F_xj - ln(1 - F(x_j))
        - term - слагаемое под суммой в формуле (Г.1)
    """
    j: int
    x_j: float
    a_j: float
    F_xj: float
    ln_F_xj: float
    one_minus_a_j: float
    one_minus_F_xj: float
    ln_one_minus_F_xj: float
    term: float

@dataclass
class MisesSmirnovNormalityResult:
    """
    Приложение Г. Результат проверки нормальности по критерию ω².
        - n - число результатов измерений
        - x_mean - среднее арифметическое
        - S - среднее квадратическое отклонение результатов измерений
        - n_omega2 - вычисленное значение статистики nΩ²
        - a_value - значение функции a(x) из таблицы Г.3
        - alpha - уровень значимости
        - threshold = 1 - alpha
        - passed - True, если гипотеза о нормальности не отвергается
        - rows - промежуточные строки расчета
    """
    n: int
    x_mean: float
    S: float
    n_omega2: float
    a_value: float
    alpha: float
    threshold: float
    passed: bool
    rows: list[MisesSmirnovRow]


@dataclass
class RandomErrorConfidenceResult:
    """
    7.5 Доверительные границы случайной погрешности
        - n - количество результатов измерений
        - p_conf - доверительная вероятность P
        - df - число степеней свободы n - 1
        - x_mean - среднее арифметическое значение
        - S - среднее квадратическое отклонение S
        - S_x_mean - среднее квадратическое отклонение среднего арифметического
        - t_value - коэффициент Стьюдента
        - delta - доверительная граница случайной погрешности без учета знака
    """
    n: int
    p_conf: float
    df: int
    x_mean: float
    S: float
    S_x_mean: float
    t_value: float
    delta: float

@dataclass
class SystematicComponent:
    """
    8. Доверительные границы неисключенной систематической погрешности.

    Один компонент НСП.
        - name - имя компонента
        - theta - граница компонента НСП без учета знака
        - influence_coefficient - коэффициент влияния dX/dY.
          Если не задан, считается равным 1.
        - effective_theta - приведенная граница компонента:
          |influence_coefficient| * |theta|
    """
    name: str
    theta: float
    influence_coefficient: float = 1.0

    @property
    def effective_theta(self) -> float:
        return abs(self.influence_coefficient) * abs(self.theta)


@dataclass
class SystematicErrorResult:
    """
    8. Доверительные границы неисключенной систематической погрешности.

        - m - число составляющих НСП
        - p_conf - доверительная вероятность
        - k - коэффициент композиции
        - theta_sum - итоговая граница НСП без учета знака
        - method - способ расчета: 'sum' или 'rss'
        - components - список компонентов
    """
    m: int
    p_conf: float
    k: float
    theta_sum: float
    method: str
    components: list[SystematicComponent]


@dataclass
class TotalErrorResult:
    """
    9. Доверительные границы погрешности оценки измеряемой величины.

        - p_conf - доверительная вероятность
        - x_mean - оценка измеряемой величины
        - delta_random - доверительная граница случайной погрешности
        - theta_systematic - граница НСП
        - s_x_mean - СКО среднего арифметического
        - s_theta - СКО НСП
        - s_total - суммарное СКО оценки измеряемой величины
        - k_total - коэффициент K из формулы (12)
        - delta_total - итоговая доверительная граница погрешности
        - theta_mode - способ интерпретации НСП:
          'plain' -> формула (14)
          'confidence' -> формула (15)
        - theta_k - коэффициент k шага 8, нужен только для режима 'confidence'
    """
    p_conf: float
    x_mean: float
    delta_random: float
    theta_systematic: float
    s_x_mean: float
    s_theta: float
    s_total: float
    k_total: float
    delta_total: float
    theta_mode: str
    theta_k: float | None = None

@dataclass
class RoundedMeasurementResult:
    """
    10. Форма записи оценки измеряемой величины.
    Приложение Е. Правила округления.

        - x_raw - исходная оценка измеряемой величины
        - delta_raw - исходная погрешность без учета знака
        - p_conf - доверительная вероятность
        - x_rounded - округленная оценка измеряемой величины
        - delta_rounded - округленная погрешность
        - delta_significant_digits - число значащих цифр, сохраненных в погрешности
        - decimal_places - число знаков после запятой для окончательной записи
        - notation - готовая запись результата вида "x ± Δ, P=..."
    """
    x_raw: float
    delta_raw: float
    p_conf: float
    x_rounded: float
    delta_rounded: float
    delta_significant_digits: int
    decimal_places: int
    notation: str
