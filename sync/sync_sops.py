"""Sync Markdown SOPs from the repo into existing Google Docs.

This is the one-way bridge between GitHub (source of truth) and Google Drive
(distribution). It is invoked by the GitHub Actions workflow in
``.github/workflows/sync-sops-to-drive.yml`` but is also runnable locally for
testing.

Environment:
    GOOGLE_SERVICE_ACCOUNT_JSON   Full JSON of a service account key with
                                  access to edit the target Google Docs.

Usage:
    python sync/sync_sops.py --mapping sop-mapping.json sops/foo.md sops/bar.md
    python sync/sync_sops.py --mapping sop-mapping.json --all
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Iterable

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from md_to_docs import build_requests


SCOPES = ["https://www.googleapis.com/auth/documents"]
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2

log = logging.getLogger("sync_sops")


def _load_credentials():
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise SystemExit(
            "GOOGLE_SERVICE_ACCOUNT_JSON is not set. "
            "Provide the service-account key JSON via that env var."
        )
    info = json.loads(raw)
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)


def _load_mapping(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SystemExit(f"Mapping file {path} must be a JSON object")
    return data


def _document_end_index(docs_service, document_id: str) -> int:
    doc = docs_service.documents().get(documentId=document_id).execute()
    body = doc.get("body", {})
    content = body.get("content", [])
    if not content:
        return 2  # empty doc has a single trailing newline at index 1
    return content[-1].get("endIndex", 2)


def _apply_with_retry(docs_service, document_id: str, requests: list[dict]) -> None:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            docs_service.documents().batchUpdate(
                documentId=document_id,
                body={"requests": requests},
            ).execute()
            return
        except HttpError as exc:
            last_error = exc
            # 429/5xx are retryable; 4xx (except 429) are not.
            status = getattr(exc, "status_code", None) or exc.resp.status
            retryable = status == 429 or 500 <= status < 600
            log.warning(
                "batchUpdate failed for %s (attempt %d/%d, status=%s): %s",
                document_id,
                attempt,
                MAX_RETRIES,
                status,
                exc,
            )
            if not retryable or attempt == MAX_RETRIES:
                raise
            time.sleep(RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1)))
    if last_error:
        raise last_error


def sync_file(docs_service, repo_path: Path, source_path: str, document_id: str) -> None:
    if not repo_path.exists():
        # File was deleted in the commit we're syncing; never delete the Drive
        # copy automatically — surface it instead.
        log.error("Source file %s no longer exists; skipping. Remove the mapping entry manually if intended.", source_path)
        return

    markdown = repo_path.read_text(encoding="utf-8")
    end_index = _document_end_index(docs_service, document_id)
    requests = build_requests(
        markdown=markdown,
        source_path=source_path,
        existing_end_index=end_index,
    )
    log.info("Updating %s -> %s (%d requests)", source_path, document_id, len(requests))
    _apply_with_retry(docs_service, document_id, requests)
    log.info("Synced %s", source_path)


def _iter_targets(
    mapping: dict[str, str],
    explicit_paths: list[str],
    sync_all: bool,
) -> Iterable[tuple[str, str]]:
    if sync_all:
        return list(mapping.items())
    targets: list[tuple[str, str]] = []
    for raw in explicit_paths:
        normalized = raw.lstrip("./")
        if not normalized.endswith(".md"):
            continue
        doc_id = mapping.get(normalized)
        if not doc_id:
            log.error(
                "No Drive mapping for %s; add it to sop-mapping.json or remove the file from the trigger.",
                normalized,
            )
            continue
        targets.append((normalized, doc_id))
    return targets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mapping",
        default="sop-mapping.json",
        help="Path to the JSON file mapping repo paths to Google Doc IDs.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Sync every entry in the mapping (useful for backfills).",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root, used to resolve the paths in the mapping.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Explicit list of changed SOP paths to sync (relative to repo root).",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    mapping_path = Path(args.mapping)
    if not mapping_path.exists():
        log.error("Mapping file %s not found", mapping_path)
        return 2
    mapping = _load_mapping(mapping_path)

    targets = list(_iter_targets(mapping, args.paths, args.all))
    if not targets:
        log.info("No SOPs to sync.")
        return 0

    credentials = _load_credentials()
    docs_service = build("docs", "v1", credentials=credentials, cache_discovery=False)

    repo_root = Path(args.repo_root).resolve()
    failures = 0
    for source_path, document_id in targets:
        file_path = repo_root / source_path
        try:
            sync_file(docs_service, file_path, source_path, document_id)
        except Exception as exc:  # noqa: BLE001 - we log and continue per spec
            failures += 1
            log.exception("Failed to sync %s: %s", source_path, exc)

    if failures:
        log.error("%d SOP(s) failed to sync", failures)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
