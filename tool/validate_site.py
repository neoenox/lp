from __future__ import annotations

import json
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "tool/site_manifest.json").read_text(encoding="utf-8"))
ORIGIN = MANIFEST["origin"].rstrip("/")
RELEASE_LABELS = {
    "preparing": "準備中",
    "published": "公開中",
    "suspended": "公開停止中",
}
STORE_LINK_PATTERNS = (
    "https://play.google.com/store/apps/details",
    "https://apps.apple.com/",
)


class HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self.links: list[dict[str, str]] = []
        self.meta: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "link":
            self.links.append(values)
        elif tag == "meta":
            self.meta.append(values)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def page_paths() -> list[str]:
    paths = ["/"]
    for app in MANIFEST["apps"]:
        base = f"/apps/{app['slug']}"
        paths.extend([f"{base}/", f"{base}/privacy", f"{base}/terms", f"{base}/contact"])
    paths.extend(page["path"] for page in MANIFEST.get("standalone_pages", []))
    return paths


def all_html_paths() -> list[str]:
    paths = page_paths() + ["/404"]
    for app in MANIFEST["apps"]:
        base = f"/apps/{app['slug']}"
        paths.append(f"{base}/404")
    return paths


def local_html_path(site: Path, url_path: str) -> Path:
    if url_path == "/":
        return site / "index.html"
    if url_path == "/404":
        return site / "404.html"
    stripped = url_path.strip("/")
    if url_path.endswith("/"):
        return site / stripped / "index.html"
    if url_path.endswith("/404"):
        return site / stripped[:-len("404")] / "404.html"
    return site / f"{stripped}.html"


def expected_og(url_path: str) -> str:
    if url_path == "/":
        return f"{ORIGIN}/assets/brand/og-portal.png"
    slug = url_path.split("/")[2]
    app = next((item for item in MANIFEST["apps"] if item["slug"] == slug), None)
    if app is not None:
        image = app["og_image"]
    else:
        page = next(item for item in MANIFEST.get("standalone_pages", []) if item["path"] == url_path)
        image = page["og_image"]
    return f"{ORIGIN}/assets/brand/{image}"


def read_png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert_true(data.startswith(b"\x89PNG\r\n\x1a\n"), f"invalid PNG: {path}")
    assert_true(len(data) >= 24, f"truncated PNG: {path}")
    return struct.unpack(">II", data[16:24])


