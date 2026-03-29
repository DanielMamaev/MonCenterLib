from decimal import Decimal, ROUND_HALF_UP
from math import floor, log10, isfinite

from typeguard import typechecked

from moncenterlib.stats.stats_gost_R_8_736_2011.dataclasses import (
    RoundedMeasurementResult,
)

@typechecked
def _round_half_up(value: float, decimal_places: int) -> float:
    """
    Округление по правилу >= 5 вверх.
    Это соответствует приложению Е, п. Е.5.
    """
    q = Decimal("1e{}".format(-decimal_places))
    d = Decimal(str(value)).quantize(q, rounding=ROUND_HALF_UP)
    return float(d)

@typechecked
def _significant_exponent(value: float) -> int:
    """
    Возвращает порядок числа:
        123.4 -> 2
        12.34 -> 1
        1.234 -> 0
        0.1234 -> -1
    """
    if value <= 0:
        raise ValueError("value должно быть > 0")
    return int(floor(log10(value)))

@typechecked
def _first_significant_digit(value: float) -> int:
    """
    Первая значащая цифра положительного числа.
        0.038 -> 3
        12.5 -> 1
        487 -> 4
    """
    exp = _significant_exponent(value)
    scaled = value / (10 ** exp)
    return int(floor(scaled))

@typechecked
def _error_significant_digits(
    delta: float,
    precise_measurement: bool = False,
) -> int:
    """
    Приложение Е, п. Е.2.

    По умолчанию:
    - сохраняем 1 значащую цифру;
    - сохраняем 2 значащие цифры, если первая значащая цифра <= 3;
    - также 2 значащие цифры можно сохранять для точных измерений.
    """
    if delta <= 0:
        raise ValueError("delta должно быть > 0")

    first_digit = _first_significant_digit(delta)

    if precise_measurement:
        return 2

    if first_digit <= 3:
        return 2

    return 1

@typechecked
def round_to_significant_digits(value: float, sig_digits: int) -> float:
    """
    Округляет число до sig_digits значащих цифр.
    """
    if sig_digits < 1:
        raise ValueError("sig_digits должно быть >= 1")
    if value == 0:
        return 0.0
    if not isfinite(value):
        raise ValueError("value должно быть конечным числом")

    sign = -1.0 if value < 0 else 1.0
    value = abs(value)

    exp = _significant_exponent(value)
    decimal_places = sig_digits - exp - 1

    rounded = _round_half_up(value, decimal_places)
    return sign * rounded

@typechecked
def _decimal_places_from_error(delta_rounded: float) -> int:
    """
    Определяет, до какого разряда надо округлять x,
    чтобы он оканчивался цифрой того же разряда, что и Δ.

    Примеры:
        0.12  -> 2
        0.1   -> 1
        12    -> -0  (округление до целых)
        120   -> -1  (до десятков)
    """
    if delta_rounded <= 0:
        raise ValueError("delta_rounded должно быть > 0")

    exp = _significant_exponent(delta_rounded)

    # число знаков после запятой в последнем значащем разряде
    # для уже округленного delta.
    if exp >= 0:
        # 12, 120, 500 ...
        # exp=1 => десятки, exp=2 => сотни
        return -exp if delta_rounded == int(delta_rounded) and str(int(delta_rounded)).endswith("0") else 0

    # 0.12 -> exp=-1, нужно 2 знака
    return -exp

@typechecked
def _last_place_decimal_places(delta_raw: float, sig_digits: int) -> int:
    """
    Более надежно определяет разряд последней сохраняемой цифры Δ
    до фактического округления x.

    decimal_places:
        > 0  -> число знаков после запятой
        = 0  -> до целых
        < 0  -> до десятков, сотен и т.д.
    """
    exp = _significant_exponent(delta_raw)
    return sig_digits - exp - 1

@typechecked
def _format_number(value: float, decimal_places: int) -> str:
    """
    Форматирует число с фиксированным количеством знаков после запятой,
    если decimal_places >= 0.
    Если decimal_places < 0, число уже должно быть округлено до нужного разряда,
    и выводим его без дробной части.
    """
    if decimal_places >= 0:
        return f"{value:.{decimal_places}f}"

    return f"{int(value):d}"

@typechecked
def format_measurement_result(
    x: float,
    delta: float,
    p_conf: float = 0.95,
    precise_measurement: bool = False,
) -> RoundedMeasurementResult:
    """
    10.3 + Приложение Е.

    Формирует окончательную запись результата измерения:
        x ± Δ, P=...

    Логика:
    1) Δ округляется по приложению Е;
    2) x округляется до того же разряда, что и Δ;
    3) возвращается готовая запись.

    Args:
        x (float): оценка измеряемой величины
        delta (float): погрешность без учета знака
        p_conf (float, optional): доверительная вероятность
        precise_measurement (bool, optional):
            True -> сохранять 2 значащие цифры в Δ как для точных измерений

    Returns:
        RoundedMeasurementResult: итог округления и готовая запись
    """
    if not isfinite(x):
        raise ValueError("x должно быть конечным числом")
    if not isfinite(delta) or delta <= 0:
        raise ValueError("delta должно быть положительным конечным числом")
    if not (0 < p_conf < 1):
        raise ValueError("p_conf должно быть в интервале (0, 1)")

    delta_sig_digits = _error_significant_digits(
        delta=delta,
        precise_measurement=precise_measurement,
    )

    delta_rounded = round_to_significant_digits(delta, delta_sig_digits)

    decimal_places = _last_place_decimal_places(delta, delta_sig_digits)
    x_rounded = _round_half_up(x, decimal_places)

    x_str = _format_number(x_rounded, decimal_places)
    delta_str = _format_number(delta_rounded, decimal_places)

    notation = f"{x_str} ± {delta_str}, P={p_conf:g}"

    return RoundedMeasurementResult(
        x_raw=float(x),
        delta_raw=float(delta),
        p_conf=float(p_conf),
        x_rounded=float(x_rounded),
        delta_rounded=float(delta_rounded),
        delta_significant_digits=delta_sig_digits,
        decimal_places=decimal_places,
        notation=notation,
    )

@typechecked
def format_measurement_components(
    x: float,
    s_x_mean: float,
    n: int,
    theta: float,
    p_conf: float | None = None,
) -> str:
    """
    Clause 10.4. Formatting for further processing of results.

    Output format:
        ``x; S_x_mean; n; Theta``

    If necessary, the confidence probability ``P`` is also included.
    """
    if n < 1:
        raise ValueError("n должно быть >= 1")
    if s_x_mean < 0:
        raise ValueError("s_x_mean должно быть >= 0")
    if theta < 0:
        raise ValueError("theta должно быть >= 0")

    result = f"x={x}; S_x_mean={s_x_mean}; n={n}; Theta={theta}"

    if p_conf is not None:
        if not (0 < p_conf < 1):
            raise ValueError("p_conf должно быть в интервале (0, 1)")
        result += f"; P={p_conf:g}"

    return result
