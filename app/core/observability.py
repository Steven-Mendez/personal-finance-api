from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator


def setup_observability(app: FastAPI) -> None:
    """
    Sets up Prometheus metrics instrumentation.
    Provides a /metrics endpoint for monitoring.
    """
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=[
            ".*admin.*",
            "/metrics",
            "/health/live",
            "/health/ready",
        ],
        env_var_name="ENABLE_METRICS",
    )
    instrumentator.instrument(app).expose(
        app, include_in_schema=False, tags=["observability"]
    )
