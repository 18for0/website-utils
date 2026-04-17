from unittest.mock import MagicMock, patch

import pytest

from src import health_check
from src.common.errors import LambdaError


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("TARGET_URL", "https://example.test/health")
    monkeypatch.setenv("ERROR_TOPIC_ARN", "arn:aws:sns:eu-west-1:0:topic")


def _fake_response(status: int) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.__enter__.return_value = resp
    return resp


def test_returns_status_on_success():
    with (
        patch.object(health_check.request, "urlopen", return_value=_fake_response(200)),
        patch("src.common.errors.notify_failure") as notify,
    ):
        result = health_check.lambda_handler({}, None)

    assert result == {"url": "https://example.test/health", "status": 200}
    notify.assert_not_called()


def test_missing_url_notifies_and_raises(monkeypatch):
    monkeypatch.delenv("TARGET_URL", raising=False)
    with (
        patch("src.common.errors.notify_failure") as notify,
        pytest.raises(LambdaError),
    ):
        health_check.lambda_handler({}, None)
    notify.assert_called_once()


def test_http_error_notifies_and_raises():
    with (
        patch.object(health_check.request, "urlopen", return_value=_fake_response(503)),
        patch("src.common.errors.notify_failure") as notify,
        pytest.raises(LambdaError),
    ):
        health_check.lambda_handler({}, None)
    notify.assert_called_once()
