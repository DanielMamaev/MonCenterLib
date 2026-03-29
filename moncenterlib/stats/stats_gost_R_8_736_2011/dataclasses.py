from dataclasses import dataclass


@dataclass
class BasicStats:
    """
    Clause 5. Estimate of the measured value and standard deviation.

    Attributes:
        n (int): Number of measurement results.
        x_mean (float): Arithmetic mean value.
        S (float): Standard deviation ``S``.
        S_x_mean (float): Standard deviation of the arithmetic mean.
        S_biased (float): Biased standard deviation ``S*``.
    """
    n: int
    x_mean: float
    S: float
    S_x_mean: float
    S_biased: float


@dataclass
class GrubbsCheck:
    """
    Clause 6. Detection and elimination of gross errors.

    Attributes:
        n (int): Number of measurement results.
        x_mean (float): Arithmetic mean value.
        S (float): Standard deviation ``S``.
        x_min (float): Minimum measurement result.
        x_max (float): Maximum measurement result.
        g_min (float): Computed Grubbs criterion for the minimum value.
        g_max (float): Computed Grubbs criterion for the maximum value.
        g_crit (float): Theoretical Grubbs criterion.
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
    Clause 6. Detection and elimination of gross errors.

    Attributes:
        cleaned_values (list): Filtered measurement results.
        removed (list): Removed measurement results.
        checks (list[GrubbsCheck]): Results for each Grubbs test iteration.
    """
    cleaned_values: list
    removed: list
    checks: list[GrubbsCheck]


@dataclass
class CompositeCriterion1Result:
    """
    Clause 7. Confidence limits for random error.

    Clause 7.3 applies for ``15 < n <= 50``.
    Criterion 1, Appendix B.

    Attributes:
        d (float): Computed ratio ``d~``.
        d_low (float): Lower quantile of the distribution.
        d_high (float): Upper quantile of the distribution.
        passed (bool): ``True`` if the criterion is satisfied.
    """
    d: float
    d_low: float
    d_high: float
    passed: bool


