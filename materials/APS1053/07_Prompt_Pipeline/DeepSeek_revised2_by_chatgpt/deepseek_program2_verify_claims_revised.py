"""
Program 2: Verify Unverifiable Claims and Patch Compendium Flags Only
=====================================================================

Designed for the output format produced by
deepseek_speech_processing_program1_notree_revised2.py.

Objective
---------
1. Parse every record in output/unverifiable_claims.md.
2. Verify externally checkable claims with DeepSeek, using an optional Tavily
   web-search fallback when DeepSeek's memory-only pass is inconclusive.
3. Save resumable verification results.
4. Match verified claim records to the corresponding ``Unverifiable`` evidence
   entries in the ORIGINAL compendium.md.
5. Produce compendium_verified.md by replacing ONLY the leading verifiability
   token on matched evidence entries.

The compendium is never sent to an LLM and is never re-synthesised. The patcher
performs a strict preservation audit: after status tokens are normalised to a
placeholder, the original and updated compendia must be byte-for-byte identical.
If that invariant fails, no updated compendium is written.

Expected inputs (default locations under --output):
    unverifiable_claims.md
    compendium.md

Outputs:
    verification_results.jsonl       resumable checkpoint
    verification_results.md          readable result report
    unverifiable_claims_updated.md   claims grouped by final status
    compendium_verified.md           status-only patched compendium
    claim_match_report.md            matching diagnostics

Dependencies:
    pip install openai python-dotenv
Optional web fallback:
    pip install tavily-python
    and set TAVILY_API_KEY in .env

Python 3.9+; synchronous and Spyder-friendly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore

load_dotenv()


# =============================================================================
# Configuration
# =============================================================================

PROGRAM_VERSION = "2.0-current-format-status-only"
PROMPT_VERSION = "2.0"

DEEPSEEK_MODEL = "deepseek-v4-flash"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
LLM_TIMEOUT_SECONDS = 180.0
TEMPERATURE = 0.0
MAX_TOKENS = 8_000
MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 5
RATE_LIMIT_SECONDS = 1.0

# Memory-only claims are processed in batches to reduce API calls.
MEMORY_BATCH_SIZE = 8
# Search-result reviews are smaller because each record carries source snippets.
SEARCH_REVIEW_BATCH_SIZE = 4

# Cost-control estimates only; actual provider billing may differ.
ESTIMATED_MEMORY_COST_PER_CLAIM_USD = 0.01
ESTIMATED_SEARCH_COST_PER_CLAIM_USD = 0.01
ESTIMATED_SEARCH_REVIEW_COST_PER_CLAIM_USD = 0.01
MAX_SPEND_USD = 300.0
MAX_NEW_CLAIMS: Optional[int] = None

# ``auto`` uses Tavily only when TAVILY_API_KEY is present.
# CLI --web-search overrides this value.
WEB_SEARCH_MODE = "auto"  # auto | off | tavily
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_MAX_RESULTS = 5

# Matching is restricted by source filename before textual similarity is used.
MATCH_THRESHOLD = 0.56
AMBIGUITY_MARGIN = 0.025

# By default an incomplete checkpoint does not produce a partially updated
# compendium. Use --allow-partial-patch to override.
ALLOW_PARTIAL_PATCH = False

# Claims matching these descriptions are not objectively checkable from public
# sources. They are retained as Still Unverifiable without spending an API call.
INHERENTLY_UNVERIFIABLE_PATTERNS = (
    r"personal (?:account|anecdote|claim|experience)",
    r"without external verification",
    r"without verifiable documentation",
    r"speaker'?s? (?:own|personal)",
    r"private (?:return|loss|gain|transaction|experience)",
    r"inherently unverifiable",
    r"not empirically testable",
    r"no specific verifiable facts",
    r"purely hypothetical",
    r"subjective opinion",
)

VALID_STATUSES = (
    "Verified",
    "Disputed",
    "Partially Verified",
    "Still Unverifiable",
)

STATUS_TOKENS = {
    "Verified": "✅ **Verified**",
    "Disputed": "❌ **Disputed**",
    "Partially Verified": "⚠️ **Partially Verified**",
    "Still Unverifiable": "🔍 **Still Unverifiable**",
}


# =============================================================================
# Prompts
# =============================================================================

MEMORY_VERIFY_SYSTEM = """You are a rigorous fact-checker specialising in finance, economics, public policy, and investment history.

You receive a JSON array of claim records. This pass has NO live web access. Use only well-established information in your training knowledge. Be conservative. Do not infer that a claim is true merely because it sounds plausible. Treat relative wording such as "today" or "currently" as referring to the supplied speech_date.

Status definitions:
- Verified: the material factual content is confidently correct.
- Disputed: the material factual content is confidently false or materially misleading.
- Partially Verified: the claim combines supported and unsupported/incorrect material, or is directionally right but materially overstates precision.
- Still Unverifiable: available knowledge is insufficient, the claim is too vague, source-dependent, private, predictive, or requires live/historical data you cannot confidently reconstruct.

Return one JSON object only, with this exact top-level shape:
{"results": [{"claim_id": "...", "status": "Verified|Disputed|Partially Verified|Still Unverifiable", "finding": "concise explanation", "source": "named authoritative source if confidently known, otherwise DeepSeek training knowledge; no live source consulted"}]}

Return exactly one result for every supplied claim_id. Never rewrite claim_id."""

SEARCH_VERIFY_SYSTEM = """You are a rigorous fact-checker specialising in finance, economics, public policy, and investment history.

