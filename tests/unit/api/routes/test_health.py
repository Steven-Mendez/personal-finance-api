from app.services.health import build_liveness_payload, build_readiness_payload


def test_build_liveness_payload_returns_alive_status() -> None:
    assert build_liveness_payload() == {"status": "alive"}


def test_build_readiness_payload_returns_ready_when_all_dependencies_healthy() -> None:
    payload = build_readiness_payload({"api": "healthy", "db": "healthy"})

    assert payload == {
        "status": "ready",
        "dependencies": {"api": "healthy", "db": "healthy"},
    }


def test_build_readiness_payload_returns_unready_when_any_dependency_unhealthy() -> None:
    payload = build_readiness_payload({"api": "healthy", "db": "unhealthy"})

    assert payload == {
        "status": "unready",
        "dependencies": {"api": "healthy", "db": "unhealthy"},
    }
