"""Smoke tests for the markdown → Google Docs converter.

Run with: python -m pytest sync/test_md_to_docs.py
Or:       python sync/test_md_to_docs.py
"""

from __future__ import annotations

from md_to_docs import _parse_paragraphs, build_requests


def test_table_rendered_as_rows():
    md = """
| When | Who | What |
|---|---|---|
| Day one | CEM | Kickoff |
| Daily | CEM | Site visit |
""".strip()
    paras = _parse_paragraphs(md)
    texts = [p.text for p in paras]
    assert "When | Who | What" in texts, texts
    assert "--- | --- | ---" in texts, texts
    assert "Day one | CEM | Kickoff" in texts, texts
    assert "Daily | CEM | Site visit" in texts, texts

    header = next(p for p in paras if p.text == "When | Who | What")
    assert any("bold" in style and style["bold"] for (_s, _e, style) in header.text_runs), (
        "Header row cells should be bold"
    )


def test_table_preserves_inline_formatting():
    md = """
| Amount | Authority |
|---|---|
| Under $200 | CEM decides **independently** |
""".strip()
    paras = _parse_paragraphs(md)
    body_row = next(p for p in paras if "Under $200" in p.text)
    assert body_row.text == "Under $200 | CEM decides independently"
    bold_runs = [
        (s, e) for (s, e, style) in body_row.text_runs if style.get("bold")
    ]
    assert any(
        body_row.text[s:e] == "independently" for (s, e) in bold_runs
    ), f"Expected 'independently' bold, got runs={body_row.text_runs}"


def test_blockquote_preserved():
    md = "> Hi [Name], thanks for choosing us."
    paras = _parse_paragraphs(md)
    assert any(p.text.startswith("> Hi [Name]") for p in paras)


def test_ordered_and_unordered_lists():
    md = """
1. First step.
2. Second step.

- Bullet a
- Bullet b
""".strip()
    paras = _parse_paragraphs(md)
    numbered = [p for p in paras if p.list_kind == "number"]
    bullets = [p for p in paras if p.list_kind == "bullet"]
    assert [p.text for p in numbered] == ["First step.", "Second step."]
    assert [p.text for p in bullets] == ["Bullet a", "Bullet b"]


def test_build_requests_runs_clean_on_table_heavy_doc():
    md = """
# Title

## Section

| A | B |
|---|---|
| 1 | 2 |

> Script line.
""".strip()
    reqs = build_requests(md, "sops/test.md", existing_end_index=2)
    assert any("insertText" in r for r in reqs)
    inserted = next(r for r in reqs if "insertText" in r)["insertText"]["text"]
    assert "A | B" in inserted
    assert "--- | ---" in inserted
    assert "1 | 2" in inserted
    assert "> Script line." in inserted


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all tests passed")