You receive claim records plus live web-search results gathered for each claim. Base the verdict on the supplied search material. Prefer primary and authoritative sources (government agencies, regulators, central banks, official company filings, original research, and established data providers). Do not treat a search-result snippet as conclusive when it does not directly support the claim.

Status definitions:
- Verified: the material factual content is supported by reliable sources.
- Disputed: reliable sources contradict the material factual content.
- Partially Verified: reliable sources support only part of the claim or show a material qualification.
- Still Unverifiable: the search material is inadequate, ambiguous, private, predictive, or not tied to a reliable source.

Return one JSON object only, with this exact top-level shape:
{"results": [{"claim_id": "...", "status": "Verified|Disputed|Partially Verified|Still Unverifiable", "finding": "concise source-grounded explanation", "source": "best source URL or full publication/source name"}]}

Return exactly one result for every supplied claim_id. Never rewrite claim_id."""


# =============================================================================
# Data structures
# =============================================================================

@dataclass(frozen=True)
class ClaimRecord:
    record_index: int
    record_type: str
    speech_ref: str
    claim: str
    reason: str
    memory_check: str
    memory_note: str
    source_excerpt: str
    source_match: bool
    source_location: Any

    @cached_property
    def claim_id(self) -> str:
        payload = "\x1f".join(
            (self.record_type, self.speech_ref, self.claim, self.source_excerpt)
        )
        return "CLM-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20].upper()

    @cached_property
    def speech_date(self) -> str:
        match = re.match(r"^(\d{4})(\d{2})(\d{2})", self.speech_ref)
        if not match:
            return "Unknown"
        return "{0}-{1}-{2}".format(*match.groups())

    def to_prompt_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "record_type": self.record_type,
            "speech_ref": self.speech_ref,
            "speech_date": self.speech_date,
            "claim": self.claim,
            "reason_originally_flagged": self.reason,
            "source_excerpt": self.source_excerpt,
        }


@dataclass
class EvidenceEntry:
    line_index: int
    status_span: Tuple[int, int]
    original_status: str
    item: str
    basis: str
    sources: List[str]
    excerpt: str
    raw_header: str


# =============================================================================
# General utilities
# =============================================================================

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalise_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalise_text(value: Any) -> str:
    text = _normalise_space(value).lower().replace("…", " ")
    text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    text = re.sub(r"[^a-z0-9%$]+", " ", text)
    return _normalise_space(text)


def _sequence_similarity(a: str, b: str) -> float:
    na, nb = _normalise_text(a), _normalise_text(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def _token_similarity(a: str, b: str) -> float:
    left, right = set(_normalise_text(a).split()), set(_normalise_text(b).split())
    if not left or not right:
        return 0.0
    intersection = len(left & right)
    # Sørensen-Dice rewards overlap without over-penalising paraphrase length.
    return (2.0 * intersection) / (len(left) + len(right))


def _text_similarity(a: str, b: str) -> float:
    return max(_sequence_similarity(a, b), _token_similarity(a, b))


def _strip_markdown_quotes(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        value = value[1:-1]
    if value.startswith("“") and value.endswith("”") and len(value) >= 2:
        value = value[1:-1]
    return value.strip()


def _chunks(items: Sequence[Any], size: int) -> Iterable[Sequence[Any]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _json_from_llm(text: str) -> Dict[str, Any]:
    cleaned = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    decoder = json.JSONDecoder()
    for index, char in enumerate(cleaned):
        if char != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    raise ValueError("LLM response did not contain a valid JSON object.")


def _normalise_verdict(value: Any) -> str:
    text = _normalise_space(value).lower().replace("️", "")
    if "partial" in text:
        return "Partially Verified"
    if "disput" in text or "false" == text or "contradict" in text:
        return "Disputed"
    if "still" in text or "unver" in text or "unknown" in text:
        return "Still Unverifiable"
    if "verif" in text or "true" == text or "support" == text:
        return "Verified"
    return "Still Unverifiable"


def _is_inherently_unverifiable(record: ClaimRecord) -> bool:
    haystack = "{0}\n{1}".format(record.claim, record.reason).lower()
    return any(re.search(pattern, haystack) for pattern in INHERENTLY_UNVERIFIABLE_PATTERNS)


# =============================================================================
# Current-format claims parser
# =============================================================================

FIELD_RE = re.compile(
    r"^- \*\*(TYPE|SPEECH_REF|CLAIM|REASON|MEMORY|MEMORY NOTE|SOURCE EXCERPT|SOURCE MATCH|SOURCE LOCATION):\*\*\s*(.*)$"
)
BLOCK_RE = re.compile(r"(?m)^##\s+(\d+)\.\s+(.+?)\s*$")


def parse_unverifiable_claims(path: Path) -> List[ClaimRecord]:
    """Parse the multi-line format emitted by _render_unverifiable_claims()."""
    text = path.read_text(encoding="utf-8")
    matches = list(BLOCK_RE.finditer(text))
    records: List[ClaimRecord] = []

    for position, match in enumerate(matches):
        block_start = match.end()
        block_end = matches[position + 1].start() if position + 1 < len(matches) else len(text)
        block = text[block_start:block_end]
        fields: Dict[str, str] = {}
        for line in block.splitlines():
            field_match = FIELD_RE.match(line)
            if not field_match:
                continue
            key = field_match.group(1).lower().replace(" ", "_")
            fields[key] = field_match.group(2).strip()

        if not fields.get("claim"):
            raise ValueError(
                "Claim record {0} has no CLAIM field in {1}.".format(
                    match.group(1), path
                )
            )

        source_location: Any = None
        raw_location = _strip_markdown_quotes(fields.get("source_location", ""))
        if raw_location:
            try:
                source_location = json.loads(raw_location)
            except json.JSONDecodeError:
                source_location = raw_location

        source_match = fields.get("source_match", "False").strip().lower() == "true"
        speech_ref = _strip_markdown_quotes(
            fields.get("speech_ref", match.group(2).strip())
        )
        records.append(
            ClaimRecord(
                record_index=int(match.group(1)),
                record_type=fields.get("type", ""),
                speech_ref=speech_ref,
                claim=_strip_markdown_quotes(fields.get("claim", "")),
                reason=_strip_markdown_quotes(fields.get("reason", "")),
                memory_check=_strip_markdown_quotes(fields.get("memory", "NoInternalBasis")),
                memory_note=_strip_markdown_quotes(fields.get("memory_note", "")),
                source_excerpt=_strip_markdown_quotes(fields.get("source_excerpt", "")),
                source_match=source_match,
                source_location=source_location,
            )
        )

    if not records:
        raise ValueError(
            "No claim records were parsed. This verifier expects the multi-line "
            "unverifiable_claims.md format produced by "
            "speech_processing_program_notree_revised2_new.py."
        )

    id_counts: Dict[str, int] = {}
    for record in records:
        id_counts[record.claim_id] = id_counts.get(record.claim_id, 0) + 1
    duplicate_ids = [claim_id for claim_id, count in id_counts.items() if count > 1]
    if duplicate_ids:
        raise ValueError("Duplicate claim identities found: {0}".format(duplicate_ids[:5]))
    return records


# =============================================================================
# Checkpoint handling
# =============================================================================

def load_checkpoint(path: Path) -> Dict[str, Dict[str, Any]]:
    completed: Dict[str, Dict[str, Any]] = {}
    if not path.exists():
        return completed
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            print("WARNING: ignoring malformed checkpoint line {0}.".format(line_number))
            continue
        if record.get("program_version") != PROGRAM_VERSION:
            continue
        claim_id = record.get("claim_id")
        if claim_id:
            completed[claim_id] = record
    return completed


def append_checkpoint(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


# =============================================================================
# DeepSeek and optional Tavily verification
# =============================================================================

def create_deepseek_client() -> OpenAI:
    if OpenAI is None:
        raise ImportError(
            "The openai package is required for verification. "
            "Run: pip install openai python-dotenv"
        )
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise EnvironmentError("DEEPSEEK_API_KEY not found in environment or .env file.")
    return OpenAI(
        api_key=api_key,
        base_url=DEEPSEEK_BASE_URL,
        timeout=LLM_TIMEOUT_SECONDS,
    )


def call_deepseek(client: OpenAI, system_prompt: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    last_error: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(payload, ensure_ascii=False, indent=2),
                    },
                ],
                extra_body={"thinking": {"type": "disabled"}},
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("DeepSeek returned an empty response.")
            return _json_from_llm(content)
        except Exception as exc:  # provider/network/format errors
            last_error = exc
            if attempt >= MAX_RETRIES:
                break
            wait = RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
            print(
                "  DeepSeek error on attempt {0}/{1}: {2}; retrying in {3}s".format(
                    attempt, MAX_RETRIES, exc, wait
                )
            )
            time.sleep(wait)
    raise RuntimeError("DeepSeek call failed: {0}".format(last_error))


def validate_batch_results(
    response: Dict[str, Any], expected_ids: Sequence[str]
) -> Dict[str, Dict[str, str]]:
    raw_results = response.get("results")
    if not isinstance(raw_results, list):
        raise ValueError("Verification response lacks a results array.")

    parsed: Dict[str, Dict[str, str]] = {}
    expected = set(expected_ids)
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        claim_id = str(item.get("claim_id", "")).strip()
        if claim_id not in expected or claim_id in parsed:
            continue
        parsed[claim_id] = {
            "status": _normalise_verdict(item.get("status")),
            "finding": _normalise_space(item.get("finding")),
            "source": _normalise_space(item.get("source")),
        }

    missing = [claim_id for claim_id in expected_ids if claim_id not in parsed]
    if missing:
        raise ValueError("Verification response omitted claim IDs: {0}".format(missing))
    return parsed


def resolve_web_search_mode(requested: str) -> str:
    mode = requested.lower()
    if mode not in ("auto", "off", "tavily"):
        raise ValueError("web search mode must be auto, off, or tavily")
    if mode == "auto":
        return "tavily" if TAVILY_API_KEY else "off"
    return mode


def tavily_search(record: ClaimRecord) -> List[Dict[str, str]]:
    if not TAVILY_API_KEY:
        return []
    try:
        from tavily import TavilyClient
    except ImportError as exc:
        raise RuntimeError(
            "Tavily fallback requested but tavily-python is not installed. "
            "Run: pip install tavily-python"
        ) from exc

    query = record.claim
    if record.speech_date != "Unknown":
        query += " as of " + record.speech_date
    client = TavilyClient(api_key=TAVILY_API_KEY)
    response = client.search(
        query=query[:500],
        search_depth="advanced",
        max_results=TAVILY_MAX_RESULTS,
        include_answer=False,
    )
    results: List[Dict[str, str]] = []
    for item in response.get("results", []):
        results.append(
            {
                "title": _normalise_space(item.get("title")),
                "url": _normalise_space(item.get("url")),
                "content": _normalise_space(item.get("content"))[:1200],
            }
        )
    return results


def make_checkpoint_record(
    claim: ClaimRecord,
    verification: Dict[str, str],
    mode: str,
) -> Dict[str, Any]:
    return {
        "program_version": PROGRAM_VERSION,
        "prompt_version": PROMPT_VERSION,
        "model": DEEPSEEK_MODEL,
        "claim_id": claim.claim_id,
        "record_index": claim.record_index,
        "record_type": claim.record_type,
        "speech_ref": claim.speech_ref,
        "claim": claim.claim,
        "reason": claim.reason,
        "source_excerpt": claim.source_excerpt,
        "verification": {
            "status": _normalise_verdict(verification.get("status")),
            "finding": _normalise_space(verification.get("finding")),
            "source": _normalise_space(verification.get("source")),
            "mode": mode,
        },
        "verified_at": _utc_now_iso(),
    }


def verify_claims(
    client: OpenAI,
    claims: Sequence[ClaimRecord],
    checkpoint_path: Path,
    web_search_mode: str,
    max_new_claims: Optional[int],
    max_spend_usd: float,
) -> Dict[str, Dict[str, Any]]:
    completed = load_checkpoint(checkpoint_path)
    by_id = {record.claim_id: record for record in claims}

    # Remove checkpoint records no longer present in the current input from the
    # in-memory count, while leaving the append-only file untouched.
    completed = {claim_id: value for claim_id, value in completed.items() if claim_id in by_id}
    pending = [record for record in claims if record.claim_id not in completed]

    print("\n=== VERIFY CLAIMS ===")
    print("  Current claim records: {0}".format(len(claims)))
    print("  Already checkpointed:  {0}".format(len(completed)))
    print("  Pending:               {0}".format(len(pending)))
    print("  Web fallback:          {0}".format(web_search_mode))

    new_count = 0
    estimated_spend = 0.0

    # Deterministically resolve private/inherently non-public claims first.
    for record in list(pending):
        if not _is_inherently_unverifiable(record):
            continue
        verification = {
            "status": "Still Unverifiable",
            "finding": "The claim concerns private, subjective, or inherently non-public information that cannot be established from reliable public sources.",
            "source": "No reliable public source applicable",
        }
        checkpoint_record = make_checkpoint_record(record, verification, "deterministic-skip")
        append_checkpoint(checkpoint_path, checkpoint_record)
        completed[record.claim_id] = checkpoint_record
        pending.remove(record)
        new_count += 1

    if max_new_claims is not None:
        remaining_capacity = max(0, max_new_claims - new_count)
        pending = pending[:remaining_capacity]

    memory_unresolved: List[ClaimRecord] = []
    for batch_number, batch in enumerate(_chunks(pending, MEMORY_BATCH_SIZE), 1):
        projected = estimated_spend + len(batch) * ESTIMATED_MEMORY_COST_PER_CLAIM_USD
        if projected > max_spend_usd:
            print("  Spend cap reached before memory batch {0}.".format(batch_number))
            break
        print(
            "  Memory batch {0}: {1} claim(s)".format(batch_number, len(batch))
        )
        payload = {"claims": [record.to_prompt_dict() for record in batch]}
        try:
            response = call_deepseek(client, MEMORY_VERIFY_SYSTEM, payload)
            parsed = validate_batch_results(
                response, [record.claim_id for record in batch]
            )
        except Exception as exc:
            # A malformed batch is retried one claim at a time so one bad item
            # does not invalidate the full checkpoint.
            print("  Batch validation failed ({0}); retrying individually.".format(exc))
            parsed = {}
            for record in batch:
                response = call_deepseek(
                    client,
                    MEMORY_VERIFY_SYSTEM,
                    {"claims": [record.to_prompt_dict()]},
                )
                parsed.update(validate_batch_results(response, [record.claim_id]))

        for record in batch:
            verdict = parsed[record.claim_id]
            checkpoint_record = make_checkpoint_record(record, verdict, "deepseek-memory")
            append_checkpoint(checkpoint_path, checkpoint_record)
            completed[record.claim_id] = checkpoint_record
            new_count += 1
            if verdict["status"] == "Still Unverifiable":
                memory_unresolved.append(record)
        estimated_spend = projected
        time.sleep(RATE_LIMIT_SECONDS)

    if web_search_mode == "tavily":
        # Also escalate memory-only Still Unverifiable records created by an
        # earlier run. This allows the user to add TAVILY_API_KEY later and
        # improve an existing checkpoint without resetting it.
        unresolved_by_id: Dict[str, ClaimRecord] = {
            record.claim_id: record for record in memory_unresolved
        }
        for claim_id, checkpoint_record in completed.items():
            verification = checkpoint_record.get("verification", {})
            if (
                _normalise_verdict(verification.get("status"))
                == "Still Unverifiable"
                and verification.get("mode") not in ("tavily+deepseek", "deterministic-skip")
                and claim_id in by_id
            ):
                unresolved_by_id[claim_id] = by_id[claim_id]
        web_candidates = list(unresolved_by_id.values())

    else:
        web_candidates = []

    if web_candidates:
        searchable_payloads: List[Tuple[ClaimRecord, List[Dict[str, str]]]] = []
        print("\n  Searching unresolved claims with Tavily...")
        for index, record in enumerate(web_candidates, 1):
            projected = estimated_spend + (
                ESTIMATED_SEARCH_COST_PER_CLAIM_USD
                + ESTIMATED_SEARCH_REVIEW_COST_PER_CLAIM_USD
            )
            if projected > max_spend_usd:
                print("  Spend cap reached during web search.")
                break
            try:
                results = tavily_search(record)
            except Exception as exc:
                print("  Search failed for {0}: {1}".format(record.claim_id, exc))
                results = []
            if results:
                searchable_payloads.append((record, results))
            estimated_spend = projected
            if index % 25 == 0:
                print("    searched {0}/{1}".format(index, len(web_candidates)))

        for batch_number, batch_pairs in enumerate(
            _chunks(searchable_payloads, SEARCH_REVIEW_BATCH_SIZE), 1
        ):
            print(
                "  Search-review batch {0}: {1} claim(s)".format(
                    batch_number, len(batch_pairs)
                )
            )
            payload = {
                "claims": [
                    {
                        **record.to_prompt_dict(),
                        "web_search_results": results,
                    }
                    for record, results in batch_pairs
                ]
            }
            response = call_deepseek(client, SEARCH_VERIFY_SYSTEM, payload)
            expected_ids = [record.claim_id for record, _ in batch_pairs]
            parsed = validate_batch_results(response, expected_ids)
            for record, _ in batch_pairs:
                checkpoint_record = make_checkpoint_record(
                    record, parsed[record.claim_id], "tavily+deepseek"
                )
                # Append a newer record with the same claim_id. load_checkpoint()
                # deliberately keeps the last occurrence.
                append_checkpoint(checkpoint_path, checkpoint_record)
                completed[record.claim_id] = checkpoint_record
            time.sleep(RATE_LIMIT_SECONDS)

    print("\n  Newly checkpointed this run: {0}".format(new_count))
    print("  Completed current claims:    {0}/{1}".format(len(completed), len(claims)))
    print("  Estimated run spend:         ${0:.2f}".format(estimated_spend))
    return completed


# =============================================================================
# Current-format compendium parser and status-only patcher
# =============================================================================

EVIDENCE_HEADER_RE = re.compile(
    r"^(?P<prefix>-\s*)"
    r"(?P<token>✅\s*\*\*Verified\*\*"
    r"|❌\s*\*\*Disputed\*\*"
    r"|⚠️?\s*\*\*Partially Verified\*\*"
    r"|⚠️?\s*\*\*Unverifiable\*\*"
    r"|🔍\s*\*\*Still Unverifiable\*\*)"
    r"(?P<separator>\s*—\s*)"
    r"(?P<item>.*?)(?P<trailing>\s*)$"
)


def _status_from_token(token: str) -> str:
    text = token.replace("️", "")
    if "Partially Verified" in text:
        return "Partially Verified"
    if "Still Unverifiable" in text:
        return "Still Unverifiable"
    if "Unverifiable" in text:
        return "Unverifiable"
    if "Disputed" in text:
        return "Disputed"
    return "Verified"


def parse_compendium_evidence(text: str) -> List[EvidenceEntry]:
    lines = text.splitlines(keepends=True)
    entries: List[EvidenceEntry] = []
    for line_index, line_with_end in enumerate(lines):
        line = line_with_end.rstrip("\r\n")
        match = EVIDENCE_HEADER_RE.match(line)
        if not match:
            continue

        basis = ""
        sources: List[str] = []
        excerpt = ""
        cursor = line_index + 1
        while cursor < len(lines):
            continuation = lines[cursor].rstrip("\r\n")
            stripped = continuation.strip()
            if not stripped:
                break
            if EVIDENCE_HEADER_RE.match(continuation) or continuation.startswith("#"):
                break
            if stripped.startswith("*Basis:*"):
                basis = stripped[len("*Basis:*") :].strip()
            elif stripped.startswith("*Sources:*"):
                sources = re.findall(r"`([^`]+)`", stripped)
            elif stripped.startswith("*Excerpt:*"):
                excerpt = _strip_markdown_quotes(
                    stripped[len("*Excerpt:*") :].strip()
                )
            cursor += 1

        entries.append(
            EvidenceEntry(
                line_index=line_index,
                status_span=match.span("token"),
                original_status=_status_from_token(match.group("token")),
                item=match.group("item").strip(),
                basis=basis,
                sources=sources,
                excerpt=excerpt,
                raw_header=line,
            )
        )
    return entries


def _claim_match_score(entry: EvidenceEntry, claim: ClaimRecord) -> float:
    item_score = _text_similarity(entry.item, claim.claim)
    if entry.excerpt and claim.source_excerpt:
        excerpt_score = _text_similarity(entry.excerpt, claim.source_excerpt)
        score = 0.72 * item_score + 0.28 * excerpt_score
    else:
        score = item_score

    # Exact/near-exact excerpts are a particularly strong provenance signal.
    if entry.excerpt and claim.source_excerpt:
        ne, nc = _normalise_text(entry.excerpt), _normalise_text(claim.source_excerpt)
        if ne and nc and (ne in nc or nc in ne):
            score = max(score, 0.92)
    return min(1.0, score)


def match_evidence_entries(
    entries: Sequence[EvidenceEntry],
    claims: Sequence[ClaimRecord],
    results: Dict[str, Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Match each currently Unverifiable compendium entry independently.

    A claim may legitimately appear more than once in the compendium under
    different canonical arguments, so claim records are not consumed globally.
    """
    by_source: Dict[str, List[ClaimRecord]] = {}
    for claim in claims:
        by_source.setdefault(claim.speech_ref, []).append(claim)

    matches: List[Dict[str, Any]] = []
    diagnostics: List[Dict[str, Any]] = []

    for entry in entries:
        if entry.original_status != "Unverifiable":
            continue

        candidates: Dict[str, ClaimRecord] = {}
        for source in entry.sources:
            for claim in by_source.get(source, []):
                if claim.claim_id in results:
                    candidates[claim.claim_id] = claim

        ranked: List[Tuple[float, int, ClaimRecord]] = []
        for claim in candidates.values():
            score = _claim_match_score(entry, claim)
            # Current pipeline explicitly emits evidence-item records. Prefer
            # those over parallel explicit-claim records only as a tie-breaker.
            type_priority = 1 if claim.record_type == "unverifiable_evidence_item" else 0
            ranked.append((score, type_priority, claim))
        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)

        if not ranked:
            diagnostics.append(
                {
                    "line": entry.line_index + 1,
                    "item": entry.item,
                    "sources": entry.sources,
                    "outcome": "unmatched",
                    "reason": "No completed claim record shared a source filename.",
                }
            )
            continue

        best_score, _, best_claim = ranked[0]
        second_score = ranked[1][0] if len(ranked) > 1 else 0.0
        margin = best_score - second_score

        if best_score < MATCH_THRESHOLD:
            diagnostics.append(
                {
                    "line": entry.line_index + 1,
                    "item": entry.item,
                    "sources": entry.sources,
                    "outcome": "unmatched",
                    "reason": "Best textual score {0:.3f} was below threshold {1:.3f}.".format(
                        best_score, MATCH_THRESHOLD
                    ),
                    "best_claim": best_claim.claim,
                }
            )
            continue

        # Do not block an exact evidence-item match merely because a parallel
        # explicit claim has nearly the same wording.
        parallel_duplicate = (
            len(ranked) > 1
            and ranked[0][1] > ranked[1][1]
            and _text_similarity(best_claim.claim, ranked[1][2].claim) >= 0.92
        )
        if margin < AMBIGUITY_MARGIN and not parallel_duplicate and best_score < 0.90:
            diagnostics.append(
                {
                    "line": entry.line_index + 1,
                    "item": entry.item,
                    "sources": entry.sources,
                    "outcome": "ambiguous",
                    "reason": "Best match margin {0:.3f} was below {1:.3f}.".format(
                        margin, AMBIGUITY_MARGIN
                    ),
                    "best_claim": best_claim.claim,
                    "second_claim": ranked[1][2].claim if len(ranked) > 1 else "",
                }
            )
            continue

        verification = results[best_claim.claim_id]["verification"]
        status = _normalise_verdict(verification.get("status"))
        matches.append(
            {
                "line_index": entry.line_index,
                "status_span": entry.status_span,
                "new_status": status,
                "claim_id": best_claim.claim_id,
                "claim": best_claim.claim,
                "score": best_score,
                "source": verification.get("source", ""),
                "finding": verification.get("finding", ""),
            }
        )
        diagnostics.append(
            {
                "line": entry.line_index + 1,
                "item": entry.item,
                "sources": entry.sources,
                "outcome": "matched",
                "claim_id": best_claim.claim_id,
                "claim": best_claim.claim,
                "score": round(best_score, 4),
                "status": status,
            }
        )

    return matches, diagnostics


