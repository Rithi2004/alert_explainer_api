from models import Alert

NEXT_STEPS = {
    "critical": "Investigate immediately and take corrective action.",
    "warning": "Review the affected system and monitor the metric closely.",
    "info": "Review the metric and confirm whether any action is needed.",
}


def generate_explanation(alert: Alert) -> str:
    """Build an explanation and acknowledgement string for an alert.

    Args:
        alert: Alert whose severity, source, title, metric values, threshold,
            and optional ``resolved_by`` value are used in the explanation.

    Returns:
        The explanation string, including the recommended next step and
        acknowledgement.

    Raises:
        KeyError: If ``alert.severity`` is not a key in ``NEXT_STEPS``.
        AttributeError: If a non-None ``alert.resolved_by`` value does not
            have an ``upper`` method.
    """
    if alert.metric_value > alert.threshold:
        comparison = "exceeded"
    elif alert.metric_value < alert.threshold:
        comparison = "fell below"
    else:
        comparison = "reached"

    next_step = NEXT_STEPS[alert.severity]
    explanation = (
        f'This {alert.severity} alert from {alert.source} is titled "{alert.title}". '
        f"The {alert.metric_name} metric {comparison} its threshold: the current "
        f"value is {alert.metric_value}, compared with a threshold of "
        f"{alert.threshold}. Recommended next step: {next_step}"
    )

    resolved_by = getattr(alert, "resolved_by", None)
    if resolved_by is None:
        acknowledgement = "Not yet acknowledged"
    else:
        acknowledgement = resolved_by.upper()

    return explanation + f" Acknowledged by: {acknowledgement}."