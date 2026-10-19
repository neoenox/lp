from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / '.github/workflows/audit-production-accessibility.yml').read_text(encoding='utf-8')
SCRIPT = (ROOT / 'tool/audit_production_accessibility.cjs').read_text(encoding='utf-8')


class ProductionAccessibilityAuditTest(unittest.TestCase):
    def test_workflow_audits_both_apps(self) -> None:
        self.assertIn('slug: ashita-motsumono', WORKFLOW)
        self.assertIn('expected_real_screens: 4', WORKFLOW)
        self.assertIn('slug: ehenotane', WORKFLOW)
        self.assertIn('expected_real_screens: 0', WORKFLOW)
        self.assertIn('strategy:', WORKFLOW)
        self.assertIn('matrix:', WORKFLOW)

    def test_pull_requests_use_local_site_artifact(self) -> None:
        self.assertIn('bash tool/prepare_site.sh', WORKFLOW)
        self.assertIn('python3 -m http.server 8123 --directory _site', WORKFLOW)
        self.assertIn('origin="http://127.0.0.1:8123"', WORKFLOW)
        self.assertIn("github.event_name == 'pull_request'", WORKFLOW)

    def test_pull_request_job_has_read_only_permissions(self) -> None:
        self.assertIn('audit-accessibility:', WORKFLOW)
        self.assertIn('permissions:\n      contents: read', WORKFLOW)
        self.assertIn('record-status:', WORKFLOW)
        self.assertIn('permissions:\n      statuses: write', WORKFLOW)
        self.assertIn("github.event_name != 'pull_request'", WORKFLOW)

    def test_script_supports_variable_screenshot_counts(self) -> None:
        self.assertIn("process.env.EXPECT_REAL_SCREENS || '0'", SCRIPT)
        self.assertIn('expectedRealScreens > 0', SCRIPT)
        self.assertIn('dom.images.length === expectedRealScreens', SCRIPT)
        self.assertIn('result.realScreens === expectedRealScreens', SCRIPT)

    def test_document_and_accessibility_tree_semantics_are_audited(self) -> None:
        self.assertIn("document.querySelectorAll('h1, h2, h3, h4, h5, h6')", SCRIPT)
        self.assertIn("client.send('Accessibility.getFullAXTree')", SCRIPT)
        self.assertIn("['banner', 'main', 'contentinfo', 'navigation']", SCRIPT)
        self.assertIn('navigation landmark labels are not unique', SCRIPT)
        self.assertIn('alt text is absent from accessibility tree', SCRIPT)

    def test_two_hundred_percent_text_resize_is_csp_compatible(self) -> None:
        self.assertIn("font-size: 200% !important", SCRIPT)
        self.assertIn('document.styleSheets', SCRIPT)
        self.assertIn('writableStyleSheet.insertRule', SCRIPT)
        self.assertNotIn('page.addStyleTag', SCRIPT)
        self.assertIn('text-resize-200.json', SCRIPT)
        self.assertIn("result.rootFontSize === '32px'", SCRIPT)
        self.assertIn('200% text resize causes horizontal overflow', SCRIPT)
        self.assertIn('text is clipped at 200% resize', SCRIPT)

    def test_tooling_is_pinned(self) -> None:
        self.assertIn('puppeteer-core@25.3.0', WORKFLOW)
        self.assertIn('actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0', WORKFLOW)
        # Accept only verified artifact upload SHAs, and exactly one upload step.
        allowed_pins = {
            'uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a',
            'uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9',
        }
        pins = [
            line.strip().split(' #', 1)[0]
            for line in WORKFLOW.splitlines()
            if line.strip().startswith('uses: actions/upload-artifact@')
        ]
        self.assertEqual(len(pins), 1, 'Expected one SHA-pinned artifact upload step')
        self.assertIn(pins[0], allowed_pins)


if __name__ == '__main__':
    unittest.main()
