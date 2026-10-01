from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request

REQUIRED_HEADERS = {
    "content-security-policy": ("default-src 'self'", "frame-ancestors 'none'", "object-src 'none'"),
    "permissions-policy": ("camera=()", "microphone=()", "geolocation=()"),
    "referrer-policy": ("strict-origin-when-cross-origin",),
    "x-content-type-options": ("nosniff",),
    "x-frame-options": ("deny",),
    "cross-origin-opener-policy": ("same-origin",),
    "cross-origin-resource-policy": ("same-origin",),
}


def fetch_headers(url: str, attempts: int = 5) -> dict[str, str]:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "lp-health-check/1.0"})
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.status >= 400:
                    raise RuntimeError(f"HTTP {response.status}: {url}")
                return {key.lower(): value.strip() for key, value in response.headers.items()}
        except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
            last_error = error
            if attempt < attempts:
                time.sleep(3)
    raise RuntimeError(f"failed to fetch headers for {url}: {last_error}")


def validate(headers: dict[str, str]) -> None:
    for name, expected_fragments in REQUIRED_HEADERS.items():
        actual = headers.get(name, "")
        if not actual:
            raise AssertionError(f"missing security header: {name}")
        normalized = actual.lower()
        for fragment in expected_fragments:
            if fragment.lower() not in normalized:
                raise AssertionError(f"security header mismatch: {name}: expected {fragment!r} in {actual!r}")


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else "https://neoenox-apps.pages.dev/"
    headers = fetch_headers(url)
    validate(headers)
    print("Production security headers passed")


if __name__ == "__main__":
    main()
