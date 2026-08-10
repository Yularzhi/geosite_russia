from __future__ import annotations

import unittest

from scripts.build_lists import (
    is_ru_excluded_domain,
    normalize_text_domain,
    parse_upstream_line,
)
from scripts.build_singbox_rulesets import parse_rule


class TestDomainParsing(unittest.TestCase):
    def test_normalize_text_domain(self) -> None:
        self.assertEqual(normalize_text_domain("  example.com  "), "example.com")
        self.assertEqual(normalize_text_domain("http://example.com/path"), "example.com")
        self.assertEqual(normalize_text_domain("https://sub.example.com:8080/foo"), "sub.example.com")
        self.assertEqual(normalize_text_domain("*.wildcard.org"), "wildcard.org")
        self.assertEqual(normalize_text_domain(".dotprefix.net"), "dotprefix.net")
        self.assertIsNone(normalize_text_domain("# comment"))
        self.assertIsNone(normalize_text_domain("// comment"))
        self.assertIsNone(normalize_text_domain("invalid_domain_name"))
        self.assertIsNone(normalize_text_domain("localhost.local"))

    def test_is_ru_excluded_domain(self) -> None:
        self.assertTrue(is_ru_excluded_domain("yandex.ru"))
        self.assertTrue(is_ru_excluded_domain("sub.vk.com"))
        self.assertTrue(is_ru_excluded_domain("site.xn--p1ai"))
        self.assertTrue(is_ru_excluded_domain("example.su"))
        self.assertFalse(is_ru_excluded_domain("google.com"))
        self.assertFalse(is_ru_excluded_domain("wikipedia.org"))

    def test_parse_upstream_line(self) -> None:
        self.assertEqual(
            parse_upstream_line("include:category-ru @cn"),
            ("include", "category-ru", {"cn"}),
        )
        self.assertEqual(
            parse_upstream_line("example.com @ads @cn"),
            ("rule", "example.com", {"ads", "cn"}),
        )
        self.assertIsNone(parse_upstream_line("# inline comment only"))

    def test_parse_rule(self) -> None:
        self.assertEqual(parse_rule("full:example.com"), ("domain", "example.com"))
        self.assertEqual(parse_rule("keyword:test"), ("domain_keyword", "test"))
        self.assertEqual(parse_rule("regexp:^foo.*"), ("domain_regex", "^foo.*"))
        self.assertEqual(parse_rule("domain:example.com"), ("domain_suffix", "example.com"))
        self.assertEqual(parse_rule("example.com"), ("domain_suffix", "example.com"))
        self.assertIsNone(parse_rule("include:other-tag"))
        self.assertIsNone(parse_rule("geosite:other-tag"))


if __name__ == "__main__":
    unittest.main()
