from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from src import website_health_check
from src.common.errors import LambdaError


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("TARGET_URL", "https://18for0.lennonsec.org")
    monkeypatch.setenv("ERROR_TOPIC_ARN", "arn:aws:sns:eu-west-1:0:topic")


def _fake_response(status: int) -> MagicMock:
    response = MagicMock()
    response.status = status
    response.__enter__.return_value = response
    return response


def test_returns_status_on_success():
    with (
        patch.object(
            website_health_check.request,
            "urlopen",
            return_value=_fake_response(200),
        ) as urlopen,
        patch("src.common.errors.notify_failure") as notify,
    ):
        result = website_health_check.lambda_handler({}, None)

    assert result == {"url": "https://18for0.lennonsec.org", "status": 200}
    notify.assert_not_called()

    sent_request = urlopen.call_args.args[0]
    assert sent_request.get_header("User-agent") == website_health_check.USER_AGENT


def test_missing_url_notifies_with_site_specific_subject(monkeypatch):
    monkeypatch.delenv("TARGET_URL", raising=False)
    with (
        patch("src.common.errors.notify_failure") as notify,
        pytest.raises(LambdaError),
    ):
        website_health_check.lambda_handler({}, None)

    notify.assert_called_once()
    kwargs = notify.call_args.kwargs
    assert kwargs["subject"] == website_health_check.EMAIL_SUBJECT
    assert "18for0 website" in kwargs["body"]
    assert "TARGET_URL" in kwargs["body"]


def test_http_error_status_notifies_with_site_specific_body():
    with (
        patch.object(
            website_health_check.request,
            "urlopen",
            return_value=_fake_response(503),
        ),
        patch("src.common.errors.notify_failure") as notify,
        pytest.raises(LambdaError),
    ):
        website_health_check.lambda_handler({}, None)

    notify.assert_called_once()
    kwargs = notify.call_args.kwargs
    assert kwargs["subject"] == website_health_check.EMAIL_SUBJECT
    assert "HTTP 503" in kwargs["body"]
    assert "https://18for0.lennonsec.org" in kwargs["body"]


def test_url_error_notifies_with_site_specific_body():
    with (
        patch.object(
            website_health_check.request,
            "urlopen",
            side_effect=URLError("connection refused"),
        ),
        patch("src.common.errors.notify_failure") as notify,
        pytest.raises(LambdaError),
    ):
        website_health_check.lambda_handler({}, None)

    notify.assert_called_once()
    kwargs = notify.call_args.kwargs
    assert kwargs["subject"] == website_health_check.EMAIL_SUBJECT
    assert "request failed" in kwargs["body"]
