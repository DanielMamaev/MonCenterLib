from pathlib import Path
from typing import Any
from typeguard import typechecked
from moncenterlib.stats.stats_gost_R_8_736_2011.basic_stats import calc_basic_stats
from moncenterlib.stats.stats_gost_R_8_736_2011.grubbs_filter import grubbs_filter
from moncenterlib.stats.stats_gost_R_8_736_2011.composite_test import check_normality_composite
from moncenterlib.stats.stats_gost_R_8_736_2011.pearson_test import pearson_chi_square_normality
from moncenterlib.stats.stats_gost_R_8_736_2011.mises_smirnov_test import mises_smirnov_omega2_normality
from moncenterlib.stats.stats_gost_R_8_736_2011.confidence_random_error import confidence_random_error
from moncenterlib.stats.stats_gost_R_8_736_2011.systematic_error import systematic_error_confidence
from moncenterlib.stats.stats_gost_R_8_736_2011.total_error import total_error_confidence
from moncenterlib.stats.stats_gost_R_8_736_2011.result_formatting import format_measurement_result

@typechecked
def _calculate(values: list, config: dict):
    result_object = []

    # Шаг 5
    result_basic_stats = calc_basic_stats(values)
    result_object.append(result_basic_stats)

    # Шаг 6
    result_grubbs = grubbs_filter(values, config["alpha_grubbs"])
    result_object.append(result_grubbs)

    cleaned_values = result_grubbs.cleaned_values
    n_clean = len(cleaned_values)

    # Шаг 7.3 / 7.4 — проверка нормальности
    result_normality = None
    result_pearson = None
    result_smirnov = None
    normality_mode = None

    if n_clean <= 15:
        normality_mode = "assumed"
        if not config.get("normal_n<15", False):
            raise ValueError(
                "Для n <= 15 по ГОСТ расчет случайной погрешности допустим "
                "только если заранее известно, что распределение нормальное."
            )

    elif 15 < n_clean <= 50:
        normality_mode = "composite"
        result_normality = check_normality_composite(cleaned_values, config["normality_composite_q1"], config["normality_composite_q2"])
        result_object.append(result_normality)

        if not result_normality.passed:
            raise ValueError(
                "Составной критерий нормальности не пройден. "
                "По ГОСТ дальнейший расчет случайной погрешности по этой схеме недопустим."
            )

    else:  # n_clean > 50
        normality_mode = "pearson_smirnov"
        result_pearson = pearson_chi_square_normality(cleaned_values, alpha=config["alpha_pearson"], r=config["r_pearson"])
        result_smirnov = mises_smirnov_omega2_normality(cleaned_values, alpha=config["alpha_smirnov"])
        result_object.append(result_pearson)
        result_object.append(result_smirnov)

        if not (result_pearson.passed or result_smirnov.passed):
            raise ValueError(
                "Гипотеза о нормальности не подтверждена ни критерием Пирсона, "
                "ни критерием Мизеса–Смирнова."
            )

    # Шаг 7.5
    result_random_error = confidence_random_error(cleaned_values, p_conf=config["random_error_p_conf"])
    result_object.append(result_random_error)

    # Шаг 8
    if config["random_error_p_conf"] != config["systematic_error_p_conf"]:
        raise ValueError(
            "random_error_p_conf и systematic_error_p_conf должны совпадать"
        )
    result_systematic_error = systematic_error_confidence(components=config["systematic_components"], p_conf=config["systematic_error_p_conf"], k_value=config["systematic_error_k"])
    result_object.append(result_systematic_error)

    # Подготовка параметров для шага 9
    if result_systematic_error.method == "none":
        theta_mode = "plain"
        theta_k = None
    elif result_systematic_error.method == "sum":
        theta_mode = "plain"
        theta_k = None
    elif result_systematic_error.method == "rss":
        theta_mode = "confidence"
        theta_k = result_systematic_error.k
    else:
        raise ValueError(
            f"Неизвестный method у systematic_error_confidence: "
            f"{result_systematic_error.method}"
        )

    # Шаг 9
    result_total_error = total_error_confidence(random_result=result_random_error, theta_systematic=result_systematic_error.theta_sum, theta_mode=theta_mode, theta_k=theta_k)
    result_object.append(result_total_error)

    # Шаг 10
    result_formatted = format_measurement_result(x=result_total_error.x_mean, delta=result_total_error.delta_total, p_conf=result_total_error.p_conf)
    result_object.append(result_formatted)

    return {
        "basic_stats": result_basic_stats,
        "grubbs": result_grubbs,
        "n_clean": n_clean,
        "normality_mode": normality_mode,
        "normality": result_normality,
        "pearson": result_pearson,
        "smirnov": result_smirnov,
        "random_error": result_random_error,
        "systematic_error": result_systematic_error,
        "total_error": result_total_error,
        "formatted_result": result_formatted,
        "all_steps": result_object,
    }

