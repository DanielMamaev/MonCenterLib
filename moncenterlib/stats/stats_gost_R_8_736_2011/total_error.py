from math import sqrt

from typeguard import typechecked

from moncenterlib.stats.stats_gost_R_8_736_2011.dataclasses import (
    RandomErrorConfidenceResult,
    TotalErrorResult,
)

@typechecked
def _systematic_std(
    theta: float,
    theta_mode: str,
    theta_k: float | None,
) -> float:
    """
    9.1 Формулы (14) и (15).

    Args:
        theta (float): граница НСП без учета знака
        theta_mode (str): 'plain' или 'confidence'
        theta_k (float | None): коэффициент k из шага 8, если theta_mode='confidence'

    Returns:
        float: СКО НСП
    """
    theta = abs(float(theta))

    if theta_mode == "plain":
        # Формула (14)
        return theta / sqrt(3.0)

    if theta_mode == "confidence":
        # Формула (15)
        if theta_k is None or theta_k <= 0:
            raise ValueError(
                "Для theta_mode='confidence' нужно передать положительный theta_k"
            )
        return theta / (float(theta_k) * sqrt(3.0))

    raise ValueError("theta_mode должно быть 'plain' или 'confidence'")

@typechecked
def total_error_confidence(
    random_result: RandomErrorConfidenceResult,
    theta_systematic: float = 0.0,
    theta_mode: str = "plain",
    theta_k: float | None = None,
) -> TotalErrorResult:
    """
    9. Доверительные границы погрешности оценки измеряемой величины.

    Реализация формул (12)-(15) ГОСТ Р 8.736-2011.

    Args:
        random_result (RandomErrorConfidenceResult): результат шага 7.5
        theta_systematic (float, optional): граница НСП без учета знака
        theta_mode (str, optional):
            - 'plain'      -> НСП получена как обычная граница, формула (14)
            - 'confidence' -> НСП получена как доверительная граница, формула (15)
        theta_k (float | None, optional): коэффициент k из шага 8 для режима 'confidence'

    Returns:
        TotalErrorResult: итог шага 9
    """
    delta_random = abs(float(random_result.delta))
    s_x_mean = float(random_result.S_x_mean)
    theta_systematic = abs(float(theta_systematic))

    # Если НСП отсутствует, итоговая погрешность равна случайной.
    if theta_systematic == 0.0:
        return TotalErrorResult(
            p_conf=random_result.p_conf,
            x_mean=random_result.x_mean,
            delta_random=delta_random,
            theta_systematic=0.0,
            s_x_mean=s_x_mean,
            s_theta=0.0,
            s_total=s_x_mean,
            k_total=random_result.t_value,
            delta_total=delta_random,
            theta_mode=theta_mode,
            theta_k=theta_k,
        )

    s_theta = _systematic_std(
        theta=theta_systematic,
        theta_mode=theta_mode,
        theta_k=theta_k,
    )

    s_total = sqrt(s_x_mean ** 2 + s_theta ** 2)

    denominator = s_x_mean + s_theta
    if denominator == 0:
        raise ValueError("Сумма S_x_mean + S_theta не должна быть равна 0")

    # Эмпирическая формула (16)
    k_total = (delta_random + theta_systematic) / denominator

    delta_total = k_total * s_total

    return TotalErrorResult(
        p_conf=random_result.p_conf,
        x_mean=random_result.x_mean,
        delta_random=delta_random,
        theta_systematic=theta_systematic,
        s_x_mean=s_x_mean,
        s_theta=s_theta,
        s_total=s_total,
        k_total=k_total,
        delta_total=delta_total,
        theta_mode=theta_mode,
        theta_k=theta_k,
    )