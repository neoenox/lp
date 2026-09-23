from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_WORKFLOW = (ROOT / '.github/workflows/audit-production.yml').read_text(encoding='utf-8')
PR_WORKFLOW = (ROOT / '.github/workflows/validate-production-browser.yml').read_text(encoding='utf-8')
DEPLOY_WORKFLOW = (ROOT / '.github/workflows/deploy.yml').read_text(encoding='utf-8')
ASHITA_SCRIPT = (ROOT / 'tool/capture_production_screenshots.cjs').read_text(encoding='utf-8')
FALLBACK_SCRIPT = (ROOT / 'tool/audit_screenshot_fallback.cjs').read_text(encoding='utf-8')
EHENOTANE_SCRIPT = (ROOT / 'tool/audit_ehenotane.cjs').read_text(encoding='utf-8')
APP_JS = (ROOT / 'assets/app.js').read_text(encoding='utf-8')
MOBILE_CONFIG = (ROOT / 'lighthouserc.mobile.cjs').read_text(encoding='utf-8')
DESKTOP_CONFIG = (ROOT / 'lighthouserc.desktop.cjs').read_text(encoding='utf-8')


class ProductionAuditTest(unittest.TestCase):
    def test_pull_request_browser_audit_uses_local_artifact(self) -> None:
        self.assertIn('bash tool/prepare_site.sh', PR_WORKFLOW)
        self.assertIn('python3 -m http.server 8123 --directory _site', PR_WORKFLOW)
        self.assertIn('http://127.0.0.1:8123/apps/ashita-motsumono/', PR_WORKFLOW)
        self.assertIn('http://127.0.0.1:8123/apps/ehenotane/', PR_WORKFLOW)
        self.assertNotIn('TARGET_URL: https://neoenox-apps.pages.dev', PR_WORKFLOW)

    def test_both_app_browser_flows_are_exercised(self) -> None:
        for workflow in (PR_WORKFLOW, PRODUCTION_WORKFLOW):
            self.assertIn('node tool/capture_production_screenshots.cjs', workflow)
            self.assertIn('node tool/audit_screenshot_fallback.cjs', workflow)
            self.assertIn('node tool/audit_ehenotane.cjs', workflow)
        self.assertIn("page.click('.quiz-card__choice[data-index=\"0\"]')", EHENOTANE_SCRIPT)
        self.assertIn('await page.setJavaScriptEnabled(false)', EHENOTANE_SCRIPT)
        self.assertIn("pathname.endsWith('/review-extraction.webp')", FALLBACK_SCRIPT)
        self.assertIn('failedGridMockPresent', FALLBACK_SCRIPT)
        self.assertIn('heroIsRealScreen', FALLBACK_SCRIPT)

    def test_image_fallback_preloads_before_replacing(self) -> None:
        self.assertIn('replaceMockAfterImageLoad', APP_JS)
        self.assertIn('var preloader = new Image()', APP_JS)
        self.assertIn('preloader.addEventListener("load"', APP_JS)
        self.assertIn('preloader.addEventListener("error"', APP_JS)
        self.assertLess(APP_JS.index('preloader.addEventListener("load"'), APP_JS.index('preloader.src = screenshot.src'))
        self.assertIn('mock.replaceWith(image)', APP_JS)
        self.assertNotIn('mock.replaceWith(createScreenshotImage', APP_JS)

    def test_production_verification_covers_manifest_site(self) -> None:
        self.assertIn('python3 tool/verify_remote_site.py', DEPLOY_WORKFLOW)
        self.assertIn('python3 tool/verify_remote_site.py', PRODUCTION_WORKFLOW)
        self.assertIn('bash tool/prepare_site.sh', DEPLOY_WORKFLOW)
        self.assertIn('python3 tool/validate_site.py _site', DEPLOY_WORKFLOW)

    def test_lighthouse_runs_three_times_with_thresholds_for_each_app(self) -> None:
        for config in (MOBILE_CONFIG, DESKTOP_CONFIG):
            self.assertIn('numberOfRuns: 3', config)
            self.assertIn("'categories:accessibility'", config)
            self.assertIn("'categories:performance': ['warn'", config)
            self.assertIn('LHCI_APP_SLUG', config)
        self.assertIn("jq -r '.apps[].slug' tool/site_manifest.json", PRODUCTION_WORKFLOW)
        self.assertIn('while IFS= read -r slug; do', PRODUCTION_WORKFLOW)

    def test_tooling_is_pinned(self) -> None:
        for workflow in (PR_WORKFLOW, PRODUCTION_WORKFLOW):
            self.assertIn('puppeteer-core@25.3.0', workflow)
            self.assertIn('actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0', workflow)
            self.assertIn('actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a', workflow)
        self.assertIn('@lhci/cli@0.15.1', PRODUCTION_WORKFLOW)

    def test_ashita_responsive_audit_still_checks_three_widths(self) -> None:
        for name, width, columns in (
            ('mobile', 390, 1),
            ('tablet', 820, 2),
            ('desktop', 1440, 3),
        ):
            self.assertIn(f"{{ name: '{name}', width: {width}", ASHITA_SCRIPT)
            self.assertIn(f'expectedColumns: {columns}', ASHITA_SCRIPT)
        self.assertIn('horizontal overflow', ASHITA_SCRIPT)
        self.assertIn("page.keyboard.press('Tab')", ASHITA_SCRIPT)
        self.assertIn('prefers-reduced-motion', ASHITA_SCRIPT)


if __name__ == '__main__':
    unittest.main()
