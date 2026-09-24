#!/usr/bin/env python3
"""Shared loader/validator for tools/predicate_anchor_resolutions.json.

The fallback-anchor cache is a derived, audited, deterministic, VERSIONED
artifact. It is committed to the repository so that a normal clone of
NounBank.DS can render all 145 pages and run the REL audit without a local
checkout of the DANTEStocks legacy corpus. The legacy corpus remains the
authority for how the cache was PRODUCED and can be used to re-verify it,
but it is not a runtime dependency for consuming it.

This module exposes two independently-callable levels of trust:

  A. LOCAL VALIDATION (mandatory, filesystem-independent w.r.t. the legacy
     corpus) - `PredicateAnchorCache.get_validated()`. This is what the
     renderer and the audit script use. It never reads the DANTEStocks
     corpus and works identically in a fresh clone. Any failure here is a
     hard failure for that instance - the caller must not render a guess.

  B. AUTHORITY VERIFICATION (optional/strict) - `verify_authority()`. This
     re-hashes the actual legacy CoNLL-U files and compares them with the
     hashes recorded in the cache header. It is only ever invoked
     explicitly (by the resolver, or by a human running a reproducibility
     check) and is never a precondition for (A). When the legacy corpus is
     not available on disk, this returns "NOT_AVAILABLE" - which is not the
     same thing as the cache being invalid.
"""
import hashlib
import json
import os
from pathlib import Path

SCHEMA_VERSION_SUPPORTED = 2

RESOLUTIONS_PATH = Path("tools/predicate_anchor_resolutions.json")

# Provenance fields every entry must carry, in addition to the anchor
# fields (form/char_start/char_end) that (A) checks against the live text.
REQUIRED_PROVENANCE_FIELDS = (
    "sent_ID",
    "lemma",
    "ordinal",
    "legacy_source_file",
    "legacy_token_id",
    "legacy_form",
    "candidate_route",
    "text_sha256",
    "method",
)

ENV_CORPUS_DIR = "NOUNBANK_DS_DANTE_LEGACY_DIR"
# Dev-convenience default only - never a contract. See resolve_corpus_dir().
_DEV_DEFAULT_CORPUS_DIR = Path(
    "/home/bryan/workspace/nounbank_ds_authority/DANTEStocks_legacy_v1/corpus"
)
CORPUS_FILENAMES = {
    "train": "DANTEStocks-train.conllu",
    "dev": "DANTEStocks-dev.conllu",
    "test": "DANTEStocks-test.conllu",
}


def resolve_corpus_dir(cli_value=None):
    """Precedence for locating the DANTEStocks legacy corpus, none of which
    is a contract the renderer relies on:
      1. an explicit --corpus-dir value passed by the caller;
      2. the NOUNBANK_DS_DANTE_LEGACY_DIR environment variable;
      3. a hardcoded local default, kept only as a development convenience
         on this machine - not something a fresh clone can rely on.
    Returns a Path that may or may not exist; callers decide what "not
    available" means for them (see verify_authority)."""
    if cli_value:
        return Path(cli_value)
    env_value = os.environ.get(ENV_CORPUS_DIR)
    if env_value:
        return Path(env_value)
    return _DEV_DEFAULT_CORPUS_DIR


def corpus_files(corpus_dir):
    corpus_dir = Path(corpus_dir)
    return {name: corpus_dir / fname for name, fname in CORPUS_FILENAMES.items()}


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_authority_hashes(corpus_dir):
    """Hash the three legacy CoNLL-U files under corpus_dir. Raises
    FileNotFoundError (not a CacheIntegrityError) if they aren't there -
    "not present" and "present but wrong" are different situations."""
    files = corpus_files(corpus_dir)
    missing = [str(p) for p in files.values() if not p.exists()]
    if missing:
        raise FileNotFoundError(f"legacy corpus file(s) not found: {missing}")
    return {name: sha256_file(p) for name, p in files.items()}


class CacheIntegrityError(RuntimeError):
    pass


def _parse_ordinal_strict(instance_id):
    """Same strict parsing rule as the resolver: no silent default, no
    clamp. Returns int ordinal >= 1 or raises."""
    parts = instance_id.rsplit("::", 1)
    if len(parts) != 2:
        raise CacheIntegrityError(f"malformed instance_id (no '::'): {instance_id!r}")
    tail = parts[1]
    if not tail.isdigit():
        raise CacheIntegrityError(f"malformed ordinal in instance_id: {instance_id!r}")
    ordinal = int(tail)
    if ordinal < 1:
        raise CacheIntegrityError(f"ordinal < 1 in instance_id: {instance_id!r}")
    return ordinal