@dataclass
class CompositeCriterion2Result:
    """
    Clause 7. Confidence limits for random error.

    Clause 7.3 applies for ``15 < n <= 50``.
    Criterion 2, Appendix B.

    Attributes:
        threshold (float): Threshold value ``z_p/2 * S``.
        exceed_count (int): Number of values ``abs(x_i - x_mean)`` above the threshold.
        allowed_exceed_count (int): Allowed count ``m`` from Table B.2.
        p_value_table (float): Probability value from Table B.2.
        z_value (float): Upper quantile from Table B.3.
        passed (bool): ``True`` if the criterion is satisfied.
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
    Clause 7. Confidence limits for random error.

    Clause 7.3 applies for ``15 < n <= 50``.
    Result of the normality hypothesis test for measurement results.

    Attributes:
        n (int): Number of measurement results.
        x_mean (float): Arithmetic mean value.
        S (float): Standard deviation ``S``.
        S_biased (float): Biased standard deviation ``S*``.
        criterion_1 (CompositeCriterion1Result): Result of Criterion 1 from Appendix B.
        criterion_2 (CompositeCriterion2Result): Result of Criterion 2 from Appendix B.
        passed (bool): ``True`` if both criteria are satisfied.
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
    Clause 7. Confidence limits for random error.

    Clause 7.4 applies for ``n > 50``.

    Attributes:
        index (int): Interval index ``i``.
        left (float): Left interval boundary.
        right (float): Right interval boundary.
        center (float): Interval center ``x_i0``.
        observed (int): Observed count of measurements in the interval.
        expected (float): Expected count of measurements in the interval.
        y (float): Probability of falling into interval ``i``.
        contribution (float): Computed Pearson criterion contribution.
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
    Clause 7. Confidence limits for random error.

    Clause 7.4 applies for ``n > 50``.
    Result of the Pearson normality hypothesis test.

    Attributes:
        n (int): Number of measurement results.
        r (int): Number of grouping intervals.
        h (float): Grouping interval width.
        x_mean (float): Arithmetic mean value.
        S (float): Standard deviation ``S``.
        chi2_value (float): Computed Pearson criterion value.
        df (int): Degrees of freedom.
        alpha (float): Significance level.
        chi2_low (float): Lower critical bound for ``chi^2``.
        chi2_high (float): Upper critical bound for ``chi^2``.
        passed (bool): ``True`` if the normality hypothesis is not rejected.
        intervals (list[PearsonInterval]): Grouping intervals and Pearson parameters.
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
    Appendix G. Intermediate values for the ``omega^2`` criterion.

    Attributes:
        j (int): Index of the ordered measurement result.
        x_j (float): Measurement result value.
        a_j (float): Coefficient ``(2j - 1) / (2n)``.
        F_xj (float): Theoretical normal distribution value ``F(x_j)``.
        ln_F_xj (float): ``ln(F(x_j))``.
        one_minus_a_j (float): Value ``1 - a_j``.
        one_minus_F_xj (float): Value ``1 - F(x_j)``.
        ln_one_minus_F_xj (float): ``ln(1 - F(x_j))``.
        term (float): Summand in formula ``(G.1)``.
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
    Appendix G. Result of the ``omega^2`` normality test.

    Attributes:
        n (int): Number of measurement results.
        x_mean (float): Arithmetic mean.
        S (float): Standard deviation of the measurement results.
        n_omega2 (float): Computed statistic ``nOmega^2``.
        a_value (float): Function value ``a(x)`` from Table G.3.
        alpha (float): Significance level.
        threshold (float): Threshold equal to ``1 - alpha``.
        passed (bool): ``True`` if the normality hypothesis is not rejected.
        rows (list[MisesSmirnovRow]): Intermediate calculation rows.
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
    Clause 7.5. Confidence limits for the random error.

    Attributes:
        n (int): Number of measurement results.
        p_conf (float): Confidence probability ``P``.
        df (int): Degrees of freedom ``n - 1``.
        x_mean (float): Arithmetic mean value.
        S (float): Standard deviation ``S``.
        S_x_mean (float): Standard deviation of the arithmetic mean.
        t_value (float): Student coefficient.
        delta (float): Confidence limit of the random error without sign.
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
    Clause 8. Confidence limits for the unexcluded systematic error.

    One systematic error component.

    Attributes:
        name (str): Component name.
        theta (float): Unsigned limit of the component.
        influence_coefficient (float): Influence coefficient ``dX/dY``.
            If not specified, it is assumed to be ``1``.
        effective_theta (float): Effective component limit equal to
            ``abs(influence_coefficient) * abs(theta)``.
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
    Clause 8. Confidence limits for the unexcluded systematic error.

    Attributes:
        m (int): Number of systematic components.
        p_conf (float): Confidence probability.
        k (float): Composition coefficient.
        theta_sum (float): Final unsigned systematic error limit.
        method (str): Calculation method: ``none``, ``sum``, or ``rss``.
        components (list[SystematicComponent]): List of components.
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
    Clause 9. Confidence limits for the error in the estimate of the measured value.

    Attributes:
        p_conf (float): Confidence probability.
        x_mean (float): Estimate of the measured value.
        delta_random (float): Confidence limit of the random error.
        theta_systematic (float): Systematic error limit.
        s_x_mean (float): Standard deviation of the arithmetic mean.
        s_theta (float): Standard deviation of the systematic error.
        s_total (float): Total standard deviation of the estimate.
        k_total (float): Coefficient ``K`` from formula ``(12)``.
        delta_total (float): Final confidence limit of the total error.
        theta_mode (str): Systematic error interpretation mode:
            ``plain`` for formula ``(14)``, or ``confidence`` for formula ``(15)``.
        theta_k (float | None): Coefficient ``k`` from Clause 8, used only in
            ``confidence`` mode.
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
    Clause 10. Presentation of the estimate of the measured value.

    Appendix E. Rounding rules.

    Attributes:
        x_raw (float): Original estimate of the measured value.
        delta_raw (float): Original unsigned error.
        p_conf (float): Confidence probability.
        x_rounded (float): Rounded estimate of the measured value.
        delta_rounded (float): Rounded error.
        delta_significant_digits (int): Number of significant digits retained in the error.
        decimal_places (int): Number of decimal places in the final notation.
        notation (str): Final formatted result, for example ``x ± Delta, P=...``.
    """
    x_raw: float
    delta_raw: float
    p_conf: float
    x_rounded: float
    delta_rounded: float
    delta_significant_digits: int
    decimal_places: int
    notation: str