def patch_compendium_statuses(text: str, matches: Sequence[Dict[str, Any]]) -> str:
    """Replace only the status token of each matched evidence header line."""
    lines = text.splitlines(keepends=True)
    by_line = {int(match["line_index"]): match for match in matches}
    for line_index, patch in by_line.items():
        line_with_end = lines[line_index]
        line = line_with_end.rstrip("\r\n")
        ending = line_with_end[len(line) :]
        match = EVIDENCE_HEADER_RE.match(line)
        if not match:
            raise RuntimeError(
                "Evidence header disappeared before patching line {0}.".format(
                    line_index + 1
                )
            )
        start, end = match.span("token")
        token = STATUS_TOKENS[_normalise_verdict(patch["new_status"])]
        lines[line_index] = line[:start] + token + line[end:] + ending
    return "".join(lines)


def _canonicalise_status_tokens(text: str) -> str:
    lines = text.splitlines(keepends=True)
    output: List[str] = []
    for line_with_end in lines:
        line = line_with_end.rstrip("\r\n")
        ending = line_with_end[len(line) :]
        match = EVIDENCE_HEADER_RE.match(line)
        if not match:
            output.append(line_with_end)
            continue
        start, end = match.span("token")
        output.append(line[:start] + "<EVIDENCE_STATUS>" + line[end:] + ending)
    return "".join(output)


