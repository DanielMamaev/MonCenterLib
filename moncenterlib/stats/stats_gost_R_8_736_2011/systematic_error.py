from math import sqrt
from typeguard import typechecked
from moncenterlib.stats.stats_gost_R_8_736_2011.dataclasses import (
    SystematicComponent,
    SystematicErrorResult,
)

@typechecked
def _default_k_value(p_conf: float, m: int) -> float:
    """
    8.4 Коэффициент k для композиции НСП.

    По ГОСТ:
    - при P = 0.95 принимают k = 1.1;
    - при P = 0.99 и m > 4 принимают k = 1.4;
    - при P = 0.99 и m <= 4 коэффициент определяют по графику,
      поэтому автоматически здесь он не вычисляется.

    Args:
        p_conf (float): доверительная вероятность
        m (int): число составляющих НСП

    Raises:
        ValueError: если p_conf не поддерживается автоматически
        ValueError: если для P=0.99 и m<=4 нужен график ГОСТ

    Returns:
        float: коэффициент k
    """
    if p_conf == 0.95:
        return 1.1

    if p_conf == 0.99:
        if m > 4:
            return 1.4
        raise ValueError(
            "Для P=0.99 и m<=4 коэффициент k по ГОСТ нужно брать с графика. "
            "Передай k_value явно."
        )

    raise ValueError(
        "Автоматически поддерживаются только P=0.95 и P=0.99."
    )

@typechecked
def systematic_error_confidence(
    components: list[SystematicComponent],
    p_conf: float = 0.95,
    k_value: float | None = None,
) -> SystematicErrorResult:
    """
    8. Доверительные границы неисключенной систематической погрешности.

    Реализация пп. 8.2-8.5 ГОСТ Р 8.736-2011.

    Логика:
    - если m < 3, используется линейная сумма модулей компонент;
    - если m >= 3, используется композиция равномерно распределенных НСП:
      theta_sum = k * sqrt(sum(theta_i^2));
    - влияние входных величин учитывается через influence_coefficient.

    Args:
        components (list[SystematicComponent]): список компонент НСП
        p_conf (float, optional): доверительная вероятность. Обычно 0.95.
        k_value (float | None, optional): коэффициент k. Если не задан,
            для поддерживаемых случаев выбирается автоматически.

    Raises:
        ValueError: если число компонентов меньше 1
        ValueError: если p_conf не в интервале (0, 1)
        ValueError: если k_value <= 0

    Returns:
        SystematicErrorResult: итог расчета НСП
    """
    # НСП отсутствует или была полностью учтена ранее
    if not components:
        return SystematicErrorResult(
            m=0,
            p_conf=float(p_conf),
            k=1.0,
            theta_sum=0.0,
            method="none",
            components=[],
        )

    if not (0 < p_conf < 1):
        raise ValueError("p_conf должно быть в интервале (0, 1)")

    m = len(components)
    eff = [c.effective_theta for c in components]

    if m < 3:
        theta_sum = sum(eff)
        k = 1.0
        method = "sum"
    else:
        if k_value is None:
            k = _default_k_value(p_conf=p_conf, m=m)
        else:
            if k_value <= 0:
                raise ValueError("k_value должно быть > 0")
            k = float(k_value)

        theta_sum = k * sqrt(sum(x * x for x in eff))
        method = "rss"

    return SystematicErrorResult(
        m=m,
        p_conf=p_conf,
        k=k,
        theta_sum=theta_sum,
        method=method,
        components=components,
    )