"""HTTP probe helpers shared by Lambdas that fetch external URLs."""

from __future__ import annotations

from urllib import request

# The 18for0 public site sits behind a Cloudflare WAF that rejects the
# default `Python-urllib/X.Y` User-Agent with HTTP 403. Health probes need
# to measure real reachability, not WAF fingerprinting, so every outbound
# HTTP call in this repo presents as a current mainstream desktop browser.
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def browser_request(url: str) -> request.Request:
    """Build a urllib Request that carries a browser User-Agent header."""
    return request.Request(url, headers={"User-Agent": BROWSER_USER_AGENT})
