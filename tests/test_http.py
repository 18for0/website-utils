from src.common.http import BROWSER_USER_AGENT, browser_request


def test_browser_request_carries_browser_user_agent():
    req = browser_request("https://example.test/path")

    assert req.full_url == "https://example.test/path"
    assert req.get_header("User-agent") == BROWSER_USER_AGENT


def test_browser_user_agent_is_a_desktop_browser_string():
    # Guardrail: the whole point is to avoid Cloudflare fingerprinting the
    # default Python-urllib UA. If the constant ever drifts back to a
    # non-browser value, tests should flag it.
    assert BROWSER_USER_AGENT.startswith("Mozilla/5.0")
    assert "Chrome/" in BROWSER_USER_AGENT
    assert "Python-urllib" not in BROWSER_USER_AGENT