@typechecked
def _bool_text(value: bool) -> str:
    return "Да" if value else "Нет"

@typechecked
def _fmt(value: Any, digits: int = 6) -> str:
    if isinstance(value, bool):
        return _bool_text(value)
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    if value is None:
        return "None"
    return str(value)

@typechecked
def _safe_getattr(obj: Any, attr: str, default=None):
    return getattr(obj, attr, default)

@typechecked
def _build_protocol_text(result: dict) -> str:
    """
    Формирует подробный текстовый протокол по всем шагам обработки результатов измерений.
    """

    basic = result["basic_stats"]
    grubbs = result["grubbs"]
    n_clean = result.get("n_clean", len(grubbs.cleaned_values))

    normality_mode = result.get("normality_mode")
    normality = result.get("normality")
    pearson = result.get("pearson")
    smirnov = result.get("smirnov")

    random_error = result["random_error"]
    systematic_error = result["systematic_error"]
    total_error = result["total_error"]
    formatted_result = result["formatted_result"]

    lines: list[str] = []

    lines.append("ПРОТОКОЛ ОБРАБОТКИ РЕЗУЛЬТАТОВ ИЗМЕРЕНИЙ ПО ГОСТ Р 8.736-2011")
    lines.append("=" * 78)
    lines.append("")

    if "input_values" in result:
        lines.append("Исходные результаты измерений")
        lines.append("-" * 78)
        lines.append(", ".join(_fmt(x) for x in result["input_values"]))
        lines.append("")

    if "config" in result:
        lines.append("Параметры расчета")
        lines.append("-" * 78)
        for key, value in result["config"].items():
            lines.append(f"{key} = {value}")
        lines.append("")

    lines.append("Шаг 5. Оценка измеряемой величины и среднего квадратического отклонения")
    lines.append("-" * 78)
    lines.append(f"n = {_fmt(_safe_getattr(basic, 'n'))}")
    lines.append(f"x_mean = {_fmt(_safe_getattr(basic, 'x_mean'))}")
    lines.append(f"S = {_fmt(_safe_getattr(basic, 'S'))}")
    lines.append(f"S_x_mean = {_fmt(_safe_getattr(basic, 'S_x_mean'))}")
    lines.append(f"S_biased = {_fmt(_safe_getattr(basic, 'S_biased'))}")
    lines.append("")

    lines.append("Шаг 6. Исключение грубых погрешностей по критерию Граббса")
    lines.append("-" * 78)
    checks = _safe_getattr(grubbs, "checks", [])
    lines.append(f"Количество итераций проверки = {len(checks)}")

    for i, check in enumerate(checks, start=1):
        lines.append(f"  Итерация {i}:")
        lines.append(f"    n = {_fmt(_safe_getattr(check, 'n'))}")
        lines.append(f"    x_mean = {_fmt(_safe_getattr(check, 'x_mean'))}")
        lines.append(f"    S = {_fmt(_safe_getattr(check, 'S'))}")
        lines.append(f"    x_min = {_fmt(_safe_getattr(check, 'x_min'))}")
        lines.append(f"    x_max = {_fmt(_safe_getattr(check, 'x_max'))}")
        lines.append(f"    g_min = {_fmt(_safe_getattr(check, 'g_min'))}")
        lines.append(f"    g_max = {_fmt(_safe_getattr(check, 'g_max'))}")
        lines.append(f"    g_crit = {_fmt(_safe_getattr(check, 'g_crit'))}")

        remove_side = _safe_getattr(check, "remove_side", None)
        if remove_side is not None:
            lines.append(f"    remove_side = {remove_side}")

        removed_value = _safe_getattr(check, "removed_value", None)
        if removed_value is not None:
            lines.append(f"    removed_value = {_fmt(removed_value)}")

    removed = _safe_getattr(grubbs, "removed", [])
    cleaned_values = _safe_getattr(grubbs, "cleaned_values", [])
    lines.append(f"Удаленные значения: {removed if removed else 'нет'}")
    lines.append(f"Число результатов после исключения выбросов: {n_clean}")
    lines.append("Очищенные значения:")
    lines.append(", ".join(_fmt(x) for x in cleaned_values))
    lines.append("")

    lines.append("Шаг 7. Проверка гипотезы о нормальности")
    lines.append("-" * 78)

    if normality_mode == "assumed":
        lines.append("Проверка нормальности отдельно не выполнялась.")
        lines.append("Причина: после исключения выбросов n <= 15, нормальность принята заранее.")
        lines.append("")

    elif normality_mode == "composite":
        lines.append("Использован составной критерий для 15 < n <= 50.")
        lines.append(f"n = {_fmt(_safe_getattr(normality, 'n'))}")
        lines.append(f"x_mean = {_fmt(_safe_getattr(normality, 'x_mean'))}")
        lines.append(f"S = {_fmt(_safe_getattr(normality, 'S'))}")
        lines.append(f"S_biased = {_fmt(_safe_getattr(normality, 'S_biased'))}")

        c1 = _safe_getattr(normality, "criterion_1")
        c2 = _safe_getattr(normality, "criterion_2")

        lines.append("  Критерий 1:")
        lines.append(f"    d = {_fmt(_safe_getattr(c1, 'd'))}")
        lines.append(f"    d_low = {_fmt(_safe_getattr(c1, 'd_low'))}")
        lines.append(f"    d_high = {_fmt(_safe_getattr(c1, 'd_high'))}")
        lines.append(f"    passed = {_fmt(_safe_getattr(c1, 'passed'))}")

        lines.append("  Критерий 2:")
        lines.append(f"    threshold = {_fmt(_safe_getattr(c2, 'threshold'))}")
        lines.append(f"    exceed_count = {_fmt(_safe_getattr(c2, 'exceed_count'))}")
        lines.append(f"    allowed_exceed_count = {_fmt(_safe_getattr(c2, 'allowed_exceed_count'))}")
        lines.append(f"    p_value_table = {_fmt(_safe_getattr(c2, 'p_value_table'))}")
        lines.append(f"    z_value = {_fmt(_safe_getattr(c2, 'z_value'))}")
        lines.append(f"    passed = {_fmt(_safe_getattr(c2, 'passed'))}")

        lines.append(f"Общий результат проверки нормальности = {_fmt(_safe_getattr(normality, 'passed'))}")
        lines.append("")

    elif normality_mode == "pearson_smirnov":
        lines.append("Использованы критерии Пирсона и Мизеса–Смирнова для n > 50.")

        if pearson is not None:
            lines.append("  Критерий Пирсона:")
            lines.append(f"    n = {_fmt(_safe_getattr(pearson, 'n'))}")
            lines.append(f"    r = {_fmt(_safe_getattr(pearson, 'r'))}")
            lines.append(f"    h = {_fmt(_safe_getattr(pearson, 'h'))}")
            lines.append(f"    x_mean = {_fmt(_safe_getattr(pearson, 'x_mean'))}")
            lines.append(f"    S = {_fmt(_safe_getattr(pearson, 'S'))}")
            lines.append(f"    chi2_value = {_fmt(_safe_getattr(pearson, 'chi2_value'))}")
            lines.append(f"    df = {_fmt(_safe_getattr(pearson, 'df'))}")
            lines.append(f"    alpha = {_fmt(_safe_getattr(pearson, 'alpha'))}")
            lines.append(f"    chi2_low = {_fmt(_safe_getattr(pearson, 'chi2_low'))}")
            lines.append(f"    chi2_high = {_fmt(_safe_getattr(pearson, 'chi2_high'))}")
            lines.append(f"    passed = {_fmt(_safe_getattr(pearson, 'passed'))}")
            lines.append("")
            lines.append("    Интервалы:")
            lines.append("      idx |      left |     right |    center | observed | expected |        y | contribution")
            lines.append("      " + "-" * 92)

            intervals = _safe_getattr(pearson, "intervals", [])
            for interval in intervals:
                idx = _safe_getattr(interval, "index")
                left = _fmt(_safe_getattr(interval, "left"))
                right = _fmt(_safe_getattr(interval, "right"))
                center = _fmt(_safe_getattr(interval, "center"))
                observed = _safe_getattr(interval, "observed")
                expected = _fmt(_safe_getattr(interval, "expected"))
                y = _fmt(_safe_getattr(interval, "y"))
                contribution = _fmt(_safe_getattr(interval, "contribution"))

                lines.append(
                    f"      {idx:>3} | "
                    f"{left:>9} | "
                    f"{right:>9} | "
                    f"{center:>9} | "
                    f"{observed:>8} | "
                    f"{expected:>8} | "
                    f"{y:>8} | "
                    f"{contribution:>12}"
                )

            lines.append("")

        if smirnov is not None:
            lines.append("  Критерий Мизеса–Смирнова:")
            lines.append(f"    n = {_fmt(_safe_getattr(smirnov, 'n'))}")
            lines.append(f"    x_mean = {_fmt(_safe_getattr(smirnov, 'x_mean'))}")
            lines.append(f"    S = {_fmt(_safe_getattr(smirnov, 'S'))}")
            lines.append(f"    alpha = {_fmt(_safe_getattr(smirnov, 'alpha'))}")
            lines.append(f"    threshold = {_fmt(_safe_getattr(smirnov, 'threshold'))}")
            lines.append(f"    n_omega2 = {_fmt(_safe_getattr(smirnov, 'n_omega2'))}")
            lines.append(f"    a_value = {_fmt(_safe_getattr(smirnov, 'a_value'))}")
            lines.append(f"    passed = {_fmt(_safe_getattr(smirnov, 'passed'))}")
            lines.append("")

    else:
        lines.append("Информация о способе проверки нормальности отсутствует.")
        lines.append("")

    lines.append("Шаг 7.5. Доверительные границы случайной погрешности")
    lines.append("-" * 78)
    lines.append(f"n = {_fmt(_safe_getattr(random_error, 'n'))}")
    lines.append(f"p_conf = {_fmt(_safe_getattr(random_error, 'p_conf'))}")
    lines.append(f"df = {_fmt(_safe_getattr(random_error, 'df'))}")
    lines.append(f"x_mean = {_fmt(_safe_getattr(random_error, 'x_mean'))}")
    lines.append(f"S = {_fmt(_safe_getattr(random_error, 'S'))}")
    lines.append(f"S_x_mean = {_fmt(_safe_getattr(random_error, 'S_x_mean'))}")
    lines.append(f"t_value = {_fmt(_safe_getattr(random_error, 't_value'))}")
    lines.append(f"delta_random = {_fmt(_safe_getattr(random_error, 'delta'))}")
    lines.append("")

    lines.append("Шаг 8. Доверительные границы неисключенной систематической погрешности")
    lines.append("-" * 78)
    if systematic_error.method == "none":
        lines.append("Систематические погрешности отсутствуют или были учтены ранее.")
        lines.append(f"m = {systematic_error.m}")
        lines.append(f"theta_sum = {_fmt(systematic_error.theta_sum)}")
        lines.append("")
    else:
        lines.append(f"m = {_fmt(_safe_getattr(systematic_error, 'm'))}")
        lines.append(f"p_conf = {_fmt(_safe_getattr(systematic_error, 'p_conf'))}")
        lines.append(f"k = {_fmt(_safe_getattr(systematic_error, 'k'))}")
        lines.append(f"theta_sum = {_fmt(_safe_getattr(systematic_error, 'theta_sum'))}")
        lines.append(f"method = {_fmt(_safe_getattr(systematic_error, 'method'))}")
        lines.append("Компоненты НСП:")

        components = _safe_getattr(systematic_error, "components", [])
        for i, comp in enumerate(components, start=1):
            lines.append(f"  {i}. {_safe_getattr(comp, 'name')}")
            lines.append(f"     theta = {_fmt(_safe_getattr(comp, 'theta'))}")
            lines.append(f"     influence_coefficient = {_fmt(_safe_getattr(comp, 'influence_coefficient'))}")
            lines.append(f"     effective_theta = {_fmt(_safe_getattr(comp, 'effective_theta'))}")

        lines.append("")

    lines.append("Шаг 9. Доверительные границы погрешности результата измерения")
    lines.append("-" * 78)
    lines.append(f"p_conf = {_fmt(_safe_getattr(total_error, 'p_conf'))}")
    lines.append(f"x_mean = {_fmt(_safe_getattr(total_error, 'x_mean'))}")
    lines.append(f"delta_random = {_fmt(_safe_getattr(total_error, 'delta_random'))}")
    lines.append(f"theta_systematic = {_fmt(_safe_getattr(total_error, 'theta_systematic'))}")
    lines.append(f"s_x_mean = {_fmt(_safe_getattr(total_error, 's_x_mean'))}")
    lines.append(f"s_theta = {_fmt(_safe_getattr(total_error, 's_theta'))}")
    lines.append(f"s_total = {_fmt(_safe_getattr(total_error, 's_total'))}")
    lines.append(f"k_total = {_fmt(_safe_getattr(total_error, 'k_total'))}")
    lines.append(f"delta_total = {_fmt(_safe_getattr(total_error, 'delta_total'))}")
    lines.append(f"theta_mode = {_fmt(_safe_getattr(total_error, 'theta_mode'))}")
    lines.append(f"theta_k = {_fmt(_safe_getattr(total_error, 'theta_k'))}")
    lines.append("")

    lines.append("Шаг 10. Оформление результата измерения")
    lines.append("-" * 78)
    lines.append(f"x_raw = {_fmt(_safe_getattr(formatted_result, 'x_raw'))}")
    lines.append(f"delta_raw = {_fmt(_safe_getattr(formatted_result, 'delta_raw'))}")
    lines.append(f"p_conf = {_fmt(_safe_getattr(formatted_result, 'p_conf'))}")
    lines.append(f"x_rounded = {_fmt(_safe_getattr(formatted_result, 'x_rounded'))}")
    lines.append(f"delta_rounded = {_fmt(_safe_getattr(formatted_result, 'delta_rounded'))}")
    lines.append(f"delta_significant_digits = {_fmt(_safe_getattr(formatted_result, 'delta_significant_digits'))}")
    lines.append(f"decimal_places = {_fmt(_safe_getattr(formatted_result, 'decimal_places'))}")
    lines.append(f"Итоговая запись: {_fmt(_safe_getattr(formatted_result, 'notation'))}")
    lines.append("")

    return "\n".join(lines)

