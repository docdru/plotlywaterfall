"""Unit tests for scripts/ai_review.py (no network access)."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parents[1] / "ai_review.py"
_spec = importlib.util.spec_from_file_location("ai_review", _PATH)
assert _spec is not None
assert _spec.loader is not None
ai = importlib.util.module_from_spec(_spec)
sys.modules["ai_review"] = ai  # dataclasses need the module to be registered
_spec.loader.exec_module(ai)


def make_notebook(*sources: str, with_output: bool = True) -> str:
    cells = []
    for src in sources:
        cell: dict[str, object] = {
            "cell_type": "code",
            "source": src.splitlines(keepends=True),
            "metadata": {},
        }
        if with_output:
            cell["outputs"] = [{"data": {"image/png": "iVBORw0KGgo" * 1000}}]
        cells.append(cell)
    return json.dumps({"cells": cells, "metadata": {}, "nbformat": 4})


# --- notebooks ---------------------------------------------------------------


def test_notebook_to_text_drops_outputs():
    text = ai.notebook_to_text(make_notebook("import pandas as pd", "fig.show()"))
    assert "import pandas as pd" in text
    assert "fig.show()" in text
    assert "iVBORw0KGgo" not in text


def test_notebook_to_text_invalid_json_passthrough():
    assert ai.notebook_to_text("not json") == "not json"


def test_notebook_diff_shows_source_changes_only():
    old = make_notebook("x = 1")
    new = make_notebook("x = 2")
    diff = ai.notebook_diff(old, new, "examples/examples.ipynb")
    assert "-x = 1" in diff
    assert "+x = 2" in diff
    assert "iVBORw0KGgo" not in diff


def test_notebook_diff_outputs_only():
    diff = ai.notebook_diff(
        make_notebook("x = 1"), make_notebook("x = 1", with_output=False), "nb.ipynb"
    )
    assert diff == "(only outputs or metadata changed)\n"


def test_notebook_diff_added_file():
    assert "+x = 1" in ai.notebook_diff(None, make_notebook("x = 1"), "nb.ipynb")


# --- budget fitting ----------------------------------------------------------


def test_fit_to_budget_no_trim_when_small():
    notices = ai.Notices()
    diff, changed = ai.fit_to_budget("d" * 100, "r" * 100, ["### FILE: a\nx"], 10, notices)
    assert diff == "d" * 100
    assert changed == ["### FILE: a\nx"]
    assert notices.items == []


def test_fit_to_budget_trims_files_proportionally_and_lands_on_budget():
    notices = ai.Notices()
    files = [f"### FILE: f{i}\n" + "x" * 150_000 for i in range(5)]
    refs, pr_chars = "r" * 20_000, 4_000
    diff, changed = ai.fit_to_budget("d" * 30_000, refs, files, pr_chars, notices)
    total = len(diff) + len(refs) + pr_chars + sum(len(c) for c in changed)
    assert total <= ai.MAX_TOTAL_CHARS
    assert diff == "d" * 30_000  # files absorb the cut, diff stays whole
    assert all("[truncated for context budget" in c for c in changed)
    assert len(notices.items) == 1
    assert "5 file(s) truncated" in notices.items[0]


def test_fit_to_budget_trims_diff_when_files_cannot_absorb():
    notices = ai.Notices()
    files = [f"### FILE: f{i}\n" + "x" * 5_000 for i in range(10)]
    diff, _ = ai.fit_to_budget("d" * 600_000, "r" * 10_000, files, 4_000, notices)
    assert "[diff truncated for context budget" in diff
    assert any("diff truncated" in n for n in notices.items)


def test_fit_to_budget_fails_loudly_when_unreachable():
    with pytest.raises(ai.ReviewError, match="even after trimming"):
        ai.fit_to_budget("d" * 10, "r" * 600_000, [], 4_000, ai.Notices())


# --- rendering ---------------------------------------------------------------


def test_render_markdown_sections_and_neutralized_mentions():
    review = {
        "verdict": "request_changes",
        "summary": "Ping @docdru and @org/team please",
        "correctness": [
            {
                "severity": "high",
                "file": "src/plotlywaterfall/waterfall.py",
                "line": 42,
                "issue": "KeyError for y != 'Y'",
                "suggestion": "use self._y",
            }
        ],
        "api_docs": [{"file": "README.md", "reference": "README.md: Usage", "issue": "stale"}],
        "security": [],
        "surprises": ["not a dict, ignored"],
    }
    md = ai.render_markdown(review, "abcdef1234567", "mistral-large-2512", ai.Notices())
    assert md.startswith(ai.REVIEW_MARKER)
    assert "`abcdef1`" in md
    assert "**Verdict:** `request_changes`" in md
    assert "@docdru" not in md
    assert "@​docdru" in md
    assert "`high` **src/plotlywaterfall/waterfall.py:42**" in md
    assert "💡 use self._y" in md
    assert "_(README.md: Usage)_" in md
    assert "**🔒 Security & supply chain:** none found." in md
    assert "**⚠️ Surprising changes:** none found." in md


def test_render_markdown_unknown_verdict_and_notices():
    notices = ai.Notices()
    notices.warn("file x truncated")
    md = ai.render_markdown({"verdict": "lgtm!!"}, "a" * 40, "m", notices)
    assert "**Verdict:** `comment`" in md
    assert "Context notice" in md
    assert "- file x truncated" in md


# --- posting -----------------------------------------------------------------


class FakeGitHub:
    repo = "o/r"

    def __init__(self, comments):
        self.comments = comments
        self.sent = []

    def get_paginated(self, path, max_items=1_000):
        return self.comments

    def send(self, method, path, body):
        self.sent.append((method, path, body["body"]))


def test_post_review_creates_comment_when_none_exists():
    gh = FakeGitHub([{"id": 1, "user": {"login": "someone"}, "body": "hi"}])
    ai.post_review(gh, 7, "BODY")
    assert gh.sent == [("POST", "/repos/o/r/issues/7/comments", "BODY")]


def test_post_review_edits_own_comment_but_ignores_spoofed_marker():
    gh = FakeGitHub(
        [
            {"id": 1, "user": {"login": "mallory"}, "body": ai.REVIEW_MARKER + " fake"},
            {"id": 2, "user": {"login": ai.BOT_LOGIN}, "body": ai.REVIEW_MARKER + " old"},
        ]
    )
    ai.post_review(gh, 7, "BODY")
    assert gh.sent == [("PATCH", "/repos/o/r/issues/comments/2", "BODY")]


# --- Mistral call ------------------------------------------------------------


def mistral_reply(content, finish_reason="stop"):
    return json.dumps(
        {"choices": [{"message": {"content": content}, "finish_reason": finish_reason}]}
    ).encode()


def test_call_mistral_retries_on_rate_limit(monkeypatch):
    replies = iter([(429, b"slow down"), (200, mistral_reply('{"verdict": "approve"}'))])
    monkeypatch.setattr(ai, "http", lambda *a, **k: next(replies))
    monkeypatch.setattr(ai.time, "sleep", lambda s: None)
    assert ai.call_mistral("key", "model", "msg") == {"verdict": "approve"}


@pytest.mark.parametrize(
    ("status", "payload", "match"),
    [
        (401, b"unauthorized", "MISTRAL_API_KEY"),
        (400, b"too big", "400"),
        (200, mistral_reply('{"verdict": "app', finish_reason="length"), "max_tokens"),
        (200, mistral_reply("not json"), "unparseable"),
        (200, mistral_reply("[1, 2]"), "not an object"),
    ],
)
def test_call_mistral_errors_are_fatal(monkeypatch, status, payload, match):
    monkeypatch.setattr(ai, "http", lambda *a, **k: (status, payload))
    with pytest.raises(ai.ReviewError, match=match):
        ai.call_mistral("key", "model", "msg", retries=1)


def test_run_requires_mistral_key_unless_dry_run(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    with pytest.raises(ai.ReviewError, match="MISTRAL_API_KEY is not set"):
        ai.run(["--pr", "1"])