def read_webp_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert_true(data[:4] == b"RIFF" and data[8:12] == b"WEBP", f"invalid WebP: {path}")
    chunk = data[12:16]
    if chunk == b"VP8 ":
        payload = data[20:]
        assert_true(payload[3:6] == b"\x9d\x01\x2a", f"invalid VP8 frame: {path}")
        return int.from_bytes(payload[6:8], "little") & 0x3FFF, int.from_bytes(payload[8:10], "little") & 0x3FFF
    if chunk == b"VP8L":
        bits = int.from_bytes(data[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if chunk == b"VP8X":
        return int.from_bytes(data[24:27], "little") + 1, int.from_bytes(data[27:30], "little") + 1
    raise AssertionError(f"unsupported WebP encoding: {path}")


def metadata_value(parser: HeadParser, *, property_name: str | None = None, name: str | None = None) -> list[str]:
    values: list[str] = []
    for attrs in parser.meta:
        if property_name is not None and attrs.get("property") == property_name:
            values.append(attrs.get("content", ""))
        if name is not None and attrs.get("name") == name:
            values.append(attrs.get("content", ""))
    return values


def validate_store_url(value: object, store: str, slug: str) -> str | None:
    if value is None:
        return None
    assert_true(isinstance(value, str) and value, f"{store} URL must be null or a non-empty string: {slug}")
    parsed = urlsplit(value)
    assert_true(parsed.scheme == "https", f"{store} URL must use HTTPS: {slug}: {value}")

    if store == "google_play":
        query = parse_qs(parsed.query)
        assert_true(parsed.netloc == "play.google.com", f"invalid Google Play host: {slug}: {value}")
        assert_true(parsed.path == "/store/apps/details", f"invalid Google Play path: {slug}: {value}")
        assert_true(bool(query.get("id", [""])[0]), f"Google Play URL has no package id: {slug}: {value}")
    elif store == "app_store":
        assert_true(parsed.netloc == "apps.apple.com", f"invalid App Store host: {slug}: {value}")
        assert_true("/app/" in parsed.path and re.search(r"/id\d+(?:/|$)", parsed.path) is not None, f"invalid App Store path: {slug}: {value}")
    else:
        raise AssertionError(f"unknown store type: {store}")
    return value


def validate_manifest() -> None:
    apps = MANIFEST.get("apps")
    assert_true(isinstance(apps, list) and apps, "manifest apps must be a non-empty list")
    seen: set[str] = set()
    for app in apps:
        slug = app.get("slug")
        assert_true(isinstance(slug, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) is not None, f"invalid app slug: {slug}")
        assert_true(slug not in seen, f"duplicate app slug: {slug}")
        seen.add(slug)

        display_name = app.get("display_name")
        assert_true(isinstance(display_name, str) and display_name.strip(), f"missing display_name: {slug}")
        status = app.get("release_status")
        assert_true(status in RELEASE_LABELS, f"invalid release_status: {slug}: {status}")
        google_play = validate_store_url(app.get("google_play_url"), "google_play", slug)
        app_store = validate_store_url(app.get("app_store_url"), "app_store", slug)
        if status == "published":
            assert_true(bool(google_play or app_store), f"published app must have a store URL: {slug}")

    standalone_paths: set[str] = set()
    for page in MANIFEST.get("standalone_pages", []):
        path = page.get("path")
        assert_true(
            isinstance(path, str)
            and path.startswith("/apps/")
            and not path.endswith("/")
            and "." not in path
            and ".." not in path,
            f"invalid standalone page path: {path}",
        )
        assert_true(path not in standalone_paths, f"duplicate standalone page path: {path}")
        standalone_paths.add(path)
        assert_true(page.get("og_image") in MANIFEST["brand_assets"], f"invalid standalone page OGP: {path}")


def validate_release_presentation(site: Path) -> None:
    portal = (site / "index.html").read_text(encoding="utf-8")
    for app in MANIFEST["apps"]:
        slug = app["slug"]
        status = app["release_status"]
        label = RELEASE_LABELS[status]
        marker = f'data-app-slug="{slug}"'
        assert_true(portal.count(marker) == 1, f"portal app card must appear exactly once: {slug}")
        card_pattern = re.compile(
            rf'<a\b(?=[^>]*{re.escape(marker)})(?=[^>]*data-release-status="{re.escape(status)}")[^>]*>(.*?)</a>',
            re.DOTALL,
        )
        match = card_pattern.search(portal)
        assert_true(match is not None, f"portal release state mismatch: {slug}: {status}")
        card = match.group(1)
        assert_true(app["display_name"] in card, f"portal display name mismatch: {slug}")
        assert_true(
            re.search(rf'data-release-status-label[^>]*>\s*{re.escape(label)}\s*</span>', card) is not None,
            f"portal release label mismatch: {slug}: {label}",
        )

        app_index = site / "apps" / slug / "index.html"
        app_text = app_index.read_text(encoding="utf-8")
        configured_urls = [url for url in (app["google_play_url"], app["app_store_url"]) if url]
        if status == "published":
            for url in configured_urls:
                assert_true(url in app_text, f"published store URL is missing from app LP: {slug}: {url}")
        else:
            for pattern in STORE_LINK_PATTERNS:
                assert_true(pattern not in app_text, f"non-published app exposes a store link: {slug}: {pattern}")


def validate_html(site: Path) -> None:
    expected_paths = all_html_paths()
    actual_files = sorted(site.rglob("*.html"))
    expected_files = sorted(local_html_path(site, path) for path in expected_paths)
    assert_true(actual_files == expected_files, f"HTML set mismatch: actual={actual_files}, expected={expected_files}")

    internal_html_link_pattern = re.compile(
        r'href="(?!(?:https?:|mailto:|tel:|#))[^\"]*\.html(?:[?#][^\"]*)?"'
    )
    expected_verification = os.environ.get("SEARCH_CONSOLE_VERIFICATION", "").strip()
    for url_path in expected_paths:
        path = local_html_path(site, url_path)
        text = path.read_text(encoding="utf-8")
        parser = HeadParser()
        parser.feed(text)
        assert_true(parser.title.strip(), f"empty title: {path}")
        assert_true(
            not internal_html_link_pattern.search(text),
            f".html internal link found: {path}",
        )

        is_404 = url_path.endswith("/404")

        favicons = [item.get("href") for item in parser.links if "icon" in item.get("rel", "").split() and item.get("href", "").endswith("favicon.svg")]
        assert_true(favicons == ["/assets/brand/favicon.svg"], f"favicon mismatch: {path}: {favicons}")

        if not is_404:
            canonical = [item.get("href", "") for item in parser.links if item.get("rel") == "canonical"]
            expected_canonical = f"{ORIGIN}{url_path}"
            assert_true(canonical == [expected_canonical], f"canonical mismatch: {path}: {canonical}")

            og_url = metadata_value(parser, property_name="og:url")
            og_image = metadata_value(parser, property_name="og:image")
            twitter_image = metadata_value(parser, name="twitter:image")
            assert_true(og_url == [expected_canonical], f"og:url mismatch: {path}: {og_url}")
            assert_true(og_image == [expected_og(url_path)], f"og:image mismatch: {path}: {og_image}")
            assert_true(twitter_image == og_image, f"twitter:image mismatch: {path}: {twitter_image}")

        verification = metadata_value(parser, name="google-site-verification")
        if url_path == "/" and expected_verification:
            assert_true(verification == [expected_verification], f"Search Console verification mismatch: {verification}")
        elif url_path != "/":
            assert_true(not verification, f"Search Console verification must only appear on the portal root: {path}")

    validate_release_presentation(site)


def validate_assets(site: Path) -> None:
    brand = site / "assets/brand"
    for name in MANIFEST["brand_assets"]:
        path = brand / name
        assert_true(path.is_file() and path.stat().st_size > 0, f"missing brand asset: {path}")

    expected_png = {
        "favicon-16x16.png": (16, 16),
        "favicon-32x32.png": (32, 32),
        "apple-touch-icon.png": (180, 180),
        "og-portal.png": (1200, 630),
        "og-ashita-motsumono.png": (1200, 630),
        "og-ehenotane.png": (1200, 630),
    }
    for name, size in expected_png.items():
        path = brand / name
        assert_true(read_png_size(path) == size, f"PNG dimensions mismatch: {path}")
        if name.startswith("og-"):
            assert_true(path.stat().st_size < 1_000_000, f"OGP image too large: {path}")

    app_js = (site / "assets/app.js").read_text(encoding="utf-8")
    for app in MANIFEST["apps"]:
        for screenshot in app["screenshots"]:
            path = site / "assets/apps" / app["slug"] / "screenshots" / screenshot
            assert_true(path.is_file(), f"missing screenshot: {path}")
            assert_true(read_webp_size(path) == (360, 640), f"screenshot dimensions mismatch: {path}")
            assert_true(5_000 < path.stat().st_size < 100_000, f"unexpected screenshot size: {path}")
            assert_true(f"/assets/apps/{app['slug']}/screenshots/{screenshot}" in app_js, f"screenshot is not referenced: {screenshot}")


def validate_sitemap(site: Path) -> None:
    tree = ET.parse(site / "sitemap.xml")
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    actual = [node.text or "" for node in tree.findall("sm:url/sm:loc", namespace)]
    expected = [f"{ORIGIN}{path}" for path in page_paths()]
    assert_true(actual == expected, f"sitemap mismatch: actual={actual}, expected={expected}")


def main() -> None:
    site = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "_site").resolve()
    validate_manifest()
    assert_true(site.is_dir(), f"site directory not found: {site}")
    assert_true((site / "_headers").is_file(), "_headers is missing from artifact")
    assert_true(not (site / ".github").exists(), ".github leaked into artifact")
    assert_true(not (site / "README.md").exists(), "README leaked into artifact")
    validate_html(site)
    validate_assets(site)
    validate_sitemap(site)
    print("Site artifact validation passed")


if __name__ == "__main__":
    main()
