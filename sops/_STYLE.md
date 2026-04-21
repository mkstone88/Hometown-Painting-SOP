# SOP Style Guide

**Status:** Living document. Update when we agree on a new pattern.
**Applies to:** Every Markdown file under `sops/**` that gets synced to a
Google Doc via the sync workflow.

## Why this exists

Every SOP a teammate opens in Drive should feel like it came from the same
playbook: same header at the top, same section names, same voice. This file
is the style reference. `_template.md` is the fill-in-the-blanks version.

When you're writing a new SOP, start with `_template.md` and follow this
guide for any judgment calls.

## File naming

- Lowercase. Hyphens between words. No spaces.
- `kebab-case.md` — e.g. `pre-job-walkthrough.md`, `cem-intro-call.md`.
- File lives under `sops/<system>/` — one of: `production/`, `sales/`,
  `marketing/`, `appointment-setting/`.
- Files prefixed with `_` are meta (this guide, the template) and are not
  synced to Drive.

## Document structure

Every SOP is built out of the same blocks, in this order:

1. **Title** — one `# H1` line, title case, no trailing punctuation.
2. **Metadata block** — Owner / Applies to / Related (see below).
3. **Purpose** — always `## Purpose`.
4. **Scope** — `## Scope` when the boundaries aren't obvious from Applies to.
5. **Body sections** — the working content. Pick from the section library.
6. **Revision Notes** — always last, always `## Revision Notes`.

### Metadata block

Immediately after the title, before the first `##` heading:

```
**Owner:** <Role>

**Applies to:** <When this SOP is invoked>

**Related:** <comma-separated filenames of related SOPs>
```

**Put a blank line between each field.** The Drive converter treats
consecutive lines as one paragraph and will cram them onto a single line.
Blank lines make each field its own paragraph.

Required fields:

- **Owner** — the role that runs this SOP (e.g. *CEM*, *Crew Leader*,
  *Sales*). Not a person's name.
- **Applies to** — the trigger: what event or condition invokes the SOP.

One of these, as appropriate:

- **Related** — filenames of closely related SOPs (default for most SOPs).
- **Source** — origin reference for imported / master documents (only
  `customer-journey.md` currently).
- **Status** — `Draft`, or a note about unresolved workflow (e.g. Photo
  Management). Omit on stable SOPs.

More than one is allowed. Skip fields that don't apply.

### Title casing

- `# Customer Journey` — yes
- `# CEM Intro Call` — yes (keep acronyms uppercase)
- `# customer-journey` — no
- `# CUSTOMER JOURNEY` — no

### Revision Notes

Always the last section. One bullet per change, most recent at the top:

```
## Revision Notes

- 2026-04 — Initial version, extracted from Customer Journey Phase 1.
- 2026-05 — Added the NPS response matrix.
```

Date format: `YYYY-MM` is enough for most changes. Use `YYYY-MM-DD` for
changes where the day matters (e.g. a policy changeover).

## Section library

Pick sections that fit. Not every SOP needs every section.

### `## Purpose` *(required)*

One or two short paragraphs. Why this SOP exists and what outcome it drives.
Written for a new hire who's never run it before.

### `## Scope` *(optional)*

When the SOP applies — and when it doesn't. Use when Applies to alone leaves
ambiguity.

### `## Procedure` *(for procedural SOPs)*

A numbered list. One action per item. Keep each item short enough that a
CEM reading it on their phone can follow along.

### `## <Specific Thing>` *(for forms, scripts, emails, texts)*

Use a specific, descriptive heading. The table below is the canon:

| Content | Heading to use | Notes |
| --- | --- | --- |
| Phone call talking points | `## Script` | One blockquote, full script. |
| Text message | `## Text Template` | One blockquote. |
| Email | `## Email Template` | Subject on its own `> ` line first. |
| Paper or CRM form | `## Form Copy` | Includes fields and signature lines. |
| Multiple related scripts | Sub-headings under `## Scripts` | One `### Name` per script. |

### `## Principles` *(optional)*

Bulleted list of short, opinionated rules. Each bullet opens with a **bold
phrase.** followed by a sentence. Use for SOPs where voice and judgment
matter more than steps.

### `## When To Escalate` *(optional)*

Any SOP that references decisions with a cost dimension. Usually a small
table mirroring the CEM Authority matrix in `customer-journey.md`.

### `## System Gaps` *(for draft SOPs only)*

Bullet the dependencies — artifacts, tools, or processes this SOP needs but
which don't exist yet. Delete the section when the gaps are closed.