class PredicateAnchorCache:
    def __init__(self, path=RESOLUTIONS_PATH):
        self.path = Path(path)
        self._raw = None
        if self.path.exists():
            self._raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._validate_container_local()

    # ---------------- A. LOCAL VALIDATION (mandatory) ----------------

    def _validate_container_local(self):
        """Structural checks on the cache file itself. Filesystem-
        independent w.r.t. the legacy corpus: only reads the cache JSON
        already loaded into self._raw. Runs unconditionally, even in a
        fresh clone with no DANTEStocks checkout."""
        if self._raw.get("schema_version") != SCHEMA_VERSION_SUPPORTED:
            raise CacheIntegrityError(
                f"unsupported cache schema_version={self._raw.get('schema_version')!r}; "
                f"expected {SCHEMA_VERSION_SUPPORTED}"
            )
        authority = self._raw.get("authority") or {}
        for key in ("train_sha256", "dev_sha256", "test_sha256"):
            if not authority.get(key):
                raise CacheIntegrityError(f"cache authority header missing {key}")
        if not isinstance(self._raw.get("entries"), dict):
            raise CacheIntegrityError("cache missing 'entries' object")

    def entries(self):
        return (self._raw or {}).get("entries", {})

    def recorded_authority_hashes(self):
        return dict((self._raw or {}).get("authority") or {})

    def get_validated(self, instance_id, sent_id, lemma, text):
        """MANDATORY LOCAL VALIDATION. Returns
        {"form", "char_start", "char_end"} for instance_id if, and only if,
        the cache entry passes every binding check against the CURRENT
        jsons state. Returns None (never guesses) when there is simply no
        entry for this instance_id. Raises CacheIntegrityError - a hard
        failure - on any entry that exists but does not bind correctly.

        Never touches the legacy corpus on disk. Safe to call from a fresh
        clone with no DANTEStocks checkout at all."""
        if not self._raw:
            return None
        entry = self.entries().get(instance_id)
        if not entry:
            return None
        if entry.get("sent_ID") != sent_id:
            raise CacheIntegrityError(f"{instance_id}: cache sent_ID mismatch")
        if entry.get("lemma") != lemma:
            raise CacheIntegrityError(f"{instance_id}: cache lemma mismatch")
        expected_ordinal = _parse_ordinal_strict(instance_id)
        if entry.get("ordinal") != expected_ordinal:
            raise CacheIntegrityError(f"{instance_id}: cache ordinal mismatch")
        if entry.get("text_sha256") != sha256_text(text):
            raise CacheIntegrityError(f"{instance_id}: cache text_sha256 mismatch (text changed)")
        for field in REQUIRED_PROVENANCE_FIELDS:
            if entry.get(field) in (None, ""):
                raise CacheIntegrityError(f"{instance_id}: cache entry missing provenance field {field!r}")
        start, end, form = entry.get("char_start"), entry.get("char_end"), entry.get("form")
        if not isinstance(start, int) or not isinstance(end, int) or not (0 <= start < end <= len(text)):
            raise CacheIntegrityError(f"{instance_id}: cache char_start/char_end invalid for current text")
        if form is None:
            raise CacheIntegrityError(f"{instance_id}: cache entry missing form")
        if text[start:end] != form:
            raise CacheIntegrityError(f"{instance_id}: cache span does not match current text")
        return {"form": form, "char_start": start, "char_end": end}

    # ---------------- B. AUTHORITY VERIFICATION (optional/strict) -------

    def verify_authority(self, corpus_dir=None):
        """OPTIONAL/STRICT re-verification against the actual DANTEStocks
        legacy corpus on disk. Never called by get_validated / the
        renderer / the audit script - this is for the resolver's own
        reproducibility check, or a human explicitly asking "does the
        committed cache still match the authority that produced it".

        Returns "MATCH" or "NOT_AVAILABLE". Raises CacheIntegrityError on
        an actual hash mismatch (the corpus IS available but disagrees with
        what's recorded - that is a hard failure, never silently ignored).
        "NOT_AVAILABLE" is not a failure: it just means this machine has no
        legacy checkout to re-verify against, which is expected for a
        normal clone and must never block rendering."""
        corpus_dir = corpus_dir or resolve_corpus_dir()
        try:
            current = compute_authority_hashes(corpus_dir)
        except FileNotFoundError:
            return "NOT_AVAILABLE"
        recorded = self.recorded_authority_hashes()
        mismatches = {
            k: (recorded.get(f"{k}_sha256"), v)
            for k, v in current.items()
            if recorded.get(f"{k}_sha256") != v
        }
        if mismatches:
            raise CacheIntegrityError(f"authority hash mismatch: {mismatches}")
        return "MATCH"


_SINGLETON = None


def load_cache(path=RESOLUTIONS_PATH):
    """Renderer/audit entry point. Performs (A) local validation only -
    never requires or touches the legacy corpus."""
    global _SINGLETON
    if _SINGLETON is None or Path(path) != _SINGLETON.path:
        _SINGLETON = PredicateAnchorCache(path)
    return _SINGLETON
