# Hometown Painting SOPs

One-way sync of Standard Operating Procedures from this repo into existing
Google Docs. GitHub is the source of truth; Google Drive is read-only
distribution for the team.

```
repo (markdown)  ──►  GitHub Actions  ──►  Google Docs API  ──►  existing Doc
```

## Repository layout

| Path | Purpose |
|------|---------|
| `sops/*.md` | The SOPs. Edit these; nothing else. |
| `sop-mapping.json` | Maps each `sops/*.md` path to the Google Doc ID it targets. |
| `sync/sync_sops.py` | Entry point called by CI. Runnable locally for testing. |
| `sync/md_to_docs.py` | Converts Markdown into Docs `batchUpdate` requests. |
| `.github/workflows/sync-sops-to-drive.yml` | Triggers the sync on push. |

## How the sync works

1. On every push to `main` that touches `sops/**.md`, the workflow checks out
   the repo and detects the changed files.
2. For each changed file it looks up the Doc ID in `sop-mapping.json`.
3. It fetches the target Doc to find the current end index, then issues a
   single `batchUpdate` that:
   - deletes the existing body,
   - inserts a metadata header (`Last updated: …`, `Source: GitHub (<path>)`),
   - inserts the converted SOP content,
   - applies heading styles, bold/italic runs, and list bullets/numbers.
4. The Doc's file ID, sharing settings, and URL are preserved — only its body
   changes, so Google Docs version history captures each update.

Files without a mapping are logged as errors and skipped; the system never
creates new Docs automatically.

## One-time setup

1. Create a Google Cloud service account and enable the **Google Docs API**.
2. Download the JSON key for the service account.
3. For each target Doc, share it with the service account's email with
   **Editor** access.
4. In GitHub → repo Settings → Secrets → Actions, add a secret named
   `GOOGLE_SERVICE_ACCOUNT_JSON` containing the full JSON key.
5. Populate `sop-mapping.json` with one entry per SOP:

   ```json
   {
     "sops/interior-painting.md": "1aBcDeFgHiJkLmNoPqRsTuVwXyZ01234567",
     "sops/exterior-painting.md": "1ZyXwVuTsRqPoNmLkJiHgFeDcBa98765432"
   }
   ```

## Adding a new SOP

1. Create the Google Doc in Drive (this is the only time a human creates a
   Doc). Share it with the service-account email.
2. Copy the Doc's file ID from its URL.
3. Add the `"sops/<file>.md": "<doc-id>"` entry to `sop-mapping.json`.
4. Commit the new Markdown file + mapping change together. The workflow will
   populate the Doc on push.

## Running locally

```bash
pip install -r sync/requirements.txt
export GOOGLE_SERVICE_ACCOUNT_JSON="$(cat path/to/key.json)"

# Sync specific files
python sync/sync_sops.py sops/interior-painting.md

# Sync everything in the mapping
python sync/sync_sops.py --all
```

## Manual full resync

Use the workflow's **Run workflow** button (workflow_dispatch) with
`sync_all=true` to push every mapped SOP to Drive. Useful after a template
change.

## Supported Markdown

- `#`…`######` headings (mapped to `HEADING_1`…`HEADING_6`)
- Paragraphs with inline `**bold**`, `*italic*`, and `` `code` ``
- Unordered lists (`-`, `*`)
- Ordered lists (`1.`)
- Fenced code blocks (rendered as monospace paragraphs)
- Block quotes (rendered with a leading `> ` prefix)

More exotic constructs (tables, images, nested deep lists) render as plain
text so the sync never fails.

## Error handling

| Situation | Behaviour |
|-----------|-----------|
| Mapping missing for a changed file | Logged as an error; file skipped. |
| `batchUpdate` returns 429 / 5xx | Retried up to 3 times with exponential backoff. |
| `batchUpdate` returns other 4xx | Logged; that file is skipped, others continue. |
| Source `.md` was deleted | Logged; the Drive Doc is **not** deleted automatically. |

The workflow exits non-zero if any file failed, so CI surfaces failures.

## Stretch goals

Not implemented yet — easy add-ons if needed:

- Slack/email notifications on success or failure.
- Auto-creating a Doc for new SOPs (would change the "never create duplicates"
  contract, so is opt-in only).
- A committed `sync-log.md` updated by the workflow.