def assert_status_only_change(
    original: str, patched: str, expected_line_indices: Sequence[int]
) -> None:
    """Reject output if anything except expected evidence status tokens changed."""
    original_lines = original.splitlines(keepends=True)
    patched_lines = patched.splitlines(keepends=True)
    if len(original_lines) != len(patched_lines):
        raise RuntimeError("Preservation audit failed: line count changed.")

    expected = set(expected_line_indices)
    for line_index, (before, after) in enumerate(zip(original_lines, patched_lines)):
        if before == after:
            continue
        if line_index not in expected:
            raise RuntimeError(
                "Preservation audit failed: unexpected change on line {0}.".format(
                    line_index + 1
                )
            )
        if _canonicalise_status_tokens(before) != _canonicalise_status_tokens(after):
            raise RuntimeError(
                "Preservation audit failed: non-status text changed on line {0}.".format(
                    line_index + 1
                )
            )

    if _canonicalise_status_tokens(original) != _canonicalise_status_tokens(patched):
        raise RuntimeError(
            "Preservation audit failed: content other than evidence status tokens changed. "
            "The updated compendium was not written."
        )


def write_verified_compendium(
    original_path: Path,
    output_path: Path,
    claims: Sequence[ClaimRecord],
    results: Dict[str, Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    original = original_path.read_text(encoding="utf-8")
    entries = parse_compendium_evidence(original)
    matches, diagnostics = match_evidence_entries(entries, claims, results)
    patched = patch_compendium_statuses(original, matches)
    assert_status_only_change(
        original, patched, [int(match["line_index"]) for match in matches]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(patched)
    print(
        "  Wrote {0}: {1} status token(s) patched; all other text preserved.".format(
            output_path, len(matches)
        )
    )
    return matches, diagnostics


# =============================================================================
# Reports
# =============================================================================

def _result_for_claim(
    claim: ClaimRecord, results: Dict[str, Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    return results.get(claim.claim_id)


def write_verification_report(
    path: Path,
    claims: Sequence[ClaimRecord],
    results: Dict[str, Dict[str, Any]],
) -> None:
    counts = {status: 0 for status in VALID_STATUSES}
    incomplete = 0
    for claim in claims:
        result = _result_for_claim(claim, results)
        if result is None:
            incomplete += 1
            continue
        counts[_normalise_verdict(result["verification"].get("status"))] += 1

    lines = [
        "# Claim Verification Results",
        "",
        "- **Program version:** `{0}`".format(PROGRAM_VERSION),
        "- **Model:** `{0}`".format(DEEPSEEK_MODEL),
        "- **Input records:** {0}".format(len(claims)),
        "- **Completed:** {0}".format(len(claims) - incomplete),
        "- **Incomplete:** {0}".format(incomplete),
    ]
    for status in VALID_STATUSES:
        lines.append("- **{0}:** {1}".format(status, counts[status]))
    lines.append("")

    for claim in claims:
        result = _result_for_claim(claim, results)
        lines.extend(
            [
                "## {0}. {1}".format(claim.record_index, claim.speech_ref),
                "",
                "- **CLAIM ID:** `{0}`".format(claim.claim_id),
                "- **TYPE:** {0}".format(claim.record_type),
                "- **CLAIM:** {0}".format(claim.claim),
                "- **ORIGINAL REASON:** {0}".format(claim.reason),
            ]
        )
        if result is None:
            lines.append("- **VERIFICATION STATUS:** Not yet processed")
        else:
            verification = result["verification"]
            lines.extend(
                [
                    "- **VERIFICATION STATUS:** {0}".format(
                        _normalise_verdict(verification.get("status"))
                    ),
                    "- **FINDING:** {0}".format(verification.get("finding", "")),
                    "- **SOURCE:** {0}".format(verification.get("source", "")),
                    "- **MODE:** {0}".format(verification.get("mode", "")),
                ]
            )
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_updated_claims_report(
    path: Path,
    claims: Sequence[ClaimRecord],
    results: Dict[str, Dict[str, Any]],
) -> None:
    grouped: Dict[str, List[Tuple[ClaimRecord, Optional[Dict[str, Any]]]]] = {
        status: [] for status in VALID_STATUSES
    }
    incomplete: List[Tuple[ClaimRecord, Optional[Dict[str, Any]]]] = []
    for claim in claims:
        result = _result_for_claim(claim, results)
        if result is None:
            incomplete.append((claim, None))
        else:
            status = _normalise_verdict(result["verification"].get("status"))
            grouped[status].append((claim, result))

    lines = [
        "# Unverifiable Claims — Updated After Verification",
        "",
        "The original claim wording is retained below. Verification findings are separate metadata.",
        "",
    ]
    for status in VALID_STATUSES:
        lines.append("## {0} ({1})".format(status, len(grouped[status])))
        lines.append("")
        if not grouped[status]:
            lines.append("_None._")
            lines.append("")
            continue
        for claim, result in grouped[status]:
            verification = result["verification"] if result else {}
            lines.extend(
                [
                    "- **{0}** — `{1}`".format(claim.claim, claim.speech_ref),
                    "  - Claim ID: `{0}`".format(claim.claim_id),
                    "  - Finding: {0}".format(verification.get("finding", "")),
                    "  - Source: {0}".format(verification.get("source", "")),
                    "  - Original reason: {0}".format(claim.reason),
                ]
            )
        lines.append("")

    if incomplete:
        lines.append("## Not Yet Processed ({0})".format(len(incomplete)))
        lines.append("")
        for claim, _ in incomplete:
            lines.append("- **{0}** — `{1}`".format(claim.claim, claim.speech_ref))
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_match_report(
    path: Path,
    diagnostics: Sequence[Dict[str, Any]],
    total_unverifiable_entries: int,
) -> None:
    matched = [item for item in diagnostics if item.get("outcome") == "matched"]
    unmatched = [item for item in diagnostics if item.get("outcome") != "matched"]
    lines = [
        "# Compendium Claim Match Report",
        "",
        "- **Original Unverifiable evidence entries:** {0}".format(
            total_unverifiable_entries
        ),
        "- **Matched:** {0}".format(len(matched)),
        "- **Unmatched or ambiguous:** {0}".format(len(unmatched)),
        "- **Match threshold:** {0:.3f}".format(MATCH_THRESHOLD),
        "- **Ambiguity margin:** {0:.3f}".format(AMBIGUITY_MARGIN),
        "",
        "Only matched entries were eligible for a status-token replacement. Unmatched entries remain exactly as in the original compendium.",
        "",
    ]

    if unmatched:
        lines.append("## Manual Review Required")
        lines.append("")
        for item in unmatched:
            lines.extend(
                [
                    "### Line {0}: {1}".format(item.get("line"), item.get("item")),
                    "- Outcome: {0}".format(item.get("outcome")),
                    "- Sources: {0}".format(
                        ", ".join(item.get("sources", [])) or "None"
                    ),
                    "- Reason: {0}".format(item.get("reason", "")),
                ]
            )
            if item.get("best_claim"):
                lines.append("- Best claim: {0}".format(item["best_claim"]))
            if item.get("second_claim"):
                lines.append("- Second claim: {0}".format(item["second_claim"]))
            lines.append("")
    else:
        lines.append("_All originally Unverifiable evidence entries matched._")
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


# =============================================================================
# Main
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify claims from the current multi-line unverifiable_claims.md "
            "format and patch only verifiability status tokens in compendium.md."
        )
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Pipeline output directory (default: output).",
    )
    parser.add_argument(
        "--claims",
        default=None,
        help="Explicit unverifiable_claims.md path; defaults to OUTPUT/unverifiable_claims.md.",
    )
    parser.add_argument(
        "--compendium",
        default=None,
        help="Explicit compendium path; defaults to OUTPUT/compendium.md.",
    )
    parser.add_argument(
        "--web-search",
        choices=("auto", "off", "tavily"),
        default=WEB_SEARCH_MODE,
        help="Optional live-search fallback mode (default: auto).",
    )
    parser.add_argument(
        "--max-new-claims",
        type=int,
        default=MAX_NEW_CLAIMS,
        help="Limit newly processed claims during this run; rerun to continue.",
    )
    parser.add_argument(
        "--max-spend-usd",
        type=float,
        default=MAX_SPEND_USD,
        help="Estimated run-level spend cap (default: 300).",
    )
    parser.add_argument(
        "--allow-partial-patch",
        action="store_true",
        default=ALLOW_PARTIAL_PATCH,
        help="Write a partially updated compendium before all claims are checkpointed.",
    )
    parser.add_argument(
        "--reset-checkpoint",
        action="store_true",
        help="Delete the current verification_results.jsonl before processing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse inputs and report counts without API calls or output changes.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    claims_path = Path(args.claims) if args.claims else output_dir / "unverifiable_claims.md"
    compendium_path = (
        Path(args.compendium) if args.compendium else output_dir / "compendium.md"
    )
    checkpoint_path = output_dir / "verification_results.jsonl"

    for required in (claims_path, compendium_path):
        if not required.exists():
            raise FileNotFoundError("Required input not found: {0}".format(required))

    claims = parse_unverifiable_claims(claims_path)
    compendium_text = compendium_path.read_text(encoding="utf-8")
    evidence_entries = parse_compendium_evidence(compendium_text)
    original_unverifiable = [
        entry for entry in evidence_entries if entry.original_status == "Unverifiable"
    ]

    print("Parsed {0} claim records.".format(len(claims)))
    print(
        "Parsed {0} compendium evidence entries, including {1} currently Unverifiable.".format(
            len(evidence_entries), len(original_unverifiable)
        )
    )

    if args.dry_run:
        print("DRY RUN complete; no API calls and no files written.")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    if args.reset_checkpoint and checkpoint_path.exists():
        checkpoint_path.unlink()
        print("Deleted checkpoint: {0}".format(checkpoint_path))

    web_search_mode = resolve_web_search_mode(args.web_search)
    if args.web_search == "auto" and web_search_mode == "off":
        print(
            "WARNING: TAVILY_API_KEY is not set. Verification will use DeepSeek "
            "memory only; inconclusive claims remain Still Unverifiable."
        )
    if web_search_mode == "tavily" and not TAVILY_API_KEY:
        raise EnvironmentError(
            "--web-search tavily requires TAVILY_API_KEY in environment or .env."
        )

    client = create_deepseek_client()
    results = verify_claims(
        client=client,
        claims=claims,
        checkpoint_path=checkpoint_path,
        web_search_mode=web_search_mode,
        max_new_claims=args.max_new_claims,
        max_spend_usd=args.max_spend_usd,
    )

    write_verification_report(
        output_dir / "verification_results.md", claims, results
    )
    write_updated_claims_report(
        output_dir / "unverifiable_claims_updated.md", claims, results
    )

    complete_count = sum(claim.claim_id in results for claim in claims)
    if complete_count < len(claims) and not args.allow_partial_patch:
        print(
            "\nCheckpoint is incomplete ({0}/{1}). Reports were written, but the "
            "compendium was not patched. Rerun to continue, or use "
            "--allow-partial-patch.".format(complete_count, len(claims))
        )
        return 0

    matches, diagnostics = write_verified_compendium(
        original_path=compendium_path,
        output_path=output_dir / "compendium_verified.md",
        claims=claims,
        results=results,
    )
    write_match_report(
        output_dir / "claim_match_report.md",
        diagnostics,
        total_unverifiable_entries=len(original_unverifiable),
    )

    changed = sum(
        1
        for match in matches
        if match["new_status"] != "Still Unverifiable"
    )
    print("\nVerification pipeline complete.")
    print("  Matched compendium entries: {0}".format(len(matches)))
    print("  Entries resolved/disputed/partial: {0}".format(changed))
    print("  Updated compendium: {0}".format(output_dir / "compendium_verified.md"))
    print("  Match report:       {0}".format(output_dir / "claim_match_report.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
