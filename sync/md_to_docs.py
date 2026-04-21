"""Convert Markdown into a Google Docs ``batchUpdate`` request body.

The converter emits a single ``insertText`` request that contains the whole
document, followed by targeted style/paragraph/bullet requests. Every index
refers to the final document state because Google Docs applies each request in
order and the style requests are issued after the text has been inserted.

Supported constructs:
    - ATX headings (# .. ######) -> HEADING_1..HEADING_6
    - Paragraphs
    - Unordered lists (- item)
    - Ordered lists (1. item)
    - Inline bold (**x** / __x__) and italic (*x* / _x_)
    - Inline code spans (wrapped with a mono font style)

Anything more exotic (tables, images, block quotes, nested lists more than two
levels deep) is rendered as plain text so the doc is never broken.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.token import Token


HEADING_STYLES = {
    1: "HEADING_1",
    2: "HEADING_2",
    3: "HEADING_3",
    4: "HEADING_4",
    5: "HEADING_5",
    6: "HEADING_6",
}


@dataclass
class Paragraph:
    """A logical paragraph in the output doc.

    ``text`` never contains a trailing newline; the builder appends one when it
    serialises paragraphs to the single ``insertText`` payload.
    """

    text: str
    style: str = "NORMAL_TEXT"  # or HEADING_N / metadata values
    list_kind: str | None = None  # "bullet" or "number"
    list_group: int | None = None  # contiguous list items share a group id
    text_runs: list[tuple[int, int, dict[str, Any]]] = field(default_factory=list)


def _collect_inline(token: Token) -> tuple[str, list[tuple[int, int, dict[str, Any]]]]:
    """Flatten a markdown-it ``inline`` token into plain text + style runs."""
    text_parts: list[str] = []
    runs: list[tuple[int, int, dict[str, Any]]] = []
    style_stack: list[str] = []
    cursor = 0

    def add_text(value: str) -> None:
        nonlocal cursor
        if not value:
            return
        start = cursor
        text_parts.append(value)
        cursor += len(value)
        if style_stack:
            style: dict[str, Any] = {}
            if "strong" in style_stack:
                style["bold"] = True
            if "em" in style_stack:
                style["italic"] = True
            if "code" in style_stack:
                style["weightedFontFamily"] = {"fontFamily": "Roboto Mono"}
            runs.append((start, cursor, style))

    for child in token.children or []:
        t = child.type
        if t == "text":
            add_text(child.content)
        elif t == "softbreak" or t == "hardbreak":
            add_text(" ")
        elif t == "code_inline":
            style_stack.append("code")
            add_text(child.content)
            style_stack.pop()
        elif t in ("strong_open", "em_open"):
            style_stack.append("strong" if t == "strong_open" else "em")
        elif t in ("strong_close", "em_close"):
            if style_stack:
                style_stack.pop()
        elif t == "link_open":
            # Render link text inline; we don't hyperlink to keep requests simple.
            pass
        elif t == "link_close":
            pass
        elif t == "image":
            add_text(child.content or "[image]")
        else:
            if child.content:
                add_text(child.content)

    return "".join(text_parts), runs


def _parse_paragraphs(markdown: str) -> list[Paragraph]:
    md = MarkdownIt("commonmark").enable("table")
    tokens = md.parse(markdown)
    paragraphs: list[Paragraph] = []

    i = 0
    list_group_counter = 0
    list_stack: list[tuple[str, int]] = []  # (kind, group_id)

    while i < len(tokens):
        tok = tokens[i]
        if tok.type == "heading_open":
            level = int(tok.tag[1])
            inline = tokens[i + 1]
            text, runs = _collect_inline(inline)
            paragraphs.append(
                Paragraph(
                    text=text,
                    style=HEADING_STYLES.get(level, "NORMAL_TEXT"),
                    text_runs=runs,
                )
            )
            i += 3  # heading_open, inline, heading_close
        elif tok.type == "paragraph_open":
            inline = tokens[i + 1]
            text, runs = _collect_inline(inline)
            kind, group_id = list_stack[-1] if list_stack else (None, None)
            paragraphs.append(
                Paragraph(
                    text=text,
                    style="NORMAL_TEXT",
                    list_kind=kind,
                    list_group=group_id,
                    text_runs=runs,
                )
            )
            i += 3
        elif tok.type == "bullet_list_open":
            list_group_counter += 1
            list_stack.append(("bullet", list_group_counter))
            i += 1
        elif tok.type == "ordered_list_open":
            list_group_counter += 1
            list_stack.append(("number", list_group_counter))
            i += 1
        elif tok.type in ("bullet_list_close", "ordered_list_close"):
            if list_stack:
                list_stack.pop()
            i += 1
        elif tok.type in ("list_item_open", "list_item_close"):
            i += 1
        elif tok.type == "fence" or tok.type == "code_block":
            for line in tok.content.rstrip("\n").split("\n"):
                paragraphs.append(
                    Paragraph(
                        text=line or " ",
                        style="NORMAL_TEXT",
                        text_runs=[(0, len(line), {"weightedFontFamily": {"fontFamily": "Roboto Mono"}})] if line else [],
                    )
                )
            i += 1
        elif tok.type == "hr":
            paragraphs.append(Paragraph(text="—" * 20, style="NORMAL_TEXT"))
            i += 1
        elif tok.type == "blockquote_open":
            # Collect nested paragraphs until matching close.
            depth = 1
            i += 1
            while i < len(tokens) and depth > 0:
                inner = tokens[i]
                if inner.type == "blockquote_open":
                    depth += 1
                elif inner.type == "blockquote_close":
                    depth -= 1
                elif inner.type == "paragraph_open":
                    text, runs = _collect_inline(tokens[i + 1])
                    paragraphs.append(
                        Paragraph(
                            text="> " + text,
                            style="NORMAL_TEXT",
                            text_runs=[(start + 2, end + 2, style) for (start, end, style) in runs],
                        )
                    )
                    i += 2  # advance past inline + paragraph_close below
                i += 1
        else:
            i += 1

    return paragraphs


def _metadata_paragraphs(source_path: str, timestamp: datetime | None = None) -> list[Paragraph]:
    ts = (timestamp or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M UTC")
    line1 = f"Last updated: {ts}"
    line2 = f"Source: GitHub ({source_path})"
    runs = [(0, len(line1), {"italic": True, "foregroundColor": {"color": {"rgbColor": {"red": 0.4, "green": 0.4, "blue": 0.4}}}})]
    runs2 = [(0, len(line2), {"italic": True, "foregroundColor": {"color": {"rgbColor": {"red": 0.4, "green": 0.4, "blue": 0.4}}}})]
    return [
        Paragraph(text=line1, style="NORMAL_TEXT", text_runs=runs),
        Paragraph(text=line2, style="NORMAL_TEXT", text_runs=runs2),
    ]


def build_requests(
    markdown: str,
    source_path: str,
    existing_end_index: int,
    timestamp: datetime | None = None,
) -> list[dict[str, Any]]:
    """Build a list of Docs ``batchUpdate`` requests.

    ``existing_end_index`` is the ``endIndex`` of the last structural element in
    the current document as returned by ``documents.get``. Google Docs always
    keeps a trailing newline at position ``endIndex - 1`` that cannot be
    deleted, so we only clear the range ``[1, existing_end_index - 1)``.
    """
    paragraphs = _metadata_paragraphs(source_path, timestamp) + _parse_paragraphs(markdown)
    if not paragraphs:
        paragraphs = [Paragraph(text=" ")]

    requests: list[dict[str, Any]] = []

    # 1. Clear existing body content.
    if existing_end_index > 2:
        requests.append(
            {
                "deleteContentRange": {
                    "range": {"startIndex": 1, "endIndex": existing_end_index - 1}
                }
            }
        )

    # 2. Build a single text blob and track per-paragraph ranges.
    text_blob_parts: list[str] = []
    ranges: list[tuple[int, int, Paragraph]] = []
    cursor = 1  # Docs body starts at index 1
    for para in paragraphs:
        start = cursor
        line = para.text + "\n"
        text_blob_parts.append(line)
        cursor += len(line)
        ranges.append((start, cursor, para))

    blob = "".join(text_blob_parts)
    requests.append({"insertText": {"location": {"index": 1}, "text": blob}})

    # 3. Reset paragraph styles for every inserted paragraph so we don't inherit
    #    old formatting, then apply heading styles where needed.
    for start, end, para in ranges:
        requests.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "paragraphStyle": {"namedStyleType": para.style},
                    "fields": "namedStyleType",
                }
            }
        )

    # 4. Apply text styling for inline runs (bold/italic/code).
    for start, _end, para in ranges:
        for run_start, run_end, style in para.text_runs:
            if run_end <= run_start:
                continue
            requests.append(
                {
                    "updateTextStyle": {
                        "range": {
                            "startIndex": start + run_start,
                            "endIndex": start + run_end,
                        },
                        "textStyle": style,
                        "fields": ",".join(sorted(style.keys())),
                    }
                }
            )

    # 5. Group contiguous list paragraphs and attach bullets.
    current_group: int | None = None
    group_start: int | None = None
    group_end: int | None = None
    group_kind: str | None = None

    def flush_group() -> None:
        nonlocal current_group, group_start, group_end, group_kind
        if current_group is not None and group_start is not None and group_end is not None:
            preset = (
                "BULLET_DISC_CIRCLE_SQUARE"
                if group_kind == "bullet"
                else "NUMBERED_DECIMAL_ALPHA_ROMAN"
            )
            requests.append(
                {
                    "createParagraphBullets": {
                        "range": {"startIndex": group_start, "endIndex": group_end},
                        "bulletPreset": preset,
                    }
                }
            )
        current_group = None
        group_start = None
        group_end = None
        group_kind = None

    for start, end, para in ranges:
        if para.list_group is None:
            flush_group()
            continue
        if para.list_group != current_group:
            flush_group()
            current_group = para.list_group
            group_kind = para.list_kind
            group_start = start
        group_end = end
    flush_group()

    return requests
