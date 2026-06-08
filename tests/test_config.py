"""Tests for subject identity config and name-rule rendering."""

from pathlib import Path

from src.config.settings import Subject
from src.qa.agent import _build_name_rules


def test_subject_defaults_when_file_missing():
    subject = Subject.load(Path("does-not-exist.toml"))
    assert subject.name == "LeChristopher Blackwell"
    assert subject.preferred_names == ["Le", "LeChristopher"]
    assert subject.github_owner == "codeblackwell"


def test_subject_reads_custom_toml(tmp_path):
    f = tmp_path / "subject.toml"
    f.write_text(
        'name = "Ada Lovelace"\n'
        'preferred_names = ["Ada"]\n'
        "forbidden_names = []\n"
        'github_owner = "adalovelace"\n'
        'domain = "prove.example.com"\n'
    )
    subject = Subject.load(f)
    assert subject.name == "Ada Lovelace"
    assert subject.preferred_names == ["Ada"]
    assert subject.github_owner == "adalovelace"
    assert subject.domain == "prove.example.com"


def test_subject_partial_toml_falls_back_to_defaults(tmp_path):
    f = tmp_path / "subject.toml"
    f.write_text('github_owner = "someone"\n')
    subject = Subject.load(f)
    assert subject.github_owner == "someone"
    assert subject.name == "LeChristopher Blackwell"  # default preserved


def test_name_rules_default_block():
    rules = _build_name_rules(["Le", "LeChristopher"], ["Christopher", "Chris"])
    assert "NAME RULES (STRICT):" in rules
    assert '- Refer to the engineer as "Le" or "LeChristopher" ONLY.' in rules
    assert '- NEVER use "Christopher", "Chris", or any other abbreviation.' in rules


def test_name_rules_empty_when_no_preferred_names():
    assert _build_name_rules([], ["Chris"]) == ""


def test_name_rules_omits_forbidden_line_when_none():
    rules = _build_name_rules(["Ada"], [])
    assert '- Refer to the engineer as "Ada" ONLY.' in rules
    assert "NEVER use" not in rules
