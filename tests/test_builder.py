"""Comprehensive tests for geosite_russia builder logic."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from geosite_russia.build_lists import (
    dedupe_keep_order,
    is_ru_excluded_domain,
    merge_required_attrs,
    normalize_text_domain,
    parse_upstream_line,
    rule_matches_attrs,
    split_attrs,
    validate_output,
)

# Normal package imports — no sys.path hacks needed.
from geosite_russia.shared import ROOT_TAGS, load_domain_file, strip_inline_comment


class TestStripInlineComment(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(strip_inline_comment("example.com"), "example.com")

    def test_with_comment(self):
        self.assertEqual(strip_inline_comment("example.com # ads"), "example.com")

    def test_comment_only(self):
        self.assertEqual(strip_inline_comment("# comment only"), "")

    def test_empty(self):
        self.assertEqual(strip_inline_comment(""), "")

    def test_whitespace_and_comment(self):
        self.assertEqual(strip_inline_comment("  example.com  # tag  "), "example.com")


class TestLoadDomainFile(unittest.TestCase):
    def test_existing_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("# comment\nexample.com\ntest.org\n")
            path = Path(f.name)

        result = load_domain_file(path)
        self.assertEqual(result, ["example.com", "test.org"])
        path.unlink()

    def test_with_normalizer(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Example.COM\nhttps://test.org/path\n*.wildcard.net\n")
            path = Path(f.name)

        result = load_domain_file(path, normalize_text_domain)
        self.assertIn("example.com", result)
        self.assertIn("test.org", result)
        self.assertIn("wildcard.net", result)
        path.unlink()

    def test_nonexistent_file(self):
        result = load_domain_file(Path("/tmp/does_not_exist_12345.txt"))
        self.assertEqual(result, [])


class TestNormalizeTextDomain(unittest.TestCase):
    def test_plain_domain(self):
        self.assertEqual(normalize_text_domain("  example.com  "), "example.com")

    def test_lowercase(self):
        self.assertEqual(normalize_text_domain("Example.COM"), "example.com")

    def test_http_url(self):
        self.assertEqual(normalize_text_domain("http://example.com/path"), "example.com")

    def test_https_with_port(self):
        self.assertEqual(normalize_text_domain("https://sub.example.com:8080/foo"), "sub.example.com")

    def test_wildcard(self):
        self.assertEqual(normalize_text_domain("*.wildcard.org"), "wildcard.org")

    def test_dot_prefix(self):
        self.assertEqual(normalize_text_domain(".dotprefix.net"), "dotprefix.net")

    def test_comment_lines(self):
        self.assertIsNone(normalize_text_domain("# comment"))
        self.assertIsNone(normalize_text_domain("// comment"))
        self.assertIsNone(normalize_text_domain("; comment"))

    def test_empty(self):
        self.assertIsNone(normalize_text_domain(""))

    def test_underscore_in_label(self):
        self.assertIsNone(normalize_text_domain("invalid_name.com"))

    def test_local_suffix(self):
        self.assertIsNone(normalize_text_domain("localhost.local"))

    def test_internal_dns_name_passes_regex(self):
        # host.docker.internal is technically a valid domain per regex
        # even though it's not routable — validation happens at use-time
        self.assertEqual(normalize_text_domain("host.docker.internal"), "host.docker.internal")

    def test_path_in_url(self):
        self.assertEqual(normalize_text_domain("https://example.com/a/b/c?q=1"), "example.com")

    def test_ip_address(self):
        self.assertIsNone(normalize_text_domain("93.184.216.34"))

    def test_single_label(self):
        self.assertIsNone(normalize_text_domain("localhost"))

    def test_long_tld(self):
        # Regex allows up to 63 chars per label, so 10-char TLD is valid
        self.assertEqual(normalize_text_domain("example.abcdefghij"), "example.abcdefghij")


class TestIsRuExcludedDomain(unittest.TestCase):
    def test_yandex(self):
        self.assertTrue(is_ru_excluded_domain("yandex.ru"))

    def test_vk(self):
        self.assertTrue(is_ru_excluded_domain("vk.com"))
        self.assertTrue(is_ru_excluded_domain("sub.vk.com"))

    def test_mail_ru(self):
        self.assertTrue(is_ru_excluded_domain("mail.ru"))
        self.assertTrue(is_ru_excluded_domain("inbox.mail.ru"))

    def test_dzen(self):
        self.assertTrue(is_ru_excluded_domain("dzen.ru"))

    def test_punycode_tld(self):
        self.assertTrue(is_ru_excluded_domain("site.xn--p1ai"))

    def test_su_tld(self):
        self.assertTrue(is_ru_excluded_domain("example.su"))

    def test_international(self):
        self.assertFalse(is_ru_excluded_domain("google.com"))
        self.assertFalse(is_ru_excluded_domain("wikipedia.org"))
        self.assertFalse(is_ru_excluded_domain("amazon.com"))

    def test_known_suffix(self):
        self.assertTrue(is_ru_excluded_domain("mycdn.me"))
        self.assertTrue(is_ru_excluded_domain("cdn-vk.ru"))


class TestParseUpstreamLine(unittest.TestCase):
    def test_include(self):
        result = parse_upstream_line("include:category-ru @cn")
        self.assertEqual(result, ("include", "category-ru", {"cn"}))

    def test_rule_with_attrs(self):
        result = parse_upstream_line("example.com @ads @cn")
        self.assertEqual(result, ("rule", "example.com", {"ads", "cn"}))

    def test_rule_no_attrs(self):
        result = parse_upstream_line("example.com")
        self.assertEqual(result, ("rule", "example.com", set()))

    def test_comment(self):
        self.assertIsNone(parse_upstream_line("# inline comment only"))

    def test_empty(self):
        self.assertIsNone(parse_upstream_line(""))

    def test_whitespace_only(self):
        self.assertIsNone(parse_upstream_line("   "))


class TestDedupeKeepOrder(unittest.TestCase):
    def test_no_duplicates(self):
        items = ["a", "b", "c"]
        self.assertEqual(dedupe_keep_order(items), ["a", "b", "c"])

    def test_with_duplicates(self):
        items = ["a", "b", "a", "c", "b", "d"]
        self.assertEqual(dedupe_keep_order(items), ["a", "b", "c", "d"])

    def test_empty(self):
        self.assertEqual(dedupe_keep_order([]), [])


class TestSplitAttrs(unittest.TestCase):
    def test_no_attrs(self):
        base, attrs = split_attrs("example.com")
        self.assertEqual(base, "example.com")
        self.assertEqual(attrs, set())

    def test_one_attr(self):
        base, attrs = split_attrs("example.com @ads")
        self.assertEqual(base, "example.com")
        self.assertEqual(attrs, {"ads"})

    def test_multiple_attrs(self):
        base, attrs = split_attrs("example.com @ads @cn @region")
        self.assertEqual(base, "example.com")
        self.assertEqual(attrs, {"ads", "cn", "region"})

    def test_empty(self):
        base, attrs = split_attrs("")
        self.assertEqual(base, "")
        self.assertEqual(attrs, set())


class TestMergeRequiredAttrs(unittest.TestCase):
    def test_both_none(self):
        self.assertIsNone(merge_required_attrs(None, set()))
        self.assertIsNone(merge_required_attrs(None, None))

    def test_parent_only(self):
        result = merge_required_attrs({"cn"}, None)
        self.assertEqual(result, {"cn"})

    def test_local_only(self):
        result = merge_required_attrs(None, {"ads"})
        self.assertEqual(result, {"ads"})

    def test_both_present(self):
        result = merge_required_attrs({"cn"}, {"ads"})
        self.assertEqual(result, {"cn", "ads"})

    def test_parent_empty_set(self):
        result = merge_required_attrs(set(), {"ads"})
        self.assertEqual(result, {"ads"})


class TestRuleMatchesAttrs(unittest.TestCase):
    def test_no_required(self):
        self.assertTrue(rule_matches_attrs({"ads"}, None))
        self.assertTrue(rule_matches_attrs(set(), None))

    def test_subset(self):
        self.assertTrue(rule_matches_attrs({"ads", "cn"}, {"ads"}))

    def test_superset_ok(self):
        self.assertTrue(rule_matches_attrs({"ads", "cn", "region"}, {"ads", "cn"}))

    def test_missing(self):
        self.assertFalse(rule_matches_attrs({"cn"}, {"ads"}))


class TestRootTags(unittest.TestCase):
    def test_all_expected_tags(self):
        expected = {
            "category-ads-all",
            "category-ru",
            "telegram",
            "viber",
            "whatsapp",
            "meta",
            "facebook",
            "google",
            "supercell",
            "roblox",
            "apple",
            "private",
        }
        self.assertEqual(set(ROOT_TAGS), expected)

    def test_all_unique(self):
        self.assertEqual(len(ROOT_TAGS), len(set(ROOT_TAGS)))


class TestValidateOutput(unittest.TestCase):
    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            errors = validate_output({"category-ru": 1}, data_dir=Path(tmpdir))
            # Should report missing file since dir is empty
            self.assertIsInstance(errors, list)
            self.assertEqual(len(errors), 1)

    def test_minimum_thresholds_met(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            # Create a minimal file with 5 entries
            (data_dir / "small-tag").write_text("alpha\nbeta\ngamma\ndelta\nepsilon\n", encoding="utf-8")
            # Use a custom min_domains that expects 3 — should pass
            errors = validate_output({"small-tag": 3}, data_dir=data_dir)
            self.assertEqual(errors, [])

    def test_below_minimum(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            (data_dir / "small-tag").write_text("one\ntwo\n", encoding="utf-8")
            errors = validate_output({"small-tag": 3}, data_dir=data_dir)
            self.assertEqual(len(errors), 1)
            self.assertIn("small-tag", errors[0])
            self.assertIn("Only 2 domains", errors[0])


if __name__ == "__main__":
    unittest.main()