@typechecked
def _save_protocol_txt(result: dict, filepath: str | Path) -> Path:
    """
    Сохраняет протокол в txt-файл.
    """
    filepath = Path(filepath)
    text = _build_protocol_text(result)
    filepath.write_text(text, encoding="utf-8")
    return filepath

@typechecked
def calculate_and_save_protocol(values: list, config: dict, filepath: str | Path):
    """
    Выполняет полный расчет по ГОСТ Р 8.736-2011 и сохраняет протокол в txt-файл.

    Args:
        values (list): список результатов измерений.
        config (dict): словарь параметров расчета.
        filepath (str | Path): путь, по которому будет сохранен текстовый протокол.

    Raises:
        ValueError: если входные данные или параметры конфигурации не соответствуют
            условиям расчета по ГОСТ.

    Returns:
        dict: словарь с результатами всех этапов расчета. Одновременно сохраняет
        текстовый протокол по указанному пути.

    Example:
        >>> from moncenterlib.stats.stats_gost_R_8_736_2011.dataclasses import SystematicComponent
        >>> values = [10.12, 10.15, 10.11, 10.14, 10.13]
        >>> config = {
        ...     "alpha_grubbs": 0.05,
        ...     "normal_n<15": False,
        ...     "normality_composite_q1": 5,
        ...     "normality_composite_q2": 5,
        ...     "alpha_pearson": 0.05,
        ...     "r_pearson": None,
        ...     "alpha_smirnov": 0.1,
        ...     "random_error_p_conf": 0.95,
        ...     "systematic_components": [
        ...         SystematicComponent("калибровка", 0.05),
        ...         SystematicComponent("температура", 0.02),
        ...     ],
        ...     "systematic_error_p_conf": 0.95,
        ...     "systematic_error_k": None,
        ... }
        >>> result = calculate_and_save_protocol(values, config, "protocol.txt")
        >>> "formatted_result" in result
        True
    """
    result = _calculate(values, config)
    _save_protocol_txt(result, filepath)
    return result