### `## Notes` *(optional, sparingly)*

A catch-all for clarifications that don't belong in Procedure. Prefer a
named section over a bucket of notes.

## Voice and tone

- **Second-person imperative** in Procedure steps: "Send the text," "Walk
  the site," "Do not wait."
- **Short sentences.** Read it aloud — if you run out of breath, cut it.
- **Specific over generic.** "Finished prep on the east side" beats "made
  progress." Give real examples wherever a script or template appears.
- **No filler.** Skip "Please be aware that" and "it is important to note
  that." Just say the thing.
- **No emojis.** Anywhere. SOPs are evergreen; trends are not.

## Formatting rules

### Headings

- `#` for the SOP title. Exactly one per file, at the very top.
- `##` for top-level sections.
- `###` for sub-sections within a section (e.g. Phase 1, Phase 2 inside
  Customer Journey).
- Never skip levels (no `#` → `###`).

### Lists

- **Numbered lists** for sequences where the order matters (procedures).
- **Bulleted lists** everywhere else (principles, checklists, references).
- Keep list items to one or two sentences. Break long items into separate
  steps.
- Start each item with a capital letter. End with a period.

### Blockquotes (scripts, emails, texts, form copy)

Wrap verbatim language — scripts, templates, customer-facing copy — in a
blockquote. The convention is a **label line** in bold, a blank quote line,
then the content:

```
> **Daily update text**
>
> Hi [Name]! Quick update from your project — the crew finished
> [what was done today] today and is planning to tackle
> [what's next] tomorrow. Everything looking good from your end?
```

For multi-paragraph scripts (emails), separate paragraphs with a blank `>`
line inside the blockquote.

### Tables

**Tables work in the sync converter** — rows become plain text separated by
` | `, with the header row bolded and a `---` divider row beneath.

Use tables for:

- Small reference grids (2–5 columns, ≤15 rows).
- Authority matrices, NPS response matrices, communication cadence.

Don't use tables for:

- Anything over ~5 columns — it won't fit on a phone screen.
- Content that's really a bulleted list in disguise.

### Emphasis

- `**bold**` for imperatives, role names at first mention, and labels in
  blockquotes.
- `*italic*` sparingly — usually for an aside, a *like this* emphasis, or a
  document/tool name.
- Do not use `**bold italic**` — it renders the same as bold.

### Placeholders

Wrap placeholders in square brackets: `[Name]`, `[Day, Date]`,
`[color/project detail]`. A reader should never wonder whether a word is
literal or a fill-in.

### What the converter will NOT render

Don't spend effort on features that get dropped silently or flattened:

- Images — rendered as placeholder text `[image]`.
- Hyperlinks — the anchor text is kept; the URL is dropped. Reference
  other SOPs by filename, not URL.
- Nested lists more than two levels deep.
- Footnotes, definition lists, task lists (`- [ ]`) — task lists render as
  plain bullets, not interactive checkboxes.
- HTML tags — ignored.

## Cross-references

Link related SOPs by filename in backticks:

```
See `handling-onsite-issues.md` for the escalation path.
```

Not as a Markdown link, not as a Google Doc URL. Filenames are stable; Doc
URLs change, hyperlinks don't render.

## Whitespace and line length

- **Hard-wrap body paragraphs around 76 characters.** Easier to review in
  GitHub diffs. Paragraph breaks are blank lines.
- **Do not hard-wrap inside blockquote scripts** if the wrap would cut a
  sentence awkwardly. Readability wins.
- Always a blank line around `##` / `###` headings.
- Always a blank line between the metadata fields (Owner, Applies to,
  Related).

## When to create a new SOP

- **New SOP** when the content describes a distinct repeatable action a
  role performs.
- **Extend an existing SOP** when the content is a variation of an already
  documented action.
- **A policy / principle** (not an action) lives inside the Customer
  Journey or a relevant SOP — not its own file.
- If in doubt, write it as a new file. Merging two SOPs later is easier
  than splitting one.

## Checklist before you commit

- [ ] Title is `# Title Case` with no trailing punctuation.
- [ ] Metadata block has **blank lines between fields.**
- [ ] `## Purpose` exists.
- [ ] `## Revision Notes` is the last section, with today's entry at top.
- [ ] Filenames in `Related:` actually exist.
- [ ] Any Doc ID is in `sop-mapping.json` (for brand-new SOPs only).
- [ ] Ran `python sync/test_md_to_docs.py` if you touched the converter.
