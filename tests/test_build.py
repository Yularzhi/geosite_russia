"""Tests for geosite_russia builder (offline, no network)."""

from __future__ import annotations

import pytest

from geosite_russia import build_lists, shared
from geosite_russia.build_singbox_rulesets import build_rule_set, parse_rule


# ── shared ────────────────────────────────────────────────────────────────


def test_strip_inline_comment():
    assert shared.strip_inline_comment("example.com # comment") == "example.com"
    assert shared.strip_inline_comment("# full") == ""
    assert shared.strip_inline_comment("  a.com  ") == "a.com"


def test_load_domain_file_filters_comments(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("a.com\n# c\n\nb.com # inline\n", encoding="utf-8")
    assert shared.load_domain_file(f) == ["a.com", "b.com"]
    assert shared.load_domain_file(tmp_path / "missing") == []


def test_root_tags_includes_ru_blocked():
    assert "ru-blocked" in shared.ROOT_TAGS
    assert set(build_lists.REQUIRED_MIN_DOMAINS) >= set(shared.ROOT_TAGS)


# ── normalize ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Example.COM:443", "example.com"),
        ("example.com:", "example.com"),
        ("example.com:abc", None),  # invalid port rejected
        ("::1", None),
        ("2001:db8::1", None),
        ("привет.рф", "xn--b1agh1afp.xn--p1ai"),
        ("XN--B1AGH1AFP.XN--P1AI", "xn--b1agh1afp.xn--p1ai"),
        ("bad_host.com", None),
        ("x.local", None),
        ("1.2.3.4", None),
    ],
)
def test_normalize_text_domain(raw, expected):
    assert build_lists.normalize_text_domain(raw) == expected


# ── upstream parsing ──────────────────────────────────────────────────────


def test_parse_upstream_line_include_with_attrs():
    assert build_lists.parse_upstream_line("include:google @ads") == ("include", "google", {"ads"})


def test_flatten_rules_resolves_includes_and_attrs(monkeypatch):
    pages = {
        "https://dlc/a": "include:b @ads\nkeep.com\n",
        "https://dlc/b": "full:x.com @ads\nkeyword:y @ads\nplain.com\n",
    }
    monkeypatch.setattr(build_lists, "DLC_BASE", "https://dlc/")
    monkeypatch.setattr(build_lists, "fetch_text", lambda url, **kw: pages[url])
    build_lists.clear_flatten_cache()
    try:
        # include:b @ads pulls only @ads rules from b; attrs are stripped from values
        assert build_lists.flatten_rules("a") == ["full:x.com", "keyword:y", "keep.com"]
    finally:
        build_lists.clear_flatten_cache()


def test_flatten_rules_cycle_safe(monkeypatch):
    pages = {"https://dlc/a": "include:b\n", "https://dlc/b": "include:a\nx.com\n"}
    monkeypatch.setattr(build_lists, "DLC_BASE", "https://dlc/")
    monkeypatch.setattr(build_lists, "fetch_text", lambda url, **kw: pages[url])
    build_lists.clear_flatten_cache()
    try:
        assert build_lists.flatten_rules("a") == ["x.com"]
    finally:
        build_lists.clear_flatten_cache()


def test_flatten_rules_cached(monkeypatch):
    calls = []
    monkeypatch.setattr(build_lists, "DLC_BASE", "https://dlc/")
    def fake_fetch(url, **kw):
        calls.append(url)
        return "x.com\n"
    monkeypatch.setattr(build_lists, "fetch_text", fake_fetch)
    build_lists.clear_flatten_cache()
    try:
        build_lists.flatten_rules("a")
        build_lists.flatten_rules("a")
        assert len(calls) == 1
    finally:
        build_lists.clear_flatten_cache()


# ── ru exclusion ──────────────────────────────────────────────────────────


def test_is_ru_excluded_domain():
    build_lists.get_config()
    assert build_lists.is_ru_excluded_domain("example.ru")
    assert build_lists.is_ru_excluded_domain("sub.yandex.ru")
    assert build_lists.is_ru_excluded_domain("vk.com")
    assert not build_lists.is_ru_excluded_domain("example.com")


# ── sing-box ──────────────────────────────────────────────────────────────


def test_parse_rule_variants():
    assert parse_rule("full:example.com") == ("domain", "example.com")
    assert parse_rule("keyword:ads") == ("domain_keyword", "ads")
    assert parse_rule("example.com") == ("domain_suffix", "example.com")
    assert parse_rule("domain:example.com") == ("domain_suffix", "example.com")
    assert parse_rule("include:other") is None
    assert parse_rule("# comment") is None


def test_build_rule_set(tmp_path, monkeypatch):
    (tmp_path / "t").write_text("full:a.com\nexample.com\nkeyword:ads\n", encoding="utf-8")
    monkeypatch.setattr("geosite_russia.build_singbox_rulesets.DATA_DIR", tmp_path)
    rs = build_rule_set("t")
    assert rs["version"] == 4
    flat = {k: v for r in rs["rules"] for k, v in r.items()}
    assert flat == {"domain": ["a.com"], "domain_suffix": ["example.com"], "domain_keyword": ["ads"]}


def test_validate_output_missing_and_min(tmp_path):
    (tmp_path / "a").write_text("x.com\n", encoding="utf-8")
    errs = build_lists.validate_output({"a": 5, "b": 1}, data_dir=tmp_path)
    assert any("[a] Only 1" in e for e in errs)
    assert any("[b] File missing" in e for e in errs)
    assert build_lists.validate_output({"a": 1}, data_dir=tmp_path) == []
