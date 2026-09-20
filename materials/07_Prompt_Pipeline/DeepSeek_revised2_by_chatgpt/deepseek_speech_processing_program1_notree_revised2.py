"""
speech_processing_program_notree_REVISED.py
============================================

Five-phase, provenance-preserving map/reduce pipeline for converting a folder
of single-speaker finance, economics, and investment transcripts into:

    output/compendium.md
    output/theme_index.md
    output/unverifiable_claims.md

The authoritative publication hierarchy is:

    Canonical Central Claim chapter
        -> Canonical Theme section (one persistent CC x T pair)
            -> Canonical argument conclusions
                -> premise synthesis, evidence, rhetoric, evolution, provenance

Important modelling distinctions
--------------------------------
* A speech has one local central claim and many local themes/arguments.
* A confidently classified speech has exactly one PRIMARY canonical CC and
  one to three canonical Themes. The selected CC is the speech's best
  argumentative home; exact paraphrase or semantic equivalence is not required.
* Every categorised speech stores one controlled speech-to-CC relationship type
  (support, instance, mechanism, consequence, qualification, opposition,
  historical example, application, or evidence).
* A persistent CC x T pair is the many-to-many junction entity stored in
  cc_theme_pairs.json.
* A runtime bucket is a temporary Phase-5 aggregation container created from
  one persistent pair. A bucket is not text and is not contained in a speech.
* Phase 4 is lossless augmentation. It does not ask an LLM to rewrite or
  paraphrase the source-level intellectual record.
* Canonical CC chapters are authoritative. Theme indexes link to those
  chapters and do not duplicate the full synthesis.
* Verified / Unverifiable / Disputed are transcript-analysis workflow labels,
  not external fact-checking verdicts. This program performs no web search.

Phases
------
1  SUMMARISE   One LLM call per transcript; preserve local wording, source
               excerpts, IDs, date, source hash, and unverifiable claims.
2  INVENTORY   Aggregate complete Phase-1 records; compute semantic duplicate
               diagnostics without merging source entities.
3  CONSOLIDATE Discover canonical CCs and Themes separately; classify each
               speech into its best argumentative-home CC with an explicit
               relationship type; save mappings and the CC x T junction table.
4  REMAP       Deterministically augment each Phase-1 JSON record with canonical
               mappings, pair memberships, and source-contribution records.
5  ASSEMBLE    Build and role-group buckets in Python, synthesize within one
               pair at a time without converting qualifications or opposition
               into support, render deterministic outputs, and run integrity
               checks.

Compatibility
-------------
* Python 3.9+ and Spyder friendly: synchronous calls, no multiprocessing.
* DeepSeek V4 Flash via the OpenAI-compatible endpoint.
* Required third-party packages:
      openai, python-dotenv, sentence-transformers, numpy

The program intentionally centralizes all tunable values in the configuration
block below. Checkpoint reuse is based on dependency hashes, not file existence
alone.
"""

# ── Standard library ──────────────────────────────────────────────────────────
import argparse
import copy
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import time
import traceback
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

# ── Third-party ───────────────────────────────────────────────────────────────
try:
    import numpy as np
    from dotenv import load_dotenv
    from openai import OpenAI
    from sentence_transformers import SentenceTransformer
except ImportError as exc:
    sys.exit(
        "Missing dependency: {0}\n"
        "Run: pip install openai python-dotenv sentence-transformers numpy".format(exc)
    )


# ═════════════════════════════════════════════════════════════════════════════
# Configuration — all tunable parameters live here
# ═════════════════════════════════════════════════════════════════════════════

MODEL = "deepseek-v4-flash"
BASE_URL = "https://api.deepseek.com/v1"
TEMPERATURE = 0
MIN_MAX_TOKENS = 8_000
LLM_TIMEOUT_SECONDS = 180.0
MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 10
BUCKET_VALIDATION_MAX_ATTEMPTS = 3

TRANSCRIPTS_DIR = Path(__file__).resolve().parents[3] / "assignments/generative-ai/notes/Transcripts"
OUTPUT_DIR = Path("output")
CHECKPOINTS_DIR = OUTPUT_DIR / "checkpoints"
LOGS_DIR = OUTPUT_DIR / "logs"

PHASE1_DIR = CHECKPOINTS_DIR / "phase1"
PHASE2_DIR = CHECKPOINTS_DIR / "phase2"
PHASE3_DIR = CHECKPOINTS_DIR / "phase3"
PHASE4_DIR = CHECKPOINTS_DIR / "phase4"
PHASE5_DIR = CHECKPOINTS_DIR / "phase5"
PHASE5_BUCKETS_DIR = PHASE5_DIR / "buckets"
PHASE5_SUBGROUPS_DIR = PHASE5_DIR / "subgroups"

MASTER_INVENTORY = PHASE2_DIR / "master_inventory.json"
INVENTORY_MANIFEST = PHASE2_DIR / "inventory_manifest.json"
DUPLICATE_DIAGNOSTICS = PHASE2_DIR / "near_duplicate_diagnostics.json"

CANONICAL_CCS_FILE = PHASE3_DIR / "canonical_ccs.json"
CANONICAL_THEMES_FILE = PHASE3_DIR / "canonical_themes.json"
LOCAL_MAPPINGS_FILE = PHASE3_DIR / "local_to_canonical_mappings.json"
CLASSIFICATIONS_FILE = PHASE3_DIR / "speech_classifications.json"
CC_THEME_PAIRS_FILE = PHASE3_DIR / "cc_theme_pairs.json"
SECONDARY_CONTRIBUTIONS_FILE = PHASE3_DIR / "secondary_cc_contributions.json"
CANONICAL_HISTORY_FILE = PHASE3_DIR / "canonical_history.json"
CANONICAL_MANIFEST = PHASE3_DIR / "manifest.json"

UNCATEGORISED_FILE = PHASE4_DIR / "uncategorised.jsonl"
PHASE4_MANIFEST = PHASE4_DIR / "manifest.json"

COMPENDIUM_FILE = OUTPUT_DIR / "compendium.md"
THEME_INDEX_FILE = OUTPUT_DIR / "theme_index.md"
UNVERIFIABLE_FILE = OUTPUT_DIR / "unverifiable_claims.md"
INTEGRITY_REPORT_FILE = OUTPUT_DIR / "integrity_report.json"
PHASE5_MANIFEST = PHASE5_DIR / "manifest.json"

PROMPT_VERSION = "2.0"
SCHEMA_VERSION = "2.0"

# Phase-specific versions let a classification/synthesis prompt change
# invalidate only the dependent phases. Phase 1 and canonical discovery can be
# reused when their own prompts and source dependencies are unchanged.
CLASSIFICATION_PROMPT_VERSION = "2.1"
CLASSIFICATION_SCHEMA_VERSION = "2.1"
BUCKET_PROMPT_VERSION = "2.1"
BUCKET_SCHEMA_VERSION = "2.2"

# Discovery and semantic representation
DISCOVERY_BATCH_SIZE = 50
CC_PER_BATCH_MIN = 3
CC_PER_BATCH_MAX = 6
T_PER_BATCH_MIN = 8
T_PER_BATCH_MAX = 11
EMBEDDING_MODEL_NAME = "mukaj/fin-mpnet-base"
CC_DEDUP_THRESHOLD = 0.85
THEME_DEDUP_THRESHOLD = 0.85
CANONICAL_STABILITY_THRESHOLD = 0.90
DUPLICATE_DIAGNOSTIC_MAX_PAIRS = 5_000

# Corpus-size-relative counts are diagnostics, not hard quotas.
CC_RATIO_MIN = 0.06
CC_RATIO_MAX = 0.08
THEME_RATIO_MIN = 0.12
THEME_RATIO_MAX = 0.16
TARGET_COUNTS_ARE_HARD = False

# Classification and mapping
# Intentionally unchanged at 0.70 so this revision tests the broader
# argumentative-home definition without simultaneously relaxing acceptance.
CLASSIFICATION_CONFIDENCE_MIN = 0.70
THEME_MAPPING_CONFIDENCE_MIN = 0.55
MAX_THEMES_PER_SPEECH = 3
CLASSIFICATION_CC_CANDIDATES = 12
CLASSIFICATION_THEME_CANDIDATES_PER_LOCAL_THEME = 6
ALLOW_SECONDARY_CC_CONTRIBUTIONS = False

# Controlled vocabulary describing how a speech participates in its primary
# Canonical Central Claim chapter. Topical overlap alone is never a valid type.
PRIMARY_CC_RELATIONSHIP_TYPES = (
    "supports",
    "specific_instance",
    "mechanism",
    "consequence",
    "qualification",
    "opposition",
    "historical_example",
    "application",
    "evidence",
)
AFFIRMATIVE_RELATIONSHIP_TYPES = {
    "supports",
    "specific_instance",
    "mechanism",
    "consequence",
    "application",
    "evidence",
}
NON_AFFIRMATIVE_RELATIONSHIP_TYPES = {
    "qualification",
    "opposition",
}

# Assembly
ASSEMBLY_BUCKET_LIMIT = 20
BUCKET_SUBGROUP_SIZE = 10
WRITE_THEME_INDEX = True
WRITE_REMAPPED_MARKDOWN = True
MAX_TRANSCRIPT_CHARS = 120_000
MAX_SOURCE_EXCERPT_CHARS = 700
MAX_RENDERED_EXCERPT_CHARS = 350

# Checkpoint and run policy
RECONSOLIDATE = False
CLEAN_PHASE5_STALE_BUCKETS = True

# Deterministic schema identifiers
PHASE1_RECORD_KIND = "speech_analysis"
PHASE4_RECORD_KIND = "remapped_speech_analysis"
PAIR_RECORD_KIND = "canonical_cc_theme_pair"
BUCKET_RECORD_KIND = "canonical_pair_synthesis"


# ═════════════════════════════════════════════════════════════════════════════
# Global runtime state
# ═════════════════════════════════════════════════════════════════════════════

log = logging.getLogger("speech_compendium")
_LLM_CALL_COUNT = 0
_EMBEDDING_MODEL = None  # type: Optional[SentenceTransformer]


# ═════════════════════════════════════════════════════════════════════════════
# Directory, logging, hashing, JSON, and text utilities
# ═════════════════════════════════════════════════════════════════════════════

def _setup_dirs() -> None:
    """Create every output/checkpoint directory before logging or file I/O."""
    for directory in (
        OUTPUT_DIR,
        CHECKPOINTS_DIR,
        LOGS_DIR,
        PHASE1_DIR,
        PHASE2_DIR,
        PHASE3_DIR,
        PHASE4_DIR,
        PHASE5_DIR,
        PHASE5_BUCKETS_DIR,
        PHASE5_SUBGROUPS_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def _configure_logging(debug: bool = False) -> None:
    """Configure stdout and file logging after directories exist."""
    level = logging.DEBUG if debug else logging.INFO
    formatter = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s")

    log.setLevel(level)
    log.handlers.clear()
    log.propagate = False

    stream = logging.StreamHandler(sys.stdout)
    stream.setLevel(level)
    stream.setFormatter(formatter)
    log.addHandler(stream)

    file_handler = logging.FileHandler(
        LOGS_DIR / "pipeline.log", mode="a", encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalise_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _normalise_key(text: str) -> str:
    value = _normalise_whitespace(text).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return _normalise_whitespace(value)


def _safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return value.strip("._") or "record"


def _slug(value: str) -> str:
    value = _normalise_key(value).replace(" ", "-")
    return value[:80].strip("-") or "item"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _canonical_json_text(data: Any) -> str:
    return json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _hash_json(data: Any) -> str:
    return _sha256_text(_canonical_json_text(data))


def _hash_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def _write_json(path: Path, data: Any) -> None:
    _atomic_write_text(
        path,
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False),
    )


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_if_exists(path: Path) -> Optional[Any]:
    try:
        return _read_json(path) if path.exists() else None
    except Exception as exc:
        log.warning("Cannot read JSON checkpoint %s: %s", path, exc)
        return None


def _load_transcript(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            text = path.read_text(encoding=encoding).lstrip("\ufeff")
            if text.startswith("---\n"):
                text = text.split("\n---\n", 1)[1]
                text = re.sub(r"^\s*# [^\n]+\n+", "", text, count=1)
                text = re.sub(r"(?m) \^[a-zA-Z0-9-]+$", "", text)
            text = re.sub(r'(?<!!)\[\[([^\]\n]+)\]\]', lambda m: m[1].split('|', 1)[1] if '|' in m[1] else m[1].split('#', 1)[0], text)
            text = text.replace('\\$', '$')
            return text
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, "Cannot decode {0}".format(path))


def _parse_date_from_filename(filename: str) -> str:
    prefix = filename[:8]
    if len(prefix) == 8 and prefix.isdigit():
        try:
            parsed = datetime.strptime(prefix, "%Y%m%d")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return "Unknown"


def _stable_speech_id(filename: str) -> str:
    return "SP-" + _sha256_text(filename.lower())[:12].upper()


def _stable_local_id(prefix: str, speech_id: str, position: str, text: str) -> str:
    payload = "|".join((speech_id, position, _normalise_key(text)))
    return "{0}-{1}".format(prefix, _sha256_text(payload)[:12].upper())


def _numeric_id_sort_key(identifier: str) -> Tuple[str, int, str]:
    match = re.match(r"([A-Za-z_-]+)(\d+)$", identifier or "")
    if match:
        return (match.group(1), int(match.group(2)), identifier)
    return (identifier or "", 0, identifier or "")


def _pair_id(cc_id: str, theme_id: str) -> str:
    return "PAIR-{0}-{1}".format(cc_id, theme_id)


def _pair_anchor(cc_id: str, theme_id: str) -> str:
    return "cc-{0}-theme-{1}".format(cc_id.lower(), theme_id.lower())


def _chapter_anchor(cc_id: str) -> str:
    return "cc-{0}".format(cc_id.lower())


def _record_dependency_matches(record: Dict[str, Any], expected: Dict[str, Any]) -> bool:
    return record.get("dependencies") == expected


def _phase_configuration() -> Dict[str, Any]:
    """Configuration subset recorded in manifests for reproducibility."""
    return {
        "model": MODEL,
        "base_url": BASE_URL,
        "temperature": TEMPERATURE,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "classification_prompt_version": CLASSIFICATION_PROMPT_VERSION,
        "classification_schema_version": CLASSIFICATION_SCHEMA_VERSION,
        "bucket_prompt_version": BUCKET_PROMPT_VERSION,
        "bucket_schema_version": BUCKET_SCHEMA_VERSION,
        "primary_cc_relationship_types": list(PRIMARY_CC_RELATIONSHIP_TYPES),
        "embedding_model": EMBEDDING_MODEL_NAME,
        "cc_dedup_threshold": CC_DEDUP_THRESHOLD,
        "theme_dedup_threshold": THEME_DEDUP_THRESHOLD,
        "canonical_stability_threshold": CANONICAL_STABILITY_THRESHOLD,
        "classification_confidence_min": CLASSIFICATION_CONFIDENCE_MIN,
        "theme_mapping_confidence_min": THEME_MAPPING_CONFIDENCE_MIN,
        "max_themes_per_speech": MAX_THEMES_PER_SPEECH,
        "allow_secondary_cc_contributions": ALLOW_SECONDARY_CC_CONTRIBUTIONS,
        "assembly_bucket_limit": ASSEMBLY_BUCKET_LIMIT,
        "bucket_subgroup_size": BUCKET_SUBGROUP_SIZE,
        "cc_ratio_min": CC_RATIO_MIN,
        "cc_ratio_max": CC_RATIO_MAX,
        "theme_ratio_min": THEME_RATIO_MIN,
        "theme_ratio_max": THEME_RATIO_MAX,
        "target_counts_are_hard": TARGET_COUNTS_ARE_HARD,
    }


def _manifest_payload(
    phase: str,
    dependencies: Dict[str, Any],
    outputs: Sequence[Path],
    complete: bool = True,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    output_hashes = {}
    for path in outputs:
        if path.exists():
            output_hashes[str(path)] = _hash_file(path)
    payload = {
        "phase": phase,
        "schema_version": SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "model": MODEL,
        "configuration": _phase_configuration(),
        "dependencies": dependencies,
        "outputs": output_hashes,
        "complete": bool(complete),
        "generated_at": _utc_now_iso(),
    }
    if extra:
        payload.update(extra)
    payload["manifest_hash"] = _hash_json(payload)
    return payload


def _candidate_count_range(total: int, minimum_ratio: float, maximum_ratio: float) -> Tuple[int, int]:
    minimum = max(1, round(total * minimum_ratio))
    maximum = max(minimum, round(total * maximum_ratio))
    return minimum, maximum


# ═════════════════════════════════════════════════════════════════════════════
# LLM and strict JSON extraction
# ═════════════════════════════════════════════════════════════════════════════

def _load_env() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        sys.exit("DEEPSEEK_API_KEY not found in the environment or .env file.")
    return OpenAI(api_key=api_key, base_url=BASE_URL, timeout=LLM_TIMEOUT_SECONDS)


def _call_llm(
    client: OpenAI,
    system: str,
    user: str,
    max_tokens: int = MIN_MAX_TOKENS,
) -> str:
    """Call the LLM synchronously with exponential backoff and call counting."""
    global _LLM_CALL_COUNT
    requested_tokens = max(MIN_MAX_TOKENS, int(max_tokens))

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            _LLM_CALL_COUNT += 1
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=requested_tokens,
                temperature=TEMPERATURE,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                extra_body={"thinking": {"type": "disabled"}},
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("LLM returned an empty response.")
            return content.strip()
        except Exception as exc:
            if attempt >= MAX_RETRIES:
                raise RuntimeError(
                    "LLM call failed after {0} attempts: {1}".format(MAX_RETRIES, exc)
                ) from exc
            wait = RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
            log.warning(
                "LLM error, attempt %d/%d: %s; retrying in %ds",
                attempt,
                MAX_RETRIES,
                exc,
                wait,
            )
            time.sleep(wait)
    raise RuntimeError("Unreachable LLM retry state.")


def _json_extract(text: str, expected_shape: str) -> Any:
    """
    Extract a top-level JSON object or array and enforce the declared shape.

    The expected shape is a hard constraint. A valid nested object inside an
    expected array, or a valid nested array inside an expected object, is not
    accepted as the top-level response.
    """
    if expected_shape not in ("object", "array"):
        raise ValueError("expected_shape must be 'object' or 'array'.")

    cleaned = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    start_char, end_char = ("{", "}") if expected_shape == "object" else ("[", "]")

    in_string = False
    escaped = False
    depth = 0
    start = None

    for index, char in enumerate(cleaned):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == start_char:
            if depth == 0:
                start = index
            depth += 1
        elif char == end_char and depth > 0:
            depth -= 1
            if depth == 0 and start is not None:
                candidate = cleaned[start : index + 1]
                try:
                    parsed = json.loads(candidate)
                except json.JSONDecodeError:
                    start = None
                    continue
                if expected_shape == "object" and isinstance(parsed, dict):
                    return parsed
                if expected_shape == "array" and isinstance(parsed, list):
                    return parsed
                raise ValueError(
                    "JSON parsed but top-level shape was not {0}.".format(expected_shape)
                )

    raise ValueError(
        "No valid top-level JSON {0} found in LLM output: {1}".format(
            expected_shape, cleaned[:500]
        )
    )


def _llm_json(
    client: OpenAI,
    system: str,
    user: str,
    expected_shape: str,
    max_tokens: int = MIN_MAX_TOKENS,
) -> Any:
    raw = _call_llm(client, system, user, max_tokens=max_tokens)
    return _json_extract(raw, expected_shape=expected_shape)


# ═════════════════════════════════════════════════════════════════════════════
# Embeddings and semantic helpers
# ═════════════════════════════════════════════════════════════════════════════

def _get_embedding_model() -> SentenceTransformer:
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        log.info("Loading embedding model '%s'.", EMBEDDING_MODEL_NAME)
        _EMBEDDING_MODEL = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _EMBEDDING_MODEL


def _encode_texts(texts: Sequence[str]) -> np.ndarray:
    if not texts:
        return np.empty((0, 0), dtype=np.float32)
    model = _get_embedding_model()
    embeddings = model.encode(
        list(texts),
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(embeddings, dtype=np.float32)


def _build_embedding_index(
    candidate_records: Sequence[Dict[str, Any]],
    text_key: str,
    id_key: str,
) -> Dict[str, Any]:
    """Pre-encode a canonical list once for repeated classification queries."""
    records = list(candidate_records)
    texts = [str(item.get(text_key, "")) for item in records]
    return {
        "records": records,
        "texts": texts,
        "text_key": text_key,
        "id_key": id_key,
        "embeddings": _encode_texts(texts),
    }


def _top_matches_from_index(
    query_text: str,
    index: Dict[str, Any],
    top_k: int,
) -> List[Dict[str, Any]]:
    records = index.get("records", [])
    if not records:
        return []
    query_embedding = _encode_texts([query_text])[0]
    scores = index["embeddings"] @ query_embedding
    order = np.argsort(-scores)[: max(1, min(top_k, len(records)))]
    results = []
    for position in order:
        record = records[int(position)]
        results.append(
            {
                "id": record.get(index["id_key"]),
                "text": record.get(index["text_key"]),
                "similarity": float(scores[int(position)]),
            }
        )
    return results


def _cosine_top_matches(
    query_text: str,
    candidate_records: Sequence[Dict[str, Any]],
    text_key: str,
    id_key: str,
    top_k: int,
) -> List[Dict[str, Any]]:
    if not candidate_records:
        return []
    candidate_texts = [str(item.get(text_key, "")) for item in candidate_records]
    embeddings = _encode_texts([query_text] + candidate_texts)
    query = embeddings[0]
    scores = embeddings[1:] @ query
    order = np.argsort(-scores)[: max(1, min(top_k, len(candidate_records)))]
    results = []
    for index in order:
        record = candidate_records[int(index)]
        results.append(
            {
                "id": record.get(id_key),
                "text": record.get(text_key),
                "similarity": float(scores[int(index)]),
            }
        )
    return results


def _semantic_clusters(texts: Sequence[str], threshold: float) -> List[List[int]]:
    """Connected-component clustering from an embedding cosine threshold."""
    count = len(texts)
    if count == 0:
        return []
    if count == 1:
        return [[0]]

    embeddings = _encode_texts(texts)
    parent = list(range(count))

    def find(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    block_size = 512
    for start in range(0, count, block_size):
        end = min(count, start + block_size)
        scores = embeddings[start:end] @ embeddings.T
        for local_index, global_index in enumerate(range(start, end)):
            matches = np.where(scores[local_index, global_index + 1 :] >= threshold)[0]
            for offset in matches:
                union(global_index, global_index + 1 + int(offset))

    grouped = defaultdict(list)  # type: Dict[int, List[int]]
    for index in range(count):
        grouped[find(index)].append(index)
    return list(grouped.values())


def _near_duplicate_pairs(
    records: Sequence[Dict[str, Any]],
    text_key: str,
    id_key: str,
    threshold: float,
) -> List[Dict[str, Any]]:
    """Return the strongest candidate duplicate pairs, capped for file size."""
    if len(records) < 2:
        return []
    texts = [str(record.get(text_key, "")) for record in records]
    embeddings = _encode_texts(texts)
    results = []
    block_size = 512

    for start in range(0, len(records), block_size):
        end = min(len(records), start + block_size)
        scores = embeddings[start:end] @ embeddings.T
        for local_index, left_index in enumerate(range(start, end)):
            right_candidates = np.where(scores[local_index, left_index + 1 :] >= threshold)[0]
            for offset in right_candidates:
                right_index = left_index + 1 + int(offset)
                results.append(
                    {
                        "left_id": records[left_index].get(id_key),
                        "left_text": records[left_index].get(text_key),
                        "right_id": records[right_index].get(id_key),
                        "right_text": records[right_index].get(text_key),
                        "similarity": float(scores[local_index, right_index]),
                    }
                )

    results.sort(key=lambda item: item["similarity"], reverse=True)
    return results[:DUPLICATE_DIAGNOSTIC_MAX_PAIRS]


def _semantic_fingerprint(text: str) -> str:
    """Stable semantic identity marker used for audit/version records."""
    return _sha256_text(_normalise_key(text))


# ═════════════════════════════════════════════════════════════════════════════
# Source-excerpt location and validation helpers
# ═════════════════════════════════════════════════════════════════════════════

def _locate_excerpt(transcript: str, excerpt: str) -> Dict[str, Any]:
    excerpt = str(excerpt or "").strip()
    if not excerpt:
        return {
            "source_excerpt": "",
            "source_match": False,
            "source_location": None,
        }

    excerpt = excerpt[:MAX_SOURCE_EXCERPT_CHARS]
    exact_index = transcript.find(excerpt)
    if exact_index >= 0:
        line_number = transcript.count("\n", 0, exact_index) + 1
        return {
            "source_excerpt": excerpt,
            "source_match": True,
            "source_location": {
                "match_type": "exact",
                "character_start": exact_index,
                "character_end": exact_index + len(excerpt),
                "line_start": line_number,
            },
        }

    normalised_transcript = _normalise_whitespace(transcript)
    normalised_excerpt = _normalise_whitespace(excerpt)
    if normalised_excerpt and normalised_excerpt in normalised_transcript:
        return {
            "source_excerpt": excerpt,
            "source_match": True,
            "source_location": {"match_type": "whitespace_normalised"},
        }

    return {
        "source_excerpt": excerpt,
        "source_match": False,
        "source_location": None,
    }


def _validate_nonempty_string(value: Any, field: str) -> str:
    text = _normalise_whitespace(str(value or ""))
    if not text:
        raise ValueError("Required field '{0}' is empty.".format(field))
    return text


def _clamp_confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(1.0, max(0.0, number))


def _relationship_type_name(value: Any) -> Optional[str]:
    """Return a valid controlled speech-to-CC relationship type or None."""
    text = _normalise_whitespace(str(value or "")).lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "support": "supports",
        "instance": "specific_instance",
        "specific_example": "specific_instance",
        "historical_instance": "historical_example",
        "challenge": "opposition",
        "dispute": "opposition",
        "qualifies": "qualification",
        "qualify": "qualification",
        "applies": "application",
        "empirical_evidence": "evidence",
    }
    text = aliases.get(text, text)
    return text if text in PRIMARY_CC_RELATIONSHIP_TYPES else None


def _relationship_type_label(value: str) -> str:
    labels = {
        "supports": "Supports",
        "specific_instance": "Specific instance",
        "mechanism": "Mechanism",
        "consequence": "Consequence",
        "qualification": "Qualification",
        "opposition": "Opposition",
        "historical_example": "Historical example",
        "application": "Application",
        "evidence": "Evidence",
    }
    return labels.get(value, value.replace("_", " ").title())


def _status_name(value: Any) -> str:
    text = _normalise_whitespace(str(value or "")).lower()
    if "disput" in text or "❌" in text:
        return "Disputed"
    if "unver" in text or "⚠" in text:
        return "Unverifiable"
    return "Verified"


def _status_icon(status: str) -> str:
    return {
        "Verified": "✅",
        "Unverifiable": "⚠️",
        "Disputed": "❌",
    }.get(status, "⚠️")


def _memory_name(value: Any) -> str:
    text = _normalise_whitespace(str(value or "")).lower()
    if text == "corroborated":
        return "Corroborated"
    if text == "contradicted":
        return "Contradicted"
    return "NoInternalBasis"


def _looks_like_proposition(text: str) -> bool:
    """A permissive diagnostic: a CC should contain multiple words and a verb-like token."""
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", text)
    if len(words) < 4:
        return False
    common_verbs = {
        "is", "are", "was", "were", "be", "causes", "cause", "creates",
        "create", "drives", "drive", "leads", "lead", "produces", "produce",
        "increases", "increase", "reduces", "reduce", "distorts", "distort",
        "requires", "require", "depends", "depend", "will", "can", "must",
        "should", "encourages", "encourage", "undermines", "undermine",
        "transfers", "transfer", "raises", "raise", "lowers", "lower",
    }
    lower_words = {word.lower() for word in words}
    return bool(lower_words.intersection(common_verbs)) or any(
        word.lower().endswith(("s", "ed", "ing")) for word in words[1:]
    )


def _looks_like_theme(text: str) -> bool:
    """A permissive noun-phrase diagnostic; warnings do not delete valid Themes."""
    if not text or len(text.split()) > 14:
        return False
    lower = " {0} ".format(text.lower())
    finite_markers = (" is ", " are ", " was ", " were ", " will ", " causes ", " leads ")
    return not any(marker in lower for marker in finite_markers)


# ═════════════════════════════════════════════════════════════════════════════
# LLM prompts — versioned and schema-specific
# ═════════════════════════════════════════════════════════════════════════════

SUMMARISE_SYSTEM = """\
PROMPT_VERSION: {prompt_version}
SCHEMA_VERSION: {schema_version}

You are an expert analyst of financial and economic speeches with expertise in
investment theory. Analyse ONE transcript and extract its SOURCE-LEVEL
intellectual structure. This is not a corpus canonicalisation task.

Return ONLY one top-level JSON OBJECT. Do not use Markdown fences or a preamble.
Use exactly this shape:
{{
  "central_claim": "one full proposition with a verb",
  "themes": [
    {{
      "theme": "specific noun phrase with no finite verb",
      "arguments": [
        {{
          "conclusion": "one declarative, falsifiable conclusion",
          "premises": ["premise 1", "premise 2"],
          "evidence": [
            {{
              "item": "specific fact, statistic, quote, example, or precedent",
              "status": "Verified | Unverifiable | Disputed",
              "verification_basis": "why this workflow label applies",
              "source_excerpt": "exact transcript excerpt when available"
            }}
          ],
          "analogies": [
            {{
              "device": "name or description of analogy/rhetorical device",
              "explanation": "what it is intended to illustrate",
              "source_excerpt": "exact transcript excerpt when available"
            }}
          ]
        }}
      ]
    }}
  ],
  "unverifiable_claims": [
    {{
      "claim": "the exact factual assertion",
      "reason": "why the transcript does not adequately support verification",
      "memory_check": "Corroborated | Contradicted | NoInternalBasis",
      "memory_note": "brief advisory training-knowledge note",
      "source_excerpt": "exact transcript excerpt when available"
    }}
  ],
  "claims_inventory": {{
    "central_claim": "same local central claim",
    "themes": ["local theme labels"],
    "argument_count": 0,
    "unverifiable_count": 0
  }}
}}

Rules:
1. Preserve local wording and distinctions. Do not canonicalise, merge, rename,
   or discard local central claims, Themes, arguments, premises, or evidence.
2. The filename title is only a hint. Infer the central claim from the body.
3. Produce 1 or more Themes. Each Theme is a specific noun phrase, not a full
   proposition and not a generic label such as "Economics".
4. Every argument belongs to exactly one local Theme, has at least one premise,
   and has exactly one conclusion.
5. Evidence labels are transcript-analysis workflow labels only:
   - Verified: the transcript provides an explicit identifiable source,
     quotation, datum, or internally checkable support.
   - Unverifiable: the transcript does not provide enough information to check.
   - Disputed: contradicted or explicitly contested within available transcript
     content or the analysed reasoning.
   They are not external fact-check verdicts. Do not perform web search.
6. source_excerpt must be copied exactly from the transcript when supplied.
   Use an empty string if no exact excerpt can be supplied.
7. Put every explicit unsupported factual assertion in unverifiable_claims,
   including a central claim when the central claim itself makes such an
   unsupported factual assertion.
8. MEMORY is a separate advisory prior. It must not change evidence status or
   determine whether a claim is included.
9. Do not fabricate quotations, numbers, evidence, names, or sources.
""".format(prompt_version=PROMPT_VERSION, schema_version=SCHEMA_VERSION)


CC_DISCOVERY_SYSTEM = """\
PROMPT_VERSION: {prompt_version}
SCHEMA_VERSION: {schema_version}

You are performing corpus-level canonical Central Claim discovery from a batch
of SOURCE-LEVEL central claims. Return ONLY a top-level JSON ARRAY.

Each output object must have this shape:
{{
  "claim": "canonical full proposition with a verb",
  "tagline": "distinct shorthand of no more than 15 words",
  "aliases": ["source-level phrasings represented by this claim"],
  "source_speech_ids": ["SP-..."],
  "subject_theme_labels": ["optional noun phrases"],
  "predicate": "optional relationship/predicate",
  "object_theme_labels": ["optional noun phrases"]
}}

Rules:
- Cluster only the supplied local central claims.
- Produce approximately {minimum}-{maximum} candidates for this batch as a
  diagnostic granularity guide. Semantic coherence takes precedence over count.
- Keep semantically distinct propositions separate even if this yields a count
  outside the guide.
- Merge only genuinely equivalent propositions.
- A canonical CC must be specific enough that many corpus speeches do not fit.
- Where natural, decompose the proposition as Theme + predicate + Theme, but do
  not force artificial Themes or a two-Theme grammar.
- Preserve every represented source_speech_id.
- Do not invent Themes or claims absent from the supplied source claims.
""".format(
    prompt_version=PROMPT_VERSION,
    schema_version=SCHEMA_VERSION,
    minimum=CC_PER_BATCH_MIN,
    maximum=CC_PER_BATCH_MAX,
)


THEME_DISCOVERY_SYSTEM = """\
PROMPT_VERSION: {prompt_version}
SCHEMA_VERSION: {schema_version}

You are performing corpus-level canonical Theme discovery from a batch of
SOURCE-LEVEL Theme labels. Return ONLY a top-level JSON ARRAY.

Each output object must have this shape:
{{
  "theme": "canonical noun phrase with no finite verb",
  "aliases": ["source-level Theme phrasings represented by this Theme"],
  "source_speech_ids": ["SP-..."]
}}

Rules:
- Cluster the supplied local Theme labels independently of Central Claims.
- Produce approximately {minimum}-{maximum} candidates for this batch as a
  diagnostic granularity guide. Semantic coherence takes precedence over count.
- Do not invent the Theme inventory from CC wording.
- Merge only genuinely equivalent or near-synonymous topical concepts.
- Keep analytically distinct concepts separate.
- A Theme may function as subject, object, mechanism, outcome, institution,
  asset, policy, or another concept in a CC.
- Preserve every represented source_speech_id.
""".format(
    prompt_version=PROMPT_VERSION,
    schema_version=SCHEMA_VERSION,
    minimum=T_PER_BATCH_MIN,
    maximum=T_PER_BATCH_MAX,
)


CLASSIFY_SYSTEM = """\
CLASSIFICATION_PROMPT_VERSION: {classification_prompt_version}
CLASSIFICATION_SCHEMA_VERSION: {classification_schema_version}

You are a financial-speech classification assistant. Assign one speech to the
Canonical Central Claim chapter that provides its BEST ARGUMENTATIVE HOME, and
map its local Themes to supplied canonical Theme candidates.

Return ONLY one top-level JSON OBJECT with this exact shape:
{{
  "primary_cc": {{
    "cc_id": "CCn or UNCLASSIFIED",
    "relationship_type": "supports | specific_instance | mechanism | consequence | qualification | opposition | historical_example | application | evidence, or NONE when UNCLASSIFIED",
    "relationship_explanation": "concise explanation of the speech's argumentative role in this chapter",
    "confidence": 0.0
  }},
  "local_theme_mappings": [
    {{
      "local_theme_id": "LT-...",
      "theme_id": "Tn or UNMAPPED",
      "confidence": 0.0,
      "rationale": "concise explanation"
    }}
  ],
  "selected_theme_ids": ["Tn", "Tm"]
}}

Meaning of speech-to-CC assignment:
- Exact semantic equivalence or paraphrase between the local central claim and
  the full canonical CC is NOT required.
- The selected CC must be the chapter in which the speech makes the most
  coherent intellectual contribution.
- A speech can belong because it supports the CC, gives a narrower instance,
  explains a mechanism, develops a consequence, qualifies it, opposes it,
  gives a historical example, applies it to a particular event/policy, or
  supplies evidence.
- Topical similarity alone is insufficient. There must be a meaningful
  argumentative relationship to the canonical proposition.

Controlled relationship types:
- supports: directly argues that the canonical CC is true.
- specific_instance: presents a narrower or concrete instance of the CC.
- mechanism: explains a process through which the CC operates.
- consequence: explains a result or implication of the CC.
- qualification: limits, conditions, refines, or adds an exception to the CC.
- opposition: challenges, disputes, or gives contrary evidence against the CC.
- historical_example: supplies a historical illustration or precedent.
- application: applies the CC to a policy, market, institution, country, period,
  or event.
- evidence: mainly supplies empirical or illustrative evidence relevant to the
  CC rather than independently restating its full thesis.

For each candidate CC, consider:
1. What proposition does the speech itself assert?
2. What role would the speech play inside this candidate chapter?
3. Would placement there develop, support, instantiate, explain, apply,
   qualify, or challenge the chapter proposition?
4. Is another candidate a more coherent argumentative home?

Rules:
- Return one primary CC only when confidence is at least the substantive level
  warranted by the evidence. The program will apply its unchanged numeric
  threshold separately.
- Return UNCLASSIFIED only when NONE of the supplied CCs provides a meaningful
  argumentative home. Do not return UNCLASSIFIED merely because the local claim
  is narrower, more concrete, oppositional, qualified, or differently worded.
- For a classified speech, relationship_type must be exactly one controlled
  value and relationship_explanation must be non-empty.
- For UNCLASSIFIED, use relationship_type "NONE" and explain why no candidate
  provides an argumentative home.
- Map every supplied local Theme independently.
- selected_theme_ids must contain 1-{max_themes} valid canonical Themes for a
  classified speech, chosen from the local Theme mappings.
- Do not infer additional CC assignments merely because a Theme is shared.
- Confidence values must be numbers in [0,1].
- Use only IDs supplied in the candidate lists.
""".format(
    classification_prompt_version=CLASSIFICATION_PROMPT_VERSION,
    classification_schema_version=CLASSIFICATION_SCHEMA_VERSION,
    max_themes=MAX_THEMES_PER_SPEECH,
)


BUCKET_SYNTHESIS_SYSTEM = """\
BUCKET_PROMPT_VERSION: {bucket_prompt_version}
BUCKET_SCHEMA_VERSION: {bucket_schema_version}

You are synthesising intellectual content for EXACTLY ONE validated canonical
Central Claim x canonical Theme pair. Python has already fixed the pair,
grouped source contributions by speech-to-chapter relationship type, and
validated their provenance. Do not introduce other CCs, Themes, relationships,
or source records.

Return ONLY one top-level JSON OBJECT with this shape:
{{
  "pair_id": "PAIR-...",
  "arguments": [
    {{
      "conclusion": "one canonical declarative, falsifiable conclusion",
      "source_contribution_ids": ["CONTRIB-..."],
      "source_speech_filenames": ["YYYYMMDD_Title.md"],
      "premise_synthesis": "paragraph combining premises and preserving variation",
      "conclusion_supported": "precise statement of what is established",
      "evidence": [
        {{
          "item": "evidence item",
          "status": "Verified | Unverifiable | Disputed",
          "verification_basis": "basis retained or carefully synthesised",
          "source_contribution_ids": ["CONTRIB-..."],
          "source_speech_filenames": ["source.md"],
          "source_excerpt": "exact source excerpt when retained"
        }}
      ],
      "rhetorical_devices": [
        {{
          "device": "analogy or rhetorical device",
          "explanation": "what it illustrates",
          "source_contribution_ids": ["CONTRIB-..."],
          "source_speech_filenames": ["source.md"]
        }}
      ],
      "evolution_over_time": "date-aware longitudinal synthesis",
      "disagreements_or_qualifications": ["explicit disagreement, limit, exception, or contrary argument"]
    }}
  ]
}}

Relationship-role rules:
1. Treat supports, specific_instance, mechanism, consequence, application, and
   evidence contributions as possible components of the affirmative case, but
   do not imply that every one independently proves the complete chapter CC.
2. Treat historical_example contributions as illustrations or precedents, not
   automatically as proof.
3. Preserve qualification contributions as limits, conditions, exceptions, or
   refinements. Do NOT rewrite them as unqualified support.
4. Preserve opposition contributions as explicit disagreement or contrary
   argument. Do NOT merge them into an artificial consensus or use them solely
   as affirmative evidence.
5. When qualification or opposition contributions are used by an argument,
   identify them in disagreements_or_qualifications and state whether the
   disagreement concerns facts, mechanisms, assumptions, scope, or conclusion.
6. Do not claim consensus when materially conflicting roles are present.

General rules:
7. Deduplicate only argument conclusions that are equivalent within this exact
   CC x T context. Preserve minority, contradictory, qualified, or superseded
   arguments as distinct conclusions when intellectually meaningful.
8. Every canonical argument must retain at least one valid contribution ID and
   source speech filename from the supplied bucket.
9. Every evidence item and rhetorical device must retain source provenance.
10. Do not fabricate evidence, quotations, dates, filenames, relationship
    types, or source roles.
11. Preserve workflow evidence statuses; do not present them as external checks.
12. If one speech supports an argument, state its date and that cross-speech
    evolution cannot be inferred. If several speeches span more than one year,
    give a longitudinal synthesis. If they span one year or less, state whether
    reasoning is stable or changes within that period.
13. Do not collapse the bucket into a shallow summary.
""".format(
    bucket_prompt_version=BUCKET_PROMPT_VERSION,
    bucket_schema_version=BUCKET_SCHEMA_VERSION,
)


BUCKET_REDUCE_SYSTEM = """\
BUCKET_PROMPT_VERSION: {bucket_prompt_version}
BUCKET_SCHEMA_VERSION: {bucket_schema_version}

You are reducing several partial syntheses for THE SAME canonical CC x T pair.
Return ONLY one top-level JSON OBJECT in the same schema used by the partial
syntheses: {{"pair_id":"...","arguments":[...]}}.

Merge equivalent argument conclusions only within this pair. Preserve all
unique evidence and provenance, minority conclusions, relationship roles,
disagreements, qualifications, opposition, and temporal information. Do not
convert qualification or opposition into affirmative support and do not claim
consensus where partial syntheses conflict. Every final argument and evidence
item must retain valid source_contribution_ids and source_speech_filenames from
the supplied partial syntheses. Do not introduce source-free claims.
""".format(
    bucket_prompt_version=BUCKET_PROMPT_VERSION,
    bucket_schema_version=BUCKET_SCHEMA_VERSION,
)


# ═════════════════════════════════════════════════════════════════════════════
# Phase 1 — source-level speech analysis
# ═════════════════════════════════════════════════════════════════════════════

def _validate_phase1_payload(
    payload: Dict[str, Any],
    transcript: str,
    filename: str,
    speech_id: str,
    source_hash: str,
) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Phase 1 response must be an object.")

    central_claim = _validate_nonempty_string(payload.get("central_claim"), "central_claim")
    if not _looks_like_proposition(central_claim):
        log.warning("Local central claim may not be a full proposition: %s", central_claim)

    raw_themes = payload.get("themes")
    if not isinstance(raw_themes, list) or not raw_themes:
        raise ValueError("Phase 1 themes must be a non-empty list.")

    validated_themes = []
    argument_count = 0

    for theme_index, raw_theme in enumerate(raw_themes, 1):
        if not isinstance(raw_theme, dict):
            continue
        theme_text = _validate_nonempty_string(
            raw_theme.get("theme"), "themes[{0}].theme".format(theme_index)
        )
        if not _looks_like_theme(theme_text):
            log.warning("Local Theme may not be a noun phrase: %s", theme_text)
        local_theme_id = _stable_local_id(
            "LT", speech_id, "theme-{0}".format(theme_index), theme_text
        )

        raw_arguments = raw_theme.get("arguments")
        if not isinstance(raw_arguments, list) or not raw_arguments:
            raise ValueError("Every local Theme must contain at least one argument.")

        validated_arguments = []
        for argument_index, raw_argument in enumerate(raw_arguments, 1):
            if not isinstance(raw_argument, dict):
                continue
            conclusion = _validate_nonempty_string(
                raw_argument.get("conclusion"),
                "argument conclusion",
            )
            local_argument_id = _stable_local_id(
                "LA",
                speech_id,
                "theme-{0}-argument-{1}".format(theme_index, argument_index),
                conclusion,
            )

            premises = raw_argument.get("premises")
            if not isinstance(premises, list):
                premises = []
            premises = [_normalise_whitespace(item) for item in premises if _normalise_whitespace(item)]
            if not premises:
                raise ValueError("Every local argument must contain at least one premise.")

            evidence_items = []
            raw_evidence = raw_argument.get("evidence")
            if not isinstance(raw_evidence, list):
                raw_evidence = []
            for evidence_index, evidence in enumerate(raw_evidence, 1):
                if not isinstance(evidence, dict):
                    continue
                item = _normalise_whitespace(evidence.get("item", ""))
                if not item:
                    continue
                status = _status_name(evidence.get("status"))
                basis = _normalise_whitespace(evidence.get("verification_basis", ""))
                if not basis:
                    basis = "No verification basis supplied by the Phase 1 model."
                location = _locate_excerpt(transcript, evidence.get("source_excerpt", ""))
                evidence_id = _stable_local_id(
                    "EV",
                    speech_id,
                    "{0}-evidence-{1}".format(local_argument_id, evidence_index),
                    item,
                )
                evidence_items.append(
                    {
                        "evidence_id": evidence_id,
                        "item": item,
                        "status": status,
                        "verification_basis": basis,
                        "speech_id": speech_id,
                        "source_speech_filename": filename,
                        **location,
                    }
                )

            analogies = []
            raw_analogies = raw_argument.get("analogies")
            if not isinstance(raw_analogies, list):
                raw_analogies = []
            for analogy_index, analogy in enumerate(raw_analogies, 1):
                if isinstance(analogy, str):
                    analogy = {"device": analogy, "explanation": "", "source_excerpt": ""}
                if not isinstance(analogy, dict):
                    continue
                device = _normalise_whitespace(analogy.get("device", ""))
                if not device:
                    continue
                explanation = _normalise_whitespace(analogy.get("explanation", ""))
                location = _locate_excerpt(transcript, analogy.get("source_excerpt", ""))
                device_id = _stable_local_id(
                    "RD",
                    speech_id,
                    "{0}-device-{1}".format(local_argument_id, analogy_index),
                    device,
                )
                analogies.append(
                    {
                        "device_id": device_id,
                        "device": device,
                        "explanation": explanation,
                        "speech_id": speech_id,
                        "source_speech_filename": filename,
                        **location,
                    }
                )

            validated_arguments.append(
                {
                    "local_argument_id": local_argument_id,
                    "local_theme_id": local_theme_id,
                    "conclusion": conclusion,
                    "premises": premises,
                    "evidence": evidence_items,
                    "analogies": analogies,
                }
            )
            argument_count += 1

        validated_themes.append(
            {
                "local_theme_id": local_theme_id,
                "theme": theme_text,
                "arguments": validated_arguments,
            }
        )

    unverifiable_claims = []
    raw_unverifiable = payload.get("unverifiable_claims")
    if not isinstance(raw_unverifiable, list):
        raw_unverifiable = []
    for claim_index, raw_claim in enumerate(raw_unverifiable, 1):
        if not isinstance(raw_claim, dict):
            continue
        claim = _normalise_whitespace(raw_claim.get("claim", ""))
        if not claim:
            continue
        reason = _normalise_whitespace(raw_claim.get("reason", ""))
        if not reason:
            reason = "The transcript does not supply enough identifiable support."
        location = _locate_excerpt(transcript, raw_claim.get("source_excerpt", ""))
        unverifiable_id = _stable_local_id(
            "UV", speech_id, "unverifiable-{0}".format(claim_index), claim
        )
        unverifiable_claims.append(
            {
                "unverifiable_id": unverifiable_id,
                "speech_id": speech_id,
                "speech_ref": filename,
                "claim": claim,
                "reason": reason,
                "memory_check": _memory_name(raw_claim.get("memory_check")),
                "memory_note": _normalise_whitespace(raw_claim.get("memory_note", "")),
                **location,
            }
        )

    date = _parse_date_from_filename(filename)
    claims_inventory = {
        "central_claim": central_claim,
        "themes": [theme["theme"] for theme in validated_themes],
        "argument_count": argument_count,
        "unverifiable_count": len(unverifiable_claims),
    }

    record = {
        "record_kind": PHASE1_RECORD_KIND,
        "schema_version": SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "model": MODEL,
        "speech_id": speech_id,
        "filename": filename,
        "stem": Path(filename).stem,
        "date": date,
        "source_hash": source_hash,
        "source_character_count": len(transcript),
        "central_claim": central_claim,
        "themes": validated_themes,
        "unverifiable_claims": unverifiable_claims,
        "claims_inventory": claims_inventory,
        "generated_at": _utc_now_iso(),
    }
    record["record_hash"] = _hash_json(record)
    return record


def phase1_summarise(client: OpenAI, transcripts: Sequence[Path]) -> List[Dict[str, Any]]:
    log.info("=== PHASE 1: SUMMARISE ===")
    records = []
    processed = 0
    skipped = 0
    failed = 0

    for index, path in enumerate(transcripts, 1):
        filename = path.name
        speech_id = _stable_speech_id(filename)
        output_path = PHASE1_DIR / (path.stem + ".json")
        transcript = _load_transcript(path)
        source_hash = _sha256_text(transcript)
        dependencies = {
            "source_hash": source_hash,
            "filename": filename,
            "model": MODEL,
            "prompt_version": PROMPT_VERSION,
            "schema_version": SCHEMA_VERSION,
            "max_transcript_chars": MAX_TRANSCRIPT_CHARS,
        }

        existing = _read_json_if_exists(output_path)
        if isinstance(existing, dict) and existing.get("dependencies") == dependencies:
            try:
                validated = existing.get("record")
                if not isinstance(validated, dict):
                    raise ValueError("Missing Phase 1 record wrapper.")
                records.append(validated)
                skipped += 1
                log.debug("Phase 1 skip: %s", filename)
                continue
            except Exception as exc:
                log.warning("Invalid Phase 1 checkpoint %s: %s", output_path, exc)

        log.info("[%d/%d] Analysing %s", index, len(transcripts), filename)
        prompt_transcript = transcript
        analysis_truncated = False
        if len(prompt_transcript) > MAX_TRANSCRIPT_CHARS:
            prompt_transcript = prompt_transcript[:MAX_TRANSCRIPT_CHARS]
            analysis_truncated = True
            log.warning(
                "Transcript %s exceeds %d characters and was truncated for the LLM call.",
                filename,
                MAX_TRANSCRIPT_CHARS,
            )

        user_prompt = (
            "Speech filename: {0}\n"
            "Parsed date: {1}\n"
            "Stable speech_id: {2}\n\n"
            "TRANSCRIPT:\n{3}"
        ).format(filename, _parse_date_from_filename(filename), speech_id, prompt_transcript)

        try:
            payload = _llm_json(
                client,
                SUMMARISE_SYSTEM,
                user_prompt,
                expected_shape="object",
                max_tokens=12_000,
            )
            record = _validate_phase1_payload(
                payload, transcript, filename, speech_id, source_hash
            )
            record["analysis_truncated"] = analysis_truncated
            record["record_hash"] = _hash_json(record)
            wrapper = {
                "dependencies": dependencies,
                "record": record,
                "output_hash": _hash_json(record),
                "complete": True,
            }
            _write_json(output_path, wrapper)
            records.append(record)
            processed += 1
        except Exception as exc:
            failed += 1
            log.error("Phase 1 failed for %s: %s", filename, exc)
            log.debug(traceback.format_exc())

    manifest_dependencies = {
        "source_files": [
            {"filename": path.name, "source_hash": _hash_file(path)} for path in transcripts
        ],
        "configuration": _phase_configuration(),
    }
    output_files = sorted(PHASE1_DIR.glob("*.json"))
    manifest = _manifest_payload(
        "phase1",
        manifest_dependencies,
        output_files,
        complete=(failed == 0),
        extra={
            "source_count": len(transcripts),
            "valid_record_count": len(records),
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "llm_calls_total_so_far": _LLM_CALL_COUNT,
        },
    )
    _write_json(PHASE1_DIR / "manifest.json", manifest)
    log.info(
        "Phase 1 complete: %d processed, %d reused, %d failed.",
        processed,
        skipped,
        failed,
    )
    return records


# ═════════════════════════════════════════════════════════════════════════════
# Phase 2 — complete inventory and duplicate diagnostics
# ═════════════════════════════════════════════════════════════════════════════

def _load_all_valid_phase1_records() -> List[Dict[str, Any]]:
    records = []
    for path in sorted(PHASE1_DIR.glob("*.json")):
        if path.name == "manifest.json":
            continue
        wrapper = _read_json_if_exists(path)
        if not isinstance(wrapper, dict):
            continue
        record = wrapper.get("record")
        if not isinstance(record, dict):
            continue
        if record.get("record_kind") != PHASE1_RECORD_KIND:
            continue
        if record.get("schema_version") != SCHEMA_VERSION:
            continue
        records.append(record)
    return records


def phase2_inventory(phase1_records: Optional[Sequence[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    log.info("=== PHASE 2: INVENTORY ===")
    records = list(phase1_records or _load_all_valid_phase1_records())
    records.sort(key=lambda item: (item.get("date", ""), item.get("filename", "")))

    phase1_manifest = _read_json_if_exists(PHASE1_DIR / "manifest.json") or {}
    dependencies = {
        "phase1_manifest_hash": phase1_manifest.get("manifest_hash"),
        "record_hashes": sorted(record.get("record_hash", "") for record in records),
        "embedding_model": EMBEDDING_MODEL_NAME,
        "cc_threshold": CC_DEDUP_THRESHOLD,
        "theme_threshold": THEME_DEDUP_THRESHOLD,
        "schema_version": SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
    }

    existing_manifest = _read_json_if_exists(INVENTORY_MANIFEST)
    if (
        isinstance(existing_manifest, dict)
        and existing_manifest.get("complete")
        and existing_manifest.get("dependencies") == dependencies
        and MASTER_INVENTORY.exists()
        and DUPLICATE_DIAGNOSTICS.exists()
    ):
        log.info("Phase 2 dependencies unchanged; reusing master inventory.")
        inventory = _read_json(MASTER_INVENTORY)
        return inventory if isinstance(inventory, list) else records

    _write_json(MASTER_INVENTORY, records)

    local_claim_records = [
        {
            "entity_id": "{0}:cc".format(record["speech_id"]),
            "speech_id": record["speech_id"],
            "text": record["central_claim"],
        }
        for record in records
    ]
    local_theme_records = []
    for record in records:
        for theme in record.get("themes", []):
            local_theme_records.append(
                {
                    "entity_id": theme.get("local_theme_id"),
                    "speech_id": record.get("speech_id"),
                    "text": theme.get("theme", ""),
                }
            )

    cc_pairs = _near_duplicate_pairs(
        local_claim_records,
        text_key="text",
        id_key="entity_id",
        threshold=CC_DEDUP_THRESHOLD,
    )
    theme_pairs = _near_duplicate_pairs(
        local_theme_records,
        text_key="text",
        id_key="entity_id",
        threshold=THEME_DEDUP_THRESHOLD,
    )
    diagnostics = {
        "schema_version": SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "embedding_model": EMBEDDING_MODEL_NAME,
        "cc_threshold": CC_DEDUP_THRESHOLD,
        "theme_threshold": THEME_DEDUP_THRESHOLD,
        "central_claim_candidate_pairs": cc_pairs,
        "theme_candidate_pairs": theme_pairs,
        "note": "Diagnostic candidates only; Phase 2 does not merge source entities.",
    }
    _write_json(DUPLICATE_DIAGNOSTICS, diagnostics)

    manifest = _manifest_payload(
        "phase2",
        dependencies,
        [MASTER_INVENTORY, DUPLICATE_DIAGNOSTICS],
        complete=True,
        extra={
            "transcript_count": len(records),
            "sorted_source_hashes": sorted(record.get("source_hash", "") for record in records),
            "inventory_hash": _hash_json(records),
            "local_central_claim_count": len(local_claim_records),
            "local_theme_count": len(local_theme_records),
            "cc_duplicate_candidate_count": len(cc_pairs),
            "theme_duplicate_candidate_count": len(theme_pairs),
        },
    )
    _write_json(INVENTORY_MANIFEST, manifest)
    log.info(
        "Phase 2 complete: %d speeches, %d local Themes, %d CC duplicate candidates, %d Theme duplicate candidates.",
        len(records),
        len(local_theme_records),
        len(cc_pairs),
        len(theme_pairs),
    )
    return records


# ═════════════════════════════════════════════════════════════════════════════
# Phase 3 — canonical discovery, mappings, classifications, and CC x T pairs
# ═════════════════════════════════════════════════════════════════════════════

def _discovery_batch_cache_path(kind: str, start: int, end: int, input_hash: str) -> Path:
    return PHASE3_DIR / "discovery_{0}_{1}_{2}_{3}.json".format(
        kind, start, end, input_hash[:12]
    )


def _recursive_discovery_call(
    client: OpenAI,
    records: Sequence[Dict[str, Any]],
    kind: str,
    system_prompt: str,
    label: str,
) -> List[Dict[str, Any]]:
    """Call discovery; recursively halve malformed batches down to one item."""
    if kind == "cc":
        lines = [
            "{0}. speech_id={1} | local_cc={2}".format(
                index + 1, record["speech_id"], record["text"]
            )
            for index, record in enumerate(records)
        ]
    else:
        lines = [
            "{0}. speech_id={1} | local_theme_id={2} | local_theme={3}".format(
                index + 1,
                record["speech_id"],
                record["local_theme_id"],
                record["text"],
            )
            for index, record in enumerate(records)
        ]
    user_prompt = "SOURCE RECORDS:\n" + "\n".join(lines)

    try:
        response = _llm_json(
            client,
            system_prompt,
            user_prompt,
            expected_shape="array",
            max_tokens=16_000,
        )
        if not isinstance(response, list):
            raise ValueError("Discovery response was not an array.")
        return [item for item in response if isinstance(item, dict)]
    except Exception as exc:
        if len(records) <= 1:
            log.error("Discovery failed for singleton batch %s: %s", label, exc)
            return []
        midpoint = len(records) // 2
        log.warning(
            "Discovery batch %s failed (%s); splitting %d records into %d and %d.",
            label,
            exc,
            len(records),
            midpoint,
            len(records) - midpoint,
        )
        left = _recursive_discovery_call(
            client, records[:midpoint], kind, system_prompt, label + "a"
        )
        right = _recursive_discovery_call(
            client, records[midpoint:], kind, system_prompt, label + "b"
        )
        return left + right


def _discover_candidates(
    client: OpenAI,
    source_records: Sequence[Dict[str, Any]],
    kind: str,
) -> List[Dict[str, Any]]:
    system_prompt = CC_DISCOVERY_SYSTEM if kind == "cc" else THEME_DISCOVERY_SYSTEM
    candidates = []

    for start in range(0, len(source_records), DISCOVERY_BATCH_SIZE):
        batch = list(source_records[start : start + DISCOVERY_BATCH_SIZE])
        end = start + len(batch)
        batch_input = {
            "kind": kind,
            "records": batch,
            "prompt_version": PROMPT_VERSION,
            "schema_version": SCHEMA_VERSION,
            "model": MODEL,
        }
        input_hash = _hash_json(batch_input)
        cache_path = _discovery_batch_cache_path(kind, start + 1, end, input_hash)
        cached = _read_json_if_exists(cache_path)
        if isinstance(cached, dict) and cached.get("input_hash") == input_hash:
            batch_candidates = cached.get("candidates", [])
            log.debug("Reusing %s discovery batch %d-%d.", kind, start + 1, end)
        else:
            log.info("Discovering canonical %s candidates from records %d-%d.", kind, start + 1, end)
            batch_candidates = _recursive_discovery_call(
                client,
                batch,
                kind,
                system_prompt,
                "{0}-{1}".format(start + 1, end),
            )
            _write_json(
                cache_path,
                {
                    "input_hash": input_hash,
                    "kind": kind,
                    "candidates": batch_candidates,
                    "complete": True,
                },
            )
        candidates.extend(batch_candidates)
    return candidates


def _validate_cc_candidates(
    raw_candidates: Sequence[Dict[str, Any]],
    valid_speech_ids: Set[str],
) -> List[Dict[str, Any]]:
    candidates = []
    for raw in raw_candidates:
        claim = _normalise_whitespace(raw.get("claim", ""))
        if not claim:
            continue
        if not _looks_like_proposition(claim):
            log.warning("Canonical CC candidate may lack a clear predicate: %s", claim)
        tagline = _normalise_whitespace(raw.get("tagline", ""))
        if not tagline or tagline.lower() == claim.lower():
            tagline = " ".join(claim.split()[:15])
        tagline = " ".join(tagline.split()[:15])
        aliases = raw.get("aliases") if isinstance(raw.get("aliases"), list) else []
        aliases = sorted({_normalise_whitespace(alias) for alias in aliases if _normalise_whitespace(alias)})
        source_ids = raw.get("source_speech_ids") if isinstance(raw.get("source_speech_ids"), list) else []
        source_ids = sorted({str(value) for value in source_ids if str(value) in valid_speech_ids})
        candidates.append(
            {
                "claim": claim,
                "tagline": tagline,
                "aliases": aliases,
                "source_speech_ids": source_ids,
                "subject_theme_labels": [
                    _normalise_whitespace(value)
                    for value in (raw.get("subject_theme_labels") or [])
                    if _normalise_whitespace(value)
                ],
                "predicate": _normalise_whitespace(raw.get("predicate", "")),
                "object_theme_labels": [
                    _normalise_whitespace(value)
                    for value in (raw.get("object_theme_labels") or [])
                    if _normalise_whitespace(value)
                ],
            }
        )
    return candidates


def _validate_theme_candidates(
    raw_candidates: Sequence[Dict[str, Any]],
    valid_speech_ids: Set[str],
) -> List[Dict[str, Any]]:
    candidates = []
    for raw in raw_candidates:
        theme = _normalise_whitespace(raw.get("theme", ""))
        if not theme:
            continue
        if not _looks_like_theme(theme):
            log.warning("Canonical Theme candidate may contain a finite verb: %s", theme)
        aliases = raw.get("aliases") if isinstance(raw.get("aliases"), list) else []
        aliases = sorted({_normalise_whitespace(alias) for alias in aliases if _normalise_whitespace(alias)})
        source_ids = raw.get("source_speech_ids") if isinstance(raw.get("source_speech_ids"), list) else []
        source_ids = sorted({str(value) for value in source_ids if str(value) in valid_speech_ids})
        candidates.append(
            {
                "theme": theme,
                "aliases": aliases,
                "source_speech_ids": source_ids,
            }
        )
    return candidates


def _merge_candidate_clusters(
    candidates: Sequence[Dict[str, Any]],
    kind: str,
    threshold: float,
) -> List[Dict[str, Any]]:
    text_key = "claim" if kind == "cc" else "theme"
    texts = [candidate[text_key] for candidate in candidates]
    clusters = _semantic_clusters(texts, threshold)
    merged = []

    for cluster in clusters:
        members = [candidates[index] for index in cluster]
        # Prefer the most informative representative, then deterministic lexical order.
        representative = sorted(
            members,
            key=lambda item: (-len(item.get(text_key, "")), item.get(text_key, "").lower()),
        )[0]
        combined = copy.deepcopy(representative)
        combined_aliases = set(combined.get("aliases", []))
        combined_sources = set(combined.get("source_speech_ids", []))
        merged_from_texts = []
        for member in members:
            combined_aliases.update(member.get("aliases", []))
            combined_sources.update(member.get("source_speech_ids", []))
            if member.get(text_key) != combined.get(text_key):
                combined_aliases.add(member.get(text_key, ""))
                merged_from_texts.append(member.get(text_key, ""))
            if kind == "cc":
                combined.setdefault("subject_theme_labels", [])
                combined.setdefault("object_theme_labels", [])
                combined["subject_theme_labels"] = sorted(
                    set(combined["subject_theme_labels"]).union(member.get("subject_theme_labels", []))
                )
                combined["object_theme_labels"] = sorted(
                    set(combined["object_theme_labels"]).union(member.get("object_theme_labels", []))
                )
                if not combined.get("predicate") and member.get("predicate"):
                    combined["predicate"] = member["predicate"]
        combined["aliases"] = sorted(alias for alias in combined_aliases if alias)
        combined["source_speech_ids"] = sorted(combined_sources)
        combined["merged_candidate_texts"] = sorted(set(merged_from_texts))
        merged.append(combined)

    merged.sort(key=lambda item: item[text_key].lower())
    return merged


def _next_numeric_id(prefix: str, used_ids: Set[str]) -> str:
    numbers = []
    pattern = re.compile(r"^{0}(\d+)$".format(re.escape(prefix)))
    for identifier in used_ids:
        match = pattern.match(identifier)
        if match:
            numbers.append(int(match.group(1)))
    next_number = max(numbers, default=0) + 1
    while "{0}{1}".format(prefix, next_number) in used_ids:
        next_number += 1
    return "{0}{1}".format(prefix, next_number)


def _assign_stable_ids(
    new_entities: Sequence[Dict[str, Any]],
    old_entities: Sequence[Dict[str, Any]],
    kind: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Reuse old IDs for materially equivalent entities and audit supersession."""
    text_key = "claim" if kind == "cc" else "theme"
    id_key = "cc_id" if kind == "cc" else "theme_id"
    prefix = "CC" if kind == "cc" else "T"

    old_entities = [item for item in old_entities if item.get(id_key) and item.get(text_key)]
    used_old_ids = set()  # type: Set[str]
    used_ids = {str(item.get(id_key)) for item in old_entities if item.get(id_key)}
    assignments = []
    history = {
        "kind": kind,
        "reused": [],
        "created": [],
        "superseded": [],
    }

    if new_entities and old_entities:
        new_embeddings = _encode_texts([entity[text_key] for entity in new_entities])
        old_embeddings = _encode_texts([entity[text_key] for entity in old_entities])
        similarity = new_embeddings @ old_embeddings.T
    else:
        similarity = np.empty((len(new_entities), len(old_entities)), dtype=np.float32)

    # Match strongest pairs globally so one old ID cannot be reused twice.
    candidate_matches = []
    for new_index in range(len(new_entities)):
        for old_index in range(len(old_entities)):
            score = float(similarity[new_index, old_index])
            if score >= CANONICAL_STABILITY_THRESHOLD:
                candidate_matches.append((score, new_index, old_index))
    candidate_matches.sort(reverse=True)

    matched_new = {}  # type: Dict[int, Tuple[int, float]]
    for score, new_index, old_index in candidate_matches:
        old_id = str(old_entities[old_index][id_key])
        if new_index in matched_new or old_id in used_old_ids:
            continue
        matched_new[new_index] = (old_index, score)
        used_old_ids.add(old_id)

    for new_index, entity in enumerate(new_entities):
        record = copy.deepcopy(entity)
        if new_index in matched_new:
            old_index, score = matched_new[new_index]
            old = old_entities[old_index]
            identifier = str(old[id_key])
            record[id_key] = identifier
            record["previous_text"] = old.get(text_key)
            record["stability_similarity"] = score
            record["merged_from"] = sorted(
                set(old.get("merged_from", []) + record.get("merged_candidate_texts", []))
            )
            history["reused"].append(
                {
                    id_key: identifier,
                    "old_text": old.get(text_key),
                    "new_text": record.get(text_key),
                    "similarity": score,
                }
            )
        else:
            identifier = _next_numeric_id(prefix, used_ids)
            used_ids.add(identifier)
            record[id_key] = identifier
            record["stability_similarity"] = None
            record["merged_from"] = sorted(set(record.get("merged_candidate_texts", [])))
            history["created"].append({id_key: identifier, text_key: record.get(text_key)})
        record.pop("merged_candidate_texts", None)
        record["semantic_fingerprint"] = _semantic_fingerprint(record[text_key])
        record["superseded_by"] = None
        assignments.append(record)

    reused_ids = {record[id_key] for record in assignments}
    for old in old_entities:
        old_id = str(old[id_key])
        if old_id not in reused_ids:
            # Best new entity is recorded for audit but not silently treated as equivalent.
            best_new = None
            best_score = 0.0
            if len(new_entities):
                old_index = next(
                    index for index, item in enumerate(old_entities) if item[id_key] == old[id_key]
                )
                scores = similarity[:, old_index]
                if len(scores):
                    best_index = int(np.argmax(scores))
                    best_score = float(scores[best_index])
                    best_new = assignments[best_index].get(id_key)
            history["superseded"].append(
                {
                    id_key: old_id,
                    "old_text": old.get(text_key),
                    "best_new_id": best_new,
                    "best_similarity": best_score,
                }
            )

    assignments.sort(key=lambda item: _numeric_id_sort_key(item[id_key]))
    return assignments, history


def _map_cc_decomposition_to_theme_ids(
    canonical_ccs: List[Dict[str, Any]],
    canonical_themes: Sequence[Dict[str, Any]],
) -> None:
    if not canonical_themes:
        return
    for cc in canonical_ccs:
        subject_ids = []
        object_ids = []
        for label in cc.get("subject_theme_labels", []):
            matches = _cosine_top_matches(
                label,
                canonical_themes,
                text_key="theme",
                id_key="theme_id",
                top_k=1,
            )
            if matches and matches[0]["similarity"] >= THEME_MAPPING_CONFIDENCE_MIN:
                subject_ids.append(matches[0]["id"])
        for label in cc.get("object_theme_labels", []):
            matches = _cosine_top_matches(
                label,
                canonical_themes,
                text_key="theme",
                id_key="theme_id",
                top_k=1,
            )
            if matches and matches[0]["similarity"] >= THEME_MAPPING_CONFIDENCE_MIN:
                object_ids.append(matches[0]["id"])
        cc["subject_theme_ids"] = sorted(set(subject_ids), key=_numeric_id_sort_key)
        cc["object_theme_ids"] = sorted(set(object_ids), key=_numeric_id_sort_key)


def _classification_candidates_for_speech(
    record: Dict[str, Any],
    canonical_ccs: Sequence[Dict[str, Any]],
    canonical_themes: Sequence[Dict[str, Any]],
    cc_embedding_index: Dict[str, Any],
    theme_embedding_index: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]]:
    cc_matches = _top_matches_from_index(
        record["central_claim"],
        cc_embedding_index,
        top_k=CLASSIFICATION_CC_CANDIDATES,
    )
    cc_ids = {match["id"] for match in cc_matches}
    cc_candidates = [item for item in canonical_ccs if item.get("cc_id") in cc_ids]

    theme_matches_by_local = {}
    selected_theme_ids = set()
    for local_theme in record.get("themes", []):
        matches = _top_matches_from_index(
            local_theme.get("theme", ""),
            theme_embedding_index,
            top_k=CLASSIFICATION_THEME_CANDIDATES_PER_LOCAL_THEME,
        )
        theme_matches_by_local[local_theme["local_theme_id"]] = matches
        selected_theme_ids.update(match["id"] for match in matches)
    theme_candidates = [
        item for item in canonical_themes if item.get("theme_id") in selected_theme_ids
    ]
    return cc_candidates, theme_candidates, theme_matches_by_local, cc_matches

def _classify_one_speech(
    client: OpenAI,
    record: Dict[str, Any],
    canonical_ccs: Sequence[Dict[str, Any]],
    canonical_themes: Sequence[Dict[str, Any]],
    cc_embedding_index: Dict[str, Any],
    theme_embedding_index: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    cc_candidates, theme_candidates, embedding_theme_matches, cc_matches = _classification_candidates_for_speech(
        record, canonical_ccs, canonical_themes, cc_embedding_index, theme_embedding_index
    )
    cc_candidate_ids = {item["cc_id"] for item in cc_candidates}
    theme_candidate_ids = {item["theme_id"] for item in theme_candidates}

    user_payload = {
        "speech": {
            "speech_id": record["speech_id"],
            "filename": record["filename"],
            "local_central_claim": record["central_claim"],
            "local_themes": [
                {
                    "local_theme_id": theme["local_theme_id"],
                    "theme": theme["theme"],
                }
                for theme in record.get("themes", [])
            ],
            "local_argument_conclusions": [
                {
                    "local_theme_id": theme["local_theme_id"],
                    "local_argument_id": argument.get("local_argument_id"),
                    "conclusion": argument.get("conclusion", ""),
                }
                for theme in record.get("themes", [])
                for argument in theme.get("arguments", [])
            ],
        },
        "canonical_cc_candidates": [
            {
                "cc_id": item["cc_id"],
                "claim": item["claim"],
                "tagline": item.get("tagline", ""),
            }
            for item in cc_candidates
        ],
        "canonical_theme_candidates": [
            {"theme_id": item["theme_id"], "theme": item["theme"]}
            for item in theme_candidates
        ],
        "embedding_diagnostics": {
            "cc_matches": cc_matches,
            "theme_matches_by_local_theme": embedding_theme_matches,
        },
    }
    response = _llm_json(
        client,
        CLASSIFY_SYSTEM,
        json.dumps(user_payload, ensure_ascii=False, indent=2),
        expected_shape="object",
        max_tokens=MIN_MAX_TOKENS,
    )

    primary = response.get("primary_cc") if isinstance(response.get("primary_cc"), dict) else {}
    cc_id = str(primary.get("cc_id", "UNCLASSIFIED"))
    cc_confidence = _clamp_confidence(primary.get("confidence"))
    relationship_type = _relationship_type_name(primary.get("relationship_type"))
    relationship_explanation = _normalise_whitespace(
        primary.get("relationship_explanation", primary.get("rationale", ""))
    )

    rejection_reasons = []
    if cc_id not in cc_candidate_ids:
        rejection_reasons.append("No supplied canonical CC was selected.")
    if cc_confidence < CLASSIFICATION_CONFIDENCE_MIN:
        rejection_reasons.append(
            "The unchanged classification confidence threshold of {0:.2f} was not cleared.".format(
                CLASSIFICATION_CONFIDENCE_MIN
            )
        )
    if relationship_type is None:
        rejection_reasons.append("No valid controlled argumentative relationship type was returned.")
    if not relationship_explanation:
        rejection_reasons.append("No speech-to-chapter relationship explanation was returned.")

    if rejection_reasons:
        best_candidates = cc_matches[:5]
        classification = {
            "speech_id": record["speech_id"],
            "filename": record["filename"],
            "status": "uncategorised",
            "classification_prompt_version": CLASSIFICATION_PROMPT_VERSION,
            "classification_schema_version": CLASSIFICATION_SCHEMA_VERSION,
            "primary_cc_id": None,
            "primary_cc_confidence": cc_confidence,
            "primary_cc_relationship_type": None,
            "primary_cc_relationship_explanation": relationship_explanation,
            # Backward-compatible explanatory field used by existing logs/evaluators.
            "primary_cc_rationale": relationship_explanation or " ".join(rejection_reasons),
            "classification_rejection_reasons": rejection_reasons,
            "theme_ids": [],
            "theme_assignments": [],
            "best_cc_candidates": best_candidates,
            "bucket_memberships": [],
        }
    else:
        classification = {
            "speech_id": record["speech_id"],
            "filename": record["filename"],
            "status": "categorised",
            "classification_prompt_version": CLASSIFICATION_PROMPT_VERSION,
            "classification_schema_version": CLASSIFICATION_SCHEMA_VERSION,
            "primary_cc_id": cc_id,
            "primary_cc_confidence": cc_confidence,
            "primary_cc_relationship_type": relationship_type,
            "primary_cc_relationship_explanation": relationship_explanation,
            # Retained for compatibility; it is identical to the explicit explanation.
            "primary_cc_rationale": relationship_explanation,
            "classification_rejection_reasons": [],
            "theme_ids": [],
            "theme_assignments": [],
            "best_cc_candidates": [],
            "bucket_memberships": [],
        }

    raw_theme_mappings = response.get("local_theme_mappings")
    if not isinstance(raw_theme_mappings, list):
        raw_theme_mappings = []
    response_by_local = {
        str(item.get("local_theme_id")): item
        for item in raw_theme_mappings
        if isinstance(item, dict)
    }

    mapping_records = []
    valid_selected = []
    for local_theme in record.get("themes", []):
        local_id = local_theme["local_theme_id"]
        local_text = local_theme["theme"]
        raw_mapping = response_by_local.get(local_id, {})
        theme_id = str(raw_mapping.get("theme_id", "UNMAPPED"))
        confidence = _clamp_confidence(raw_mapping.get("confidence"))
        rationale = _normalise_whitespace(raw_mapping.get("rationale", ""))

        allowed_for_local = {
            match["id"] for match in embedding_theme_matches.get(local_id, [])
        }
        if theme_id not in theme_candidate_ids or theme_id not in allowed_for_local:
            theme_id = "UNMAPPED"
            confidence = 0.0
        if theme_id != "UNMAPPED" and confidence >= THEME_MAPPING_CONFIDENCE_MIN:
            valid_selected.append((theme_id, confidence, local_id, rationale))

        mapping_records.append(
            {
                "mapping_type": "local_theme_to_canonical_theme",
                "speech_id": record["speech_id"],
                "filename": record["filename"],
                "local_theme_id": local_id,
                "local_theme_text": local_text,
                "canonical_theme_id": None if theme_id == "UNMAPPED" else theme_id,
                "confidence": confidence,
                "rationale": rationale,
                "candidate_matches": embedding_theme_matches.get(local_id, []),
            }
        )

    # Include LLM-selected IDs first, then highest-confidence mapped Themes.
    selected_from_response = response.get("selected_theme_ids")
    if not isinstance(selected_from_response, list):
        selected_from_response = []
    ranked = []
    seen = set()
    valid_mapping_by_theme = defaultdict(list)
    for theme_id, confidence, local_id, rationale in valid_selected:
        valid_mapping_by_theme[theme_id].append((confidence, local_id, rationale))

    for theme_id in selected_from_response:
        theme_id = str(theme_id)
        if theme_id in valid_mapping_by_theme and theme_id not in seen:
            best = sorted(valid_mapping_by_theme[theme_id], reverse=True)[0]
            ranked.append((theme_id, best[0], best[1], best[2]))
            seen.add(theme_id)
    for theme_id, values in sorted(
        valid_mapping_by_theme.items(),
        key=lambda item: max(value[0] for value in item[1]),
        reverse=True,
    ):
        if theme_id not in seen:
            best = sorted(values, reverse=True)[0]
            ranked.append((theme_id, best[0], best[1], best[2]))
            seen.add(theme_id)

    ranked = ranked[:MAX_THEMES_PER_SPEECH]
    if classification["status"] == "categorised" and not ranked:
        # A categorised speech must have at least one Theme. Use the strongest
        # embedding match as a transparent fallback rather than inventing one.
        all_matches = []
        for local_id, matches in embedding_theme_matches.items():
            for match in matches:
                all_matches.append((match["similarity"], match["id"], local_id))
        all_matches.sort(reverse=True)
        if all_matches:
            similarity, theme_id, local_id = all_matches[0]
            ranked = [(theme_id, float(similarity), local_id, "Embedding fallback: strongest local Theme match.")]
            for mapping in mapping_records:
                if mapping["local_theme_id"] == local_id:
                    mapping["canonical_theme_id"] = theme_id
                    mapping["confidence"] = float(similarity)
                    mapping["rationale"] = "Embedding fallback: strongest local Theme match."
                    break
        else:
            classification["status"] = "uncategorised"
            classification["primary_cc_id"] = None
            classification["primary_cc_relationship_type"] = None
            classification["theme_ids"] = []
            classification["classification_rejection_reasons"].append(
                "No valid canonical Theme was available."
            )
            classification["primary_cc_rationale"] += " No valid canonical Theme was available."

    if classification["status"] == "categorised":
        classification["theme_ids"] = [item[0] for item in ranked]
        classification["theme_assignments"] = [
            {
                "theme_id": item[0],
                "confidence": item[1],
                "source_local_theme_id": item[2],
                "rationale": item[3],
            }
            for item in ranked
        ]
        classification["bucket_memberships"] = [
            {
                "pair_id": _pair_id(classification["primary_cc_id"], theme_id),
                "cc_id": classification["primary_cc_id"],
                "theme_id": theme_id,
                "membership_type": "primary_default",
            }
            for theme_id in classification["theme_ids"]
        ]

    cc_mapping = {
        "mapping_type": "local_cc_to_canonical_cc",
        "speech_id": record["speech_id"],
        "filename": record["filename"],
        "local_cc_text": record["central_claim"],
        "canonical_cc_id": classification.get("primary_cc_id"),
        "confidence": classification.get("primary_cc_confidence", 0.0),
        "relationship_type": classification.get("primary_cc_relationship_type"),
        "relationship_explanation": classification.get(
            "primary_cc_relationship_explanation", ""
        ),
        "rationale": classification.get("primary_cc_rationale", ""),
        "candidate_matches": classification.get("best_cc_candidates") or cc_matches[:5],
        "classification_prompt_version": CLASSIFICATION_PROMPT_VERSION,
        "classification_schema_version": CLASSIFICATION_SCHEMA_VERSION,
    }
    return classification, [cc_mapping] + mapping_records


def _enrich_canonical_aliases_and_sources(
    canonical_ccs: List[Dict[str, Any]],
    canonical_themes: List[Dict[str, Any]],
    mappings: Sequence[Dict[str, Any]],
) -> None:
    cc_map = {item["cc_id"]: item for item in canonical_ccs}
    theme_map = {item["theme_id"]: item for item in canonical_themes}

    for mapping in mappings:
        if mapping.get("mapping_type") == "local_cc_to_canonical_cc":
            entity = cc_map.get(mapping.get("canonical_cc_id"))
            if entity:
                aliases = set(entity.get("aliases", []))
                aliases.add(mapping.get("local_cc_text", ""))
                entity["aliases"] = sorted(alias for alias in aliases if alias)
                sources = set(entity.get("source_speech_ids", []))
                sources.add(mapping.get("speech_id"))
                entity["source_speech_ids"] = sorted(value for value in sources if value)
        elif mapping.get("mapping_type") == "local_theme_to_canonical_theme":
            entity = theme_map.get(mapping.get("canonical_theme_id"))
            if entity:
                aliases = set(entity.get("aliases", []))
                aliases.add(mapping.get("local_theme_text", ""))
                entity["aliases"] = sorted(alias for alias in aliases if alias)
                sources = set(entity.get("source_speech_ids", []))
                sources.add(mapping.get("speech_id"))
                entity["source_speech_ids"] = sorted(value for value in sources if value)


def _build_cc_theme_pairs(
    classifications: Sequence[Dict[str, Any]],
    canonical_ccs: Sequence[Dict[str, Any]],
    canonical_themes: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    valid_cc_ids = {item["cc_id"] for item in canonical_ccs}
    valid_theme_ids = {item["theme_id"] for item in canonical_themes}
    pair_sources = defaultdict(set)  # type: Dict[str, Set[str]]
    pair_relationship_sources = defaultdict(lambda: defaultdict(set))

    for classification in classifications:
        if classification.get("status") != "categorised":
            continue
        speech_id = classification["speech_id"]
        cc_id = classification.get("primary_cc_id")
        if cc_id not in valid_cc_ids:
            continue
        relationship_type = _relationship_type_name(
            classification.get("primary_cc_relationship_type")
        )
        for theme_id in classification.get("theme_ids", []):
            if theme_id not in valid_theme_ids:
                continue
            pair_identifier = _pair_id(cc_id, theme_id)
            pair_sources[pair_identifier].add(speech_id)
            if relationship_type is not None:
                pair_relationship_sources[pair_identifier][relationship_type].add(speech_id)

    pairs = []
    for pair_identifier, source_ids in pair_sources.items():
        _, cc_id, theme_id = pair_identifier.split("-", 2)
        pairs.append(
            {
                "record_kind": PAIR_RECORD_KIND,
                "schema_version": SCHEMA_VERSION,
                "pair_id": pair_identifier,
                "cc_id": cc_id,
                "theme_id": theme_id,
                "source_speech_ids": sorted(source_ids),
                "relationship_type_speech_ids": {
                    relationship_type: sorted(speech_ids)
                    for relationship_type, speech_ids in sorted(
                        pair_relationship_sources[pair_identifier].items(),
                        key=lambda item: PRIMARY_CC_RELATIONSHIP_TYPES.index(item[0]),
                    )
                },
                "relationship_type_counts": {
                    relationship_type: len(speech_ids)
                    for relationship_type, speech_ids in sorted(
                        pair_relationship_sources[pair_identifier].items(),
                        key=lambda item: PRIMARY_CC_RELATIONSHIP_TYPES.index(item[0]),
                    )
                },
                "source_contribution_ids": [],
                "canonical_argument_conclusion_ids": [],
                "authoritative_anchor": _pair_anchor(cc_id, theme_id),
                "created_at": _utc_now_iso(),
                "updated_at": _utc_now_iso(),
            }
        )
    pairs.sort(key=lambda item: (_numeric_id_sort_key(item["cc_id"]), _numeric_id_sort_key(item["theme_id"])))
    return pairs


def _canonical_model_version(
    canonical_ccs: Sequence[Dict[str, Any]],
    canonical_themes: Sequence[Dict[str, Any]],
    pairs: Sequence[Dict[str, Any]],
    classifications: Sequence[Dict[str, Any]],
    mappings: Sequence[Dict[str, Any]],
) -> str:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "classification_prompt_version": CLASSIFICATION_PROMPT_VERSION,
        "classification_schema_version": CLASSIFICATION_SCHEMA_VERSION,
        "primary_cc_relationship_types": list(PRIMARY_CC_RELATIONSHIP_TYPES),
        "canonical_ccs": [
            {"cc_id": item["cc_id"], "claim": item["claim"], "fingerprint": item["semantic_fingerprint"]}
            for item in canonical_ccs
        ],
        "canonical_themes": [
            {"theme_id": item["theme_id"], "theme": item["theme"], "fingerprint": item["semantic_fingerprint"]}
            for item in canonical_themes
        ],
        "pairs": [
            {
                "pair_id": item["pair_id"],
                "cc_id": item["cc_id"],
                "theme_id": item["theme_id"],
                "relationship_type_speech_ids": item.get(
                    "relationship_type_speech_ids", {}
                ),
            }
            for item in pairs
        ],
        "classifications": [
            {
                "speech_id": item.get("speech_id"),
                "status": item.get("status"),
                "primary_cc_id": item.get("primary_cc_id"),
                "primary_cc_confidence": item.get("primary_cc_confidence"),
                "primary_cc_relationship_type": item.get(
                    "primary_cc_relationship_type"
                ),
                "primary_cc_relationship_explanation": item.get(
                    "primary_cc_relationship_explanation"
                ),
                "theme_ids": item.get("theme_ids", []),
                "theme_assignments": item.get("theme_assignments", []),
            }
            for item in classifications
        ],
        "mappings": [
            {
                "mapping_type": item.get("mapping_type"),
                "speech_id": item.get("speech_id"),
                "local_theme_id": item.get("local_theme_id"),
                "canonical_cc_id": item.get("canonical_cc_id"),
                "canonical_theme_id": item.get("canonical_theme_id"),
                "confidence": item.get("confidence"),
                "relationship_type": item.get("relationship_type"),
                "relationship_explanation": item.get(
                    "relationship_explanation"
                ),
                "rationale": item.get("rationale"),
            }
            for item in mappings
        ],
    }
    return "CM-" + _hash_json(payload)[:16].upper()


def _phase3_discovery_dependencies(
    inventory: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """Dependencies that determine only the canonical CC/Theme inventories."""
    inventory_manifest = _read_json_if_exists(INVENTORY_MANIFEST) or {}
    return {
        "inventory_manifest_hash": inventory_manifest.get("manifest_hash"),
        "inventory_record_hashes": sorted(item.get("record_hash", "") for item in inventory),
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "model": MODEL,
        "embedding_model": EMBEDDING_MODEL_NAME,
        "cc_dedup_threshold": CC_DEDUP_THRESHOLD,
        "theme_dedup_threshold": THEME_DEDUP_THRESHOLD,
    }


def _phase3_dependencies(inventory: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Full Phase 3 dependencies, including the argumentative-home classifier."""
    dependencies = _phase3_discovery_dependencies(inventory)
    dependencies.update(
        {
            "classification_prompt_version": CLASSIFICATION_PROMPT_VERSION,
            "classification_schema_version": CLASSIFICATION_SCHEMA_VERSION,
            "primary_cc_relationship_types": list(PRIMARY_CC_RELATIONSHIP_TYPES),
            "classification_confidence_min": CLASSIFICATION_CONFIDENCE_MIN,
            "theme_mapping_confidence_min": THEME_MAPPING_CONFIDENCE_MIN,
            "max_themes_per_speech": MAX_THEMES_PER_SPEECH,
            "classification_cc_candidates": CLASSIFICATION_CC_CANDIDATES,
            "classification_theme_candidates_per_local_theme": (
                CLASSIFICATION_THEME_CANDIDATES_PER_LOCAL_THEME
            ),
            "allow_secondary_cc_contributions": ALLOW_SECONDARY_CC_CONTRIBUTIONS,
        }
    )
    return dependencies


def _load_phase3_model() -> Dict[str, Any]:
    return {
        "canonical_ccs": _read_json(CANONICAL_CCS_FILE),
        "canonical_themes": _read_json(CANONICAL_THEMES_FILE),
        "mappings": _read_json(LOCAL_MAPPINGS_FILE),
        "classifications": _read_json(CLASSIFICATIONS_FILE),
        "pairs": _read_json(CC_THEME_PAIRS_FILE),
        "manifest": _read_json(CANONICAL_MANIFEST),
    }


def phase3_consolidate(
    client: OpenAI,
    inventory: Sequence[Dict[str, Any]],
    reconsolidate: bool = RECONSOLIDATE,
) -> Dict[str, Any]:
    log.info("=== PHASE 3: CONSOLIDATE ===")
    dependencies = _phase3_dependencies(inventory)
    existing_manifest = _read_json_if_exists(CANONICAL_MANIFEST)
    required_files = (
        CANONICAL_CCS_FILE,
        CANONICAL_THEMES_FILE,
        LOCAL_MAPPINGS_FILE,
        CLASSIFICATIONS_FILE,
        CC_THEME_PAIRS_FILE,
    )
    if (
        not reconsolidate
        and isinstance(existing_manifest, dict)
        and existing_manifest.get("complete")
        and existing_manifest.get("dependencies") == dependencies
        and all(path.exists() for path in required_files)
    ):
        log.info("Phase 3 dependencies unchanged; reusing canonical model.")
        return _load_phase3_model()

    discovery_dependencies = _phase3_discovery_dependencies(inventory)
    reusable_discovery_files = CANONICAL_CCS_FILE.exists() and CANONICAL_THEMES_FILE.exists()
    existing_discovery_dependencies = None
    if isinstance(existing_manifest, dict):
        existing_discovery_dependencies = existing_manifest.get("discovery_dependencies")
        if not isinstance(existing_discovery_dependencies, dict):
            # Backward-compatible extraction from a schema-2.0 manifest. This
            # permits a classification-prompt experiment to reuse the exact
            # previously discovered canon instead of confounding the result by
            # rediscovering CCs and Themes.
            old_dependencies = existing_manifest.get("dependencies", {})
            if isinstance(old_dependencies, dict):
                existing_discovery_dependencies = {
                    key: old_dependencies.get(key)
                    for key in discovery_dependencies
                }

    reuse_canonical_discovery = (
        not reconsolidate
        and reusable_discovery_files
        and isinstance(existing_manifest, dict)
        and existing_manifest.get("complete")
        and existing_discovery_dependencies == discovery_dependencies
    )

    if reuse_canonical_discovery:
        canonical_ccs = _read_json(CANONICAL_CCS_FILE)
        canonical_themes = _read_json(CANONICAL_THEMES_FILE)
        if not isinstance(canonical_ccs, list) or not isinstance(canonical_themes, list):
            raise RuntimeError("Reusable canonical discovery files have invalid shapes.")
        history_record = _read_json_if_exists(CANONICAL_HISTORY_FILE) or {}
        cc_history = history_record.get(
            "central_claim_history",
            {"reused_without_rediscovery": True},
        )
        theme_history = history_record.get(
            "theme_history",
            {"reused_without_rediscovery": True},
        )
        log.info(
            "Canonical discovery dependencies unchanged; reusing %d CCs and %d Themes, "
            "then rerunning argumentative-home classification.",
            len(canonical_ccs),
            len(canonical_themes),
        )
    else:
        old_ccs = _read_json_if_exists(CANONICAL_CCS_FILE)
        old_themes = _read_json_if_exists(CANONICAL_THEMES_FILE)
        old_ccs = old_ccs if isinstance(old_ccs, list) else []
        old_themes = old_themes if isinstance(old_themes, list) else []

        valid_speech_ids = {record["speech_id"] for record in inventory}
        local_claim_records = [
            {
                "speech_id": record["speech_id"],
                "text": record["central_claim"],
            }
            for record in inventory
        ]
        local_theme_records = []
        for record in inventory:
            for theme in record.get("themes", []):
                local_theme_records.append(
                    {
                        "speech_id": record["speech_id"],
                        "local_theme_id": theme["local_theme_id"],
                        "text": theme["theme"],
                    }
                )

        raw_cc_candidates = _discover_candidates(client, local_claim_records, "cc")
        raw_theme_candidates = _discover_candidates(client, local_theme_records, "theme")
        cc_candidates = _validate_cc_candidates(raw_cc_candidates, valid_speech_ids)
        theme_candidates = _validate_theme_candidates(raw_theme_candidates, valid_speech_ids)

        if not cc_candidates:
            raise RuntimeError("Canonical CC discovery produced no valid candidates.")
        if not theme_candidates:
            raise RuntimeError("Canonical Theme discovery produced no valid candidates.")

        merged_cc_candidates = _merge_candidate_clusters(
            cc_candidates, kind="cc", threshold=CC_DEDUP_THRESHOLD
        )
        merged_theme_candidates = _merge_candidate_clusters(
            theme_candidates, kind="theme", threshold=THEME_DEDUP_THRESHOLD
        )

        canonical_ccs, cc_history = _assign_stable_ids(
            merged_cc_candidates, old_ccs, kind="cc"
        )
        canonical_themes, theme_history = _assign_stable_ids(
            merged_theme_candidates, old_themes, kind="theme"
        )
        _map_cc_decomposition_to_theme_ids(canonical_ccs, canonical_themes)

    cc_range = _candidate_count_range(len(inventory), CC_RATIO_MIN, CC_RATIO_MAX)
    theme_range = _candidate_count_range(len(inventory), THEME_RATIO_MIN, THEME_RATIO_MAX)
    if not (cc_range[0] <= len(canonical_ccs) <= cc_range[1]):
        log.warning(
            "Canonical CC count %d is outside diagnostic target %d-%d; semantic model retained.",
            len(canonical_ccs),
            cc_range[0],
            cc_range[1],
        )
    if not (theme_range[0] <= len(canonical_themes) <= theme_range[1]):
        log.warning(
            "Canonical Theme count %d is outside diagnostic target %d-%d; semantic model retained.",
            len(canonical_themes),
            theme_range[0],
            theme_range[1],
        )

    cc_embedding_index = _build_embedding_index(canonical_ccs, "claim", "cc_id")
    theme_embedding_index = _build_embedding_index(canonical_themes, "theme", "theme_id")

    classifications = []
    mappings = []
    for index, record in enumerate(inventory, 1):
        log.info("[%d/%d] Classifying %s", index, len(inventory), record["filename"])
        classification, speech_mappings = _classify_one_speech(
            client,
            record,
            canonical_ccs,
            canonical_themes,
            cc_embedding_index,
            theme_embedding_index,
        )
        classifications.append(classification)
        mappings.extend(speech_mappings)

    _enrich_canonical_aliases_and_sources(canonical_ccs, canonical_themes, mappings)
    pairs = _build_cc_theme_pairs(classifications, canonical_ccs, canonical_themes)
    canonical_model_version = _canonical_model_version(
        canonical_ccs, canonical_themes, pairs, classifications, mappings
    )

    for entity in canonical_ccs:
        entity["canonical_model_version"] = canonical_model_version
    for entity in canonical_themes:
        entity["canonical_model_version"] = canonical_model_version
    for classification in classifications:
        classification["canonical_model_version"] = canonical_model_version
    for mapping in mappings:
        mapping["canonical_model_version"] = canonical_model_version
    for pair in pairs:
        pair["canonical_model_version"] = canonical_model_version

    _write_json(CANONICAL_CCS_FILE, canonical_ccs)
    _write_json(CANONICAL_THEMES_FILE, canonical_themes)
    _write_json(LOCAL_MAPPINGS_FILE, mappings)
    _write_json(CLASSIFICATIONS_FILE, classifications)
    _write_json(CC_THEME_PAIRS_FILE, pairs)
    _write_json(SECONDARY_CONTRIBUTIONS_FILE, [])
    _write_json(
        CANONICAL_HISTORY_FILE,
        {
            "canonical_model_version": canonical_model_version,
            "generated_at": _utc_now_iso(),
            "central_claim_history": cc_history,
            "theme_history": theme_history,
        },
    )

    uncategorised = [item for item in classifications if item.get("status") != "categorised"]
    confidences = [item.get("primary_cc_confidence", 0.0) for item in classifications]
    relationship_type_distribution = Counter(
        item.get("primary_cc_relationship_type")
        for item in classifications
        if item.get("status") == "categorised"
        and item.get("primary_cc_relationship_type")
    )
    manifest = _manifest_payload(
        "phase3",
        dependencies,
        [
            CANONICAL_CCS_FILE,
            CANONICAL_THEMES_FILE,
            LOCAL_MAPPINGS_FILE,
            CLASSIFICATIONS_FILE,
            CC_THEME_PAIRS_FILE,
            SECONDARY_CONTRIBUTIONS_FILE,
            CANONICAL_HISTORY_FILE,
        ],
        complete=True,
        extra={
            "canonical_model_version": canonical_model_version,
            "discovery_dependencies": discovery_dependencies,
            "classification_prompt_version": CLASSIFICATION_PROMPT_VERSION,
            "classification_schema_version": CLASSIFICATION_SCHEMA_VERSION,
            "primary_cc_relationship_types": list(PRIMARY_CC_RELATIONSHIP_TYPES),
            "relationship_type_distribution": dict(relationship_type_distribution),
            "reused_canonical_discovery": reuse_canonical_discovery,
            "canonical_cc_count": len(canonical_ccs),
            "canonical_theme_count": len(canonical_themes),
            "cc_theme_pair_count": len(pairs),
            "uncategorised_count": len(uncategorised),
            "classification_confidence": {
                "minimum": min(confidences) if confidences else None,
                "maximum": max(confidences) if confidences else None,
                "mean": float(np.mean(confidences)) if confidences else None,
                "median": float(np.median(confidences)) if confidences else None,
            },
            "diagnostic_count_targets": {
                "cc_range": list(cc_range),
                "theme_range": list(theme_range),
                "hard_targets": TARGET_COUNTS_ARE_HARD,
            },
            "llm_calls_total_so_far": _LLM_CALL_COUNT,
        },
    )
    _write_json(CANONICAL_MANIFEST, manifest)

    log.info(
        "Phase 3 complete: %d CCs, %d Themes, %d pairs, %d uncategorised speeches. Model %s.",
        len(canonical_ccs),
        len(canonical_themes),
        len(pairs),
        len(uncategorised),
        canonical_model_version,
    )
    return {
        "canonical_ccs": canonical_ccs,
        "canonical_themes": canonical_themes,
        "mappings": mappings,
        "classifications": classifications,
        "pairs": pairs,
        "manifest": manifest,
    }


# ═════════════════════════════════════════════════════════════════════════════
# Phase 4 — deterministic, lossless remapping and contribution construction
# ═════════════════════════════════════════════════════════════════════════════

def _phase4_dependencies_for_record(
    source_record: Dict[str, Any],
    canonical_model_version: str,
) -> Dict[str, Any]:
    return {
        "source_hash": source_record.get("source_hash"),
        "phase1_record_hash": source_record.get("record_hash"),
        "canonical_model_version": canonical_model_version,
        "schema_version": SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "classification_prompt_version": CLASSIFICATION_PROMPT_VERSION,
        "classification_schema_version": CLASSIFICATION_SCHEMA_VERSION,
        "primary_cc_relationship_types": list(PRIMARY_CC_RELATIONSHIP_TYPES),
        "mapping_configuration": {
            "classification_confidence_min": CLASSIFICATION_CONFIDENCE_MIN,
            "theme_mapping_confidence_min": THEME_MAPPING_CONFIDENCE_MIN,
            "max_themes_per_speech": MAX_THEMES_PER_SPEECH,
            "allow_secondary_cc_contributions": ALLOW_SECONDARY_CC_CONTRIBUTIONS,
        },
    }


def _render_remapped_markdown(record: Dict[str, Any]) -> str:
    mapping = record.get("canonical_mapping", {})
    lines = [
        "## Speech: {0}".format(record.get("filename", "")),
        "**Date:** {0}".format(record.get("date", "Unknown")),
        "**Speech ID:** `{0}`".format(record.get("speech_id", "")),
        "**Classification:** {0}".format(mapping.get("status", "unknown")),
    ]
    if mapping.get("primary_cc_id"):
        lines.append(
            "**Primary Canonical CC:** `{0}` (confidence {1:.3f})".format(
                mapping["primary_cc_id"],
                float(mapping.get("primary_cc_confidence", 0.0)),
            )
        )
        relationship_type = mapping.get("primary_cc_relationship_type")
        relationship_explanation = mapping.get(
            "primary_cc_relationship_explanation", ""
        )
        if relationship_type:
            lines.append(
                "**Speech-to-CC relationship:** {0}".format(
                    _relationship_type_label(relationship_type)
                )
            )
        if relationship_explanation:
            lines.append(
                "**Relationship explanation:** {0}".format(
                    relationship_explanation
                )
            )
        lines.append(
            "**Canonical Themes:** {0}".format(
                ", ".join("`{0}`".format(item) for item in mapping.get("theme_ids", []))
                or "None"
            )
        )
        lines.append(
            "**Pair memberships:** {0}".format(
                ", ".join(
                    "`{0}`".format(item.get("pair_id"))
                    for item in mapping.get("bucket_memberships", [])
                )
                or "None"
            )
        )
    else:
        lines.append("**Primary Canonical CC:** None — uncategorised")

    lines.extend(["", "### Local Central Claim", record.get("central_claim", ""), ""])
    for theme in record.get("themes", []):
        lines.append("### Local Theme: {0}".format(theme.get("theme", "")))
        lines.append("Local Theme ID: `{0}`".format(theme.get("local_theme_id", "")))
        for argument in theme.get("arguments", []):
            lines.extend(
                [
                    "",
                    "#### Local Argument: {0}".format(argument.get("conclusion", "")),
                    "Local Argument ID: `{0}`".format(argument.get("local_argument_id", "")),
                    "",
                    "**Premises:**",
                ]
            )
            for premise in argument.get("premises", []):
                lines.append("- {0}".format(premise))
            if argument.get("evidence"):
                lines.append("")
                lines.append("**Evidence & Support:**")
                for evidence in argument.get("evidence", []):
                    lines.append(
                        "- {0} {1} — {2}".format(
                            _status_icon(evidence.get("status", "")),
                            evidence.get("item", ""),
                            evidence.get("verification_basis", ""),
                        )
                    )
            if argument.get("analogies"):
                lines.append("")
                lines.append("**Analogies & Rhetorical Devices:**")
                for device in argument.get("analogies", []):
                    lines.append(
                        "- {0}: {1}".format(
                            device.get("device", ""), device.get("explanation", "")
                        )
                    )
        lines.append("")

    if record.get("unverifiable_claims"):
        lines.append("### Unverifiable Claims")
        for claim in record.get("unverifiable_claims", []):
            lines.append(
                "- SPEECH_REF: {0} | CLAIM: {1} | REASON: {2} | MEMORY: {3}".format(
                    claim.get("speech_ref", record.get("filename", "")),
                    claim.get("claim", ""),
                    claim.get("reason", ""),
                    claim.get("memory_check", "NoInternalBasis"),
                )
            )
    lines.append("")
    return "\n".join(lines)


def _contribution_id(
    speech_id: str,
    pair_identifier: str,
    local_argument_id: str,
) -> str:
    payload = "|".join((speech_id, pair_identifier, local_argument_id))
    return "CONTRIB-" + _sha256_text(payload)[:14].upper()


def phase4_remap(
    inventory: Sequence[Dict[str, Any]],
    model: Dict[str, Any],
) -> List[Dict[str, Any]]:
    log.info("=== PHASE 4: REMAP ===")
    canonical_model_version = model["manifest"].get("canonical_model_version")
    if not canonical_model_version:
        raise RuntimeError("Phase 3 manifest lacks canonical_model_version.")

    classifications_by_speech = {
        item["speech_id"]: item for item in model.get("classifications", [])
    }
    mappings_by_speech = defaultdict(list)
    for mapping in model.get("mappings", []):
        mappings_by_speech[mapping.get("speech_id")].append(mapping)
    pair_ids = {item["pair_id"] for item in model.get("pairs", [])}

    remapped_records = []
    uncategorised_records = []
    processed = 0
    skipped = 0

    for source_record in inventory:
        speech_id = source_record["speech_id"]
        output_path = PHASE4_DIR / (source_record["stem"] + ".json")
        dependencies = _phase4_dependencies_for_record(
            source_record, canonical_model_version
        )
        existing = _read_json_if_exists(output_path)
        if (
            isinstance(existing, dict)
            and existing.get("dependencies") == dependencies
            and isinstance(existing.get("record"), dict)
        ):
            remapped_records.append(existing["record"])
            skipped += 1
            log.debug("Phase 4 skip: %s", source_record["filename"])
            continue

        classification = copy.deepcopy(
            classifications_by_speech.get(
                speech_id,
                {
                    "speech_id": speech_id,
                    "filename": source_record["filename"],
                    "status": "uncategorised",
                    "classification_prompt_version": CLASSIFICATION_PROMPT_VERSION,
                    "classification_schema_version": CLASSIFICATION_SCHEMA_VERSION,
                    "primary_cc_id": None,
                    "primary_cc_confidence": 0.0,
                    "primary_cc_relationship_type": None,
                    "primary_cc_relationship_explanation": "No Phase 3 classification record exists.",
                    "primary_cc_rationale": "No Phase 3 classification record exists.",
                    "classification_rejection_reasons": [
                        "No Phase 3 classification record exists."
                    ],
                    "theme_ids": [],
                    "theme_assignments": [],
                    "bucket_memberships": [],
                    "best_cc_candidates": [],
                },
            )
        )
        speech_mappings = copy.deepcopy(mappings_by_speech.get(speech_id, []))
        theme_mapping_by_local = {
            item.get("local_theme_id"): item
            for item in speech_mappings
            if item.get("mapping_type") == "local_theme_to_canonical_theme"
        }

        remapped = copy.deepcopy(source_record)
        remapped["record_kind"] = PHASE4_RECORD_KIND
        remapped["schema_version"] = SCHEMA_VERSION
        remapped["prompt_version"] = PROMPT_VERSION
        remapped["canonical_model_version"] = canonical_model_version
        remapped["phase1_record_hash"] = source_record.get("record_hash")
        remapped["canonical_mapping"] = classification
        remapped["local_to_canonical_mappings"] = speech_mappings
        remapped["source_contributions"] = []
        remapped["unmapped_arguments"] = []
        remapped["secondary_cc_contributions"] = []

        valid_bucket_memberships = [
            membership
            for membership in classification.get("bucket_memberships", [])
            if membership.get("pair_id") in pair_ids
        ]
        remapped["canonical_mapping"]["bucket_memberships"] = valid_bucket_memberships
        allowed_pair_by_theme = {
            membership["theme_id"]: membership["pair_id"]
            for membership in valid_bucket_memberships
        }

        if classification.get("status") == "categorised":
            for local_theme in source_record.get("themes", []):
                local_theme_id = local_theme.get("local_theme_id")
                mapping = theme_mapping_by_local.get(local_theme_id, {})
                canonical_theme_id = mapping.get("canonical_theme_id")
                pair_identifier = allowed_pair_by_theme.get(canonical_theme_id)

                for local_argument in local_theme.get("arguments", []):
                    if not canonical_theme_id or not pair_identifier:
                        remapped["unmapped_arguments"].append(
                            {
                                "flag": "UNMAPPED_ARGUMENT",
                                "local_theme_id": local_theme_id,
                                "local_argument_id": local_argument.get("local_argument_id"),
                                "conclusion": local_argument.get("conclusion"),
                                "reason": "The owning local Theme did not map to a selected canonical Theme/pair.",
                            }
                        )
                        continue

                    contribution_identifier = _contribution_id(
                        speech_id,
                        pair_identifier,
                        local_argument["local_argument_id"],
                    )
                    remapped["source_contributions"].append(
                        {
                            "contribution_id": contribution_identifier,
                            "speech_id": speech_id,
                            "filename": source_record["filename"],
                            "date": source_record["date"],
                            "source_hash": source_record["source_hash"],
                            "pair_id": pair_identifier,
                            "cc_id": classification["primary_cc_id"],
                            "theme_id": canonical_theme_id,
                            "membership_type": "primary_default",
                            "primary_cc_relationship_type": classification.get(
                                "primary_cc_relationship_type"
                            ),
                            "primary_cc_relationship_explanation": classification.get(
                                "primary_cc_relationship_explanation", ""
                            ),
                            "primary_cc_confidence": classification.get(
                                "primary_cc_confidence", 0.0
                            ),
                            "classification_prompt_version": classification.get(
                                "classification_prompt_version", CLASSIFICATION_PROMPT_VERSION
                            ),
                            "classification_schema_version": classification.get(
                                "classification_schema_version", CLASSIFICATION_SCHEMA_VERSION
                            ),
                            "local_theme_id": local_theme_id,
                            "local_theme_text": local_theme.get("theme"),
                            "theme_mapping_confidence": mapping.get("confidence", 0.0),
                            "theme_mapping_rationale": mapping.get("rationale", ""),
                            "local_argument_id": local_argument.get("local_argument_id"),
                            "conclusion": local_argument.get("conclusion"),
                            "premises": copy.deepcopy(local_argument.get("premises", [])),
                            "evidence": copy.deepcopy(local_argument.get("evidence", [])),
                            "analogies": copy.deepcopy(local_argument.get("analogies", [])),
                        }
                    )
        else:
            uncategorised_records.append(
                {
                    "speech_id": speech_id,
                    "filename": source_record["filename"],
                    "reason": classification.get("primary_cc_rationale", ""),
                    "best_candidates": classification.get("best_cc_candidates", []),
                    "confidence": classification.get("primary_cc_confidence", 0.0),
                    "relationship_type": classification.get(
                        "primary_cc_relationship_type"
                    ),
                    "relationship_explanation": classification.get(
                        "primary_cc_relationship_explanation", ""
                    ),
                    "rejection_reasons": classification.get(
                        "classification_rejection_reasons", []
                    ),
                }
            )

        remapped["generated_at"] = _utc_now_iso()
        remapped["record_hash"] = _hash_json(remapped)
        wrapper = {
            "dependencies": dependencies,
            "record": remapped,
            "output_hash": remapped["record_hash"],
            "complete": True,
        }
        _write_json(output_path, wrapper)
        if WRITE_REMAPPED_MARKDOWN:
            _atomic_write_text(
                PHASE4_DIR / (source_record["stem"] + ".md"),
                _render_remapped_markdown(remapped),
            )
        remapped_records.append(remapped)
        processed += 1

    # Rebuild the uncategorised log deterministically from current records.
    uncategorised_current = []
    for record in remapped_records:
        mapping = record.get("canonical_mapping", {})
        if mapping.get("status") != "categorised":
            uncategorised_current.append(
                {
                    "speech_id": record.get("speech_id"),
                    "filename": record.get("filename"),
                    "reason": mapping.get("primary_cc_rationale", ""),
                    "best_candidates": mapping.get("best_cc_candidates", []),
                    "confidence": mapping.get("primary_cc_confidence", 0.0),
                    "relationship_type": mapping.get(
                        "primary_cc_relationship_type"
                    ),
                    "relationship_explanation": mapping.get(
                        "primary_cc_relationship_explanation", ""
                    ),
                    "rejection_reasons": mapping.get(
                        "classification_rejection_reasons", []
                    ),
                }
            )
    jsonl = "\n".join(
        json.dumps(item, ensure_ascii=False) for item in uncategorised_current
    )
    if jsonl:
        jsonl += "\n"
    _atomic_write_text(UNCATEGORISED_FILE, jsonl)

    dependencies = {
        "canonical_model_version": canonical_model_version,
        "source_record_hashes": sorted(record.get("record_hash", "") for record in inventory),
        "phase3_manifest_hash": model["manifest"].get("manifest_hash"),
        "configuration": _phase_configuration(),
    }
    output_paths = sorted(PHASE4_DIR.glob("*.json")) + [UNCATEGORISED_FILE]
    manifest = _manifest_payload(
        "phase4",
        dependencies,
        output_paths,
        complete=(len(remapped_records) == len(inventory)),
        extra={
            "canonical_model_version": canonical_model_version,
            "source_count": len(inventory),
            "remapped_count": len(remapped_records),
            "uncategorised_count": len(uncategorised_current),
            "processed": processed,
            "skipped": skipped,
            "source_contribution_count": sum(
                len(record.get("source_contributions", [])) for record in remapped_records
            ),
            "unmapped_argument_count": sum(
                len(record.get("unmapped_arguments", [])) for record in remapped_records
            ),
        },
    )
    _write_json(PHASE4_MANIFEST, manifest)
    log.info(
        "Phase 4 complete: %d remapped (%d new, %d reused), %d uncategorised.",
        len(remapped_records),
        processed,
        skipped,
        len(uncategorised_current),
    )
    return remapped_records


# ═════════════════════════════════════════════════════════════════════════════
# Phase 5 — deterministic buckets, pair synthesis, rendering, and integrity
# ═════════════════════════════════════════════════════════════════════════════

def _build_runtime_buckets(
    remapped_records: Sequence[Dict[str, Any]],
    pairs: Sequence[Dict[str, Any]],
) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    pair_map = {pair["pair_id"]: copy.deepcopy(pair) for pair in pairs}
    buckets = {}
    for pair_id, pair in pair_map.items():
        buckets[pair_id] = {
            "record_kind": "runtime_cc_theme_bucket",
            "schema_version": SCHEMA_VERSION,
            "canonical_model_version": pair.get("canonical_model_version"),
            "pair_id": pair_id,
            "cc_id": pair["cc_id"],
            "theme_id": pair["theme_id"],
            "authoritative_anchor": pair["authoritative_anchor"],
            "source_contributions": [],
        }

    for record in remapped_records:
        for contribution in record.get("source_contributions", []):
            pair_id = contribution.get("pair_id")
            if pair_id not in buckets:
                log.error(
                    "Orphan source contribution %s references missing pair %s.",
                    contribution.get("contribution_id"),
                    pair_id,
                )
                continue
            buckets[pair_id]["source_contributions"].append(copy.deepcopy(contribution))

    updated_pairs = []
    for pair_id, pair in pair_map.items():
        contributions = buckets[pair_id]["source_contributions"]
        contribution_ids = sorted(
            {item["contribution_id"] for item in contributions}
        )
        source_ids = sorted({item["speech_id"] for item in contributions})
        pair["source_contribution_ids"] = contribution_ids
        pair["source_speech_ids"] = source_ids
        pair["updated_at"] = _utc_now_iso()
        updated_pairs.append(pair)

    updated_pairs.sort(
        key=lambda item: (
            _numeric_id_sort_key(item["cc_id"]),
            _numeric_id_sort_key(item["theme_id"]),
        )
    )
    return buckets, updated_pairs


def _group_contributions_by_relationship_type(
    contributions: Sequence[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Group validated contributions using the controlled chapter-role vocabulary."""
    grouped = {relationship_type: [] for relationship_type in PRIMARY_CC_RELATIONSHIP_TYPES}
    for contribution in contributions:
        relationship_type = _relationship_type_name(
            contribution.get("primary_cc_relationship_type")
        )
        if relationship_type is None:
            raise ValueError(
                "Source contribution {0} lacks a valid speech-to-CC relationship type.".format(
                    contribution.get("contribution_id")
                )
            )
        grouped[relationship_type].append(copy.deepcopy(contribution))
    return {key: value for key, value in grouped.items() if value}


def _bucket_input_payload(
    bucket: Dict[str, Any],
    cc: Dict[str, Any],
    theme: Dict[str, Any],
    contributions: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    grouped = _group_contributions_by_relationship_type(contributions)
    return {
        "pair": {
            "pair_id": bucket["pair_id"],
            "cc_id": bucket["cc_id"],
            "canonical_central_claim": cc["claim"],
            "cc_tagline": cc.get("tagline", ""),
            "theme_id": bucket["theme_id"],
            "canonical_theme": theme["theme"],
            "authoritative_anchor": bucket["authoritative_anchor"],
        },
        "relationship_type_counts": {
            relationship_type: len(items)
            for relationship_type, items in grouped.items()
        },
        "source_contributions_by_relationship_type": grouped,
    }


class BucketSynthesisError(Exception):
    """Raised when a Phase 5 bucket cannot be synthesised into any valid
    argument after all retries, even though it has source contributions."""


def _validate_bucket_synthesis(
    raw: Dict[str, Any],
    bucket: Dict[str, Any],
) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("Bucket synthesis must be an object.")
    if raw.get("pair_id") != bucket["pair_id"]:
        raw["pair_id"] = bucket["pair_id"]

    known_contributions = {
        item["contribution_id"]: item for item in bucket["source_contributions"]
    }
    known_filenames = {item["filename"] for item in bucket["source_contributions"]}
    known_evidence = {}
    known_devices = {}
    for contribution in bucket["source_contributions"]:
        for evidence in contribution.get("evidence", []):
            known_evidence[evidence.get("evidence_id")] = (evidence, contribution)
        for device in contribution.get("analogies", []):
            known_devices[device.get("device_id")] = (device, contribution)

    raw_arguments = raw.get("arguments")
    if not isinstance(raw_arguments, list):
        raw_arguments = []
    validated_arguments = []

    for raw_argument in raw_arguments:
        if not isinstance(raw_argument, dict):
            continue
        conclusion = _normalise_whitespace(raw_argument.get("conclusion", ""))
        if not conclusion:
            continue

        contribution_ids = [
            str(value)
            for value in (raw_argument.get("source_contribution_ids") or [])
            if str(value) in known_contributions
        ]
        if not contribution_ids and len(known_contributions) == 1:
            # Unambiguous case: there is only one possible source contribution
            # in this bucket, so a missing/malformed source_contribution_ids
            # field from the LLM can be safely repaired instead of discarding
            # an otherwise-valid argument.
            (sole_contribution_id,) = known_contributions.keys()
            log.warning(
                "Repairing missing source_contribution_ids in pair %s (single-source "
                "bucket) for argument: %s",
                bucket["pair_id"],
                conclusion,
            )
            contribution_ids = [sole_contribution_id]
        # The contribution IDs are authoritative. Derive filenames from them
        # deterministically so the LLM cannot add unrelated source filenames.
        filenames = sorted(
            {known_contributions[value]["filename"] for value in contribution_ids}
        )
        if not contribution_ids or not filenames:
            log.error(
                "Dropping source-free canonical argument in pair %s: %s",
                bucket["pair_id"],
                conclusion,
            )
            continue

        evidence_items = []
        for raw_evidence in raw_argument.get("evidence", []) or []:
            if not isinstance(raw_evidence, dict):
                continue
            item = _normalise_whitespace(raw_evidence.get("item", ""))
            if not item:
                continue
            evidence_contribution_ids = [
                str(value)
                for value in (raw_evidence.get("source_contribution_ids") or [])
                if str(value) in known_contributions
            ]
            evidence_filenames = []
            if not evidence_contribution_ids:
                # Try exact/normalised item matching against input evidence.
                matching = []
                item_key = _normalise_key(item)
                for evidence, contribution in known_evidence.values():
                    if _normalise_key(evidence.get("item", "")) == item_key:
                        matching.append(contribution)
                evidence_contribution_ids = sorted(
                    {match["contribution_id"] for match in matching}
                )
                evidence_filenames = sorted({match["filename"] for match in matching})
            if evidence_contribution_ids:
                evidence_filenames = sorted(
                    {
                        known_contributions[value]["filename"]
                        for value in evidence_contribution_ids
                    }
                )
            if not evidence_contribution_ids or not evidence_filenames:
                log.error(
                    "Dropping source-free evidence in pair %s: %s",
                    bucket["pair_id"],
                    item,
                )
                continue

            source_excerpt = _normalise_whitespace(raw_evidence.get("source_excerpt", ""))
            evidence_items.append(
                {
                    "item": item,
                    "status": _status_name(raw_evidence.get("status")),
                    "verification_basis": _normalise_whitespace(
                        raw_evidence.get("verification_basis", "")
                    )
                    or "Status retained from the source-level transcript analysis.",
                    "source_contribution_ids": sorted(set(evidence_contribution_ids)),
                    "source_speech_filenames": sorted(set(evidence_filenames)),
                    "source_excerpt": source_excerpt,
                }
            )

        if not evidence_items:
            log.error(
                "Dropping canonical argument with no retained evidence in pair %s: %s",
                bucket["pair_id"],
                conclusion,
            )
            continue

        devices = []
        for raw_device in raw_argument.get("rhetorical_devices", []) or []:
            if not isinstance(raw_device, dict):
                continue
            device_text = _normalise_whitespace(raw_device.get("device", ""))
            if not device_text:
                continue
            device_contribution_ids = [
                str(value)
                for value in (raw_device.get("source_contribution_ids") or [])
                if str(value) in known_contributions
            ]
            device_filenames = []
            if not device_contribution_ids:
                matching = []
                device_key = _normalise_key(device_text)
                for device, contribution in known_devices.values():
                    if _normalise_key(device.get("device", "")) == device_key:
                        matching.append(contribution)
                device_contribution_ids = sorted(
                    {match["contribution_id"] for match in matching}
                )
                device_filenames = sorted({match["filename"] for match in matching})
            if device_contribution_ids:
                device_filenames = sorted(
                    {
                        known_contributions[value]["filename"]
                        for value in device_contribution_ids
                    }
                )
            if not device_contribution_ids or not device_filenames:
                continue
            devices.append(
                {
                    "device": device_text,
                    "explanation": _normalise_whitespace(
                        raw_device.get("explanation", "")
                    ),
                    "source_contribution_ids": sorted(set(device_contribution_ids)),
                    "source_speech_filenames": sorted(set(device_filenames)),
                }
            )

        relationship_role_groups = defaultdict(
            lambda: {
                "source_contribution_ids": set(),
                "source_speech_filenames": set(),
                "relationship_explanations": set(),
            }
        )
        for contribution_id in contribution_ids:
            contribution = known_contributions[contribution_id]
            relationship_type = _relationship_type_name(
                contribution.get("primary_cc_relationship_type")
            )
            if relationship_type is None:
                continue
            role = relationship_role_groups[relationship_type]
            role["source_contribution_ids"].add(contribution_id)
            role["source_speech_filenames"].add(contribution["filename"])
            explanation = _normalise_whitespace(
                contribution.get("primary_cc_relationship_explanation", "")
            )
            if explanation:
                role["relationship_explanations"].add(explanation)

        relationship_roles = []
        for relationship_type in PRIMARY_CC_RELATIONSHIP_TYPES:
            role = relationship_role_groups.get(relationship_type)
            if not role:
                continue
            relationship_roles.append(
                {
                    "relationship_type": relationship_type,
                    "source_contribution_ids": sorted(role["source_contribution_ids"]),
                    "source_speech_filenames": sorted(role["source_speech_filenames"]),
                    "relationship_explanations": sorted(role["relationship_explanations"]),
                }
            )

        disagreements = [
            _normalise_whitespace(value)
            for value in (raw_argument.get("disagreements_or_qualifications") or [])
            if _normalise_whitespace(value)
        ]
        for role in relationship_roles:
            relationship_type = role["relationship_type"]
            if relationship_type not in NON_AFFIRMATIVE_RELATIONSHIP_TYPES:
                continue
            filenames_for_role = role["source_speech_filenames"]
            role_label = _relationship_type_label(relationship_type)
            marker = "{0} contributions are present from {1}.".format(
                role_label, ", ".join(filenames_for_role)
            )
            if not any(
                relationship_type.replace("_", " ") in item.lower()
                or role_label.lower() in item.lower()
                for item in disagreements
            ):
                disagreements.append(marker)

        argument_id = "ARG-{0}-{1}".format(
            bucket["pair_id"], _sha256_text(_normalise_key(conclusion))[:10].upper()
        )
        validated_arguments.append(
            {
                "argument_id": argument_id,
                "pair_id": bucket["pair_id"],
                "conclusion": conclusion,
                "source_contribution_ids": sorted(set(contribution_ids)),
                "source_speech_filenames": sorted(set(filenames)),
                "premise_synthesis": _normalise_whitespace(
                    raw_argument.get("premise_synthesis", "")
                ),
                "conclusion_supported": _normalise_whitespace(
                    raw_argument.get("conclusion_supported", "")
                ),
                "relationship_roles": relationship_roles,
                "evidence": evidence_items,
                "rhetorical_devices": devices,
                "evolution_over_time": _normalise_whitespace(
                    raw_argument.get("evolution_over_time", "")
                ),
                "disagreements_or_qualifications": disagreements,
            }
        )

    # Eliminate exact duplicate argument IDs while preserving the richest record.
    by_id = {}
    for argument in validated_arguments:
        existing = by_id.get(argument["argument_id"])
        if existing is None or len(_canonical_json_text(argument)) > len(_canonical_json_text(existing)):
            by_id[argument["argument_id"]] = argument
    arguments = sorted(by_id.values(), key=lambda item: item["conclusion"].lower())
    if not arguments and bucket["source_contributions"]:
        raise ValueError(
            "Bucket {0} has source contributions but synthesis produced no valid arguments.".format(
                bucket["pair_id"]
            )
        )

    synthesis = {
        "record_kind": BUCKET_RECORD_KIND,
        "schema_version": SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "bucket_schema_version": BUCKET_SCHEMA_VERSION,
        "bucket_prompt_version": BUCKET_PROMPT_VERSION,
        "model": MODEL,
        "canonical_model_version": bucket.get("canonical_model_version"),
        "pair_id": bucket["pair_id"],
        "cc_id": bucket["cc_id"],
        "theme_id": bucket["theme_id"],
        "authoritative_anchor": bucket["authoritative_anchor"],
        "arguments": arguments,
        "source_contribution_ids": sorted(known_contributions),
        "source_speech_filenames": sorted(known_filenames),
        "generated_at": _utc_now_iso(),
    }
    synthesis["record_hash"] = _hash_json(synthesis)
    return synthesis


def _group_contributions_by_speech(
    contributions: Sequence[Dict[str, Any]],
    group_size: int,
) -> List[List[Dict[str, Any]]]:
    by_speech = defaultdict(list)
    for contribution in contributions:
        by_speech[contribution["speech_id"]].append(contribution)
    speech_ids = sorted(
        by_speech,
        key=lambda speech_id: (
            min(item.get("date", "Unknown") for item in by_speech[speech_id]),
            speech_id,
        ),
    )
    groups = []
    for start in range(0, len(speech_ids), group_size):
        group_speech_ids = speech_ids[start : start + group_size]
        group = []
        for speech_id in group_speech_ids:
            group.extend(by_speech[speech_id])
        groups.append(group)
    return groups


def _synthesise_bucket(
    client: OpenAI,
    bucket: Dict[str, Any],
    cc: Dict[str, Any],
    theme: Dict[str, Any],
) -> Dict[str, Any]:
    contributions = bucket["source_contributions"]
    dependency_payload = {
        "pair_id": bucket["pair_id"],
        "canonical_model_version": bucket.get("canonical_model_version"),
        "contributions": contributions,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "bucket_prompt_version": BUCKET_PROMPT_VERSION,
        "bucket_schema_version": BUCKET_SCHEMA_VERSION,
        "model": MODEL,
        "assembly_bucket_limit": ASSEMBLY_BUCKET_LIMIT,
        "bucket_subgroup_size": BUCKET_SUBGROUP_SIZE,
    }
    dependency_hash = _hash_json(dependency_payload)
    checkpoint_path = PHASE5_BUCKETS_DIR / (_safe_filename(bucket["pair_id"]) + ".json")
    existing = _read_json_if_exists(checkpoint_path)
    if (
        isinstance(existing, dict)
        and existing.get("dependency_hash") == dependency_hash
        and isinstance(existing.get("synthesis"), dict)
    ):
        log.debug("Reusing pair synthesis %s.", bucket["pair_id"])
        return existing["synthesis"]

    speech_count = len({item["speech_id"] for item in contributions})
    if speech_count <= ASSEMBLY_BUCKET_LIMIT:
        last_exc: Optional[Exception] = None
        synthesis = None
        for attempt in range(1, BUCKET_VALIDATION_MAX_ATTEMPTS + 1):
            raw = _llm_json(
                client,
                BUCKET_SYNTHESIS_SYSTEM,
                json.dumps(
                    _bucket_input_payload(bucket, cc, theme, contributions),
                    ensure_ascii=False,
                    indent=2,
                ),
                expected_shape="object",
                max_tokens=20_000,
            )
            try:
                synthesis = _validate_bucket_synthesis(raw, bucket)
                break
            except ValueError as exc:
                last_exc = exc
                log.warning(
                    "Bucket synthesis validation failed for %s, attempt %d/%d: %s",
                    bucket["pair_id"],
                    attempt,
                    BUCKET_VALIDATION_MAX_ATTEMPTS,
                    exc,
                )
        if synthesis is None:
            raise BucketSynthesisError(
                "Bucket {0} failed validation after {1} attempts: {2}".format(
                    bucket["pair_id"], BUCKET_VALIDATION_MAX_ATTEMPTS, last_exc
                )
            ) from last_exc
    else:
        subgroup_outputs = []
        groups = _group_contributions_by_speech(contributions, BUCKET_SUBGROUP_SIZE)
        for index, group in enumerate(groups, 1):
            subgroup_payload = _bucket_input_payload(bucket, cc, theme, group)
            subgroup_dependency_hash = _hash_json(
                {
                    "pair_id": bucket["pair_id"],
                    "group_index": index,
                    "payload": subgroup_payload,
                    "prompt_version": PROMPT_VERSION,
                    "schema_version": SCHEMA_VERSION,
                    "bucket_prompt_version": BUCKET_PROMPT_VERSION,
                    "bucket_schema_version": BUCKET_SCHEMA_VERSION,
                    "model": MODEL,
                }
            )
            subgroup_path = PHASE5_SUBGROUPS_DIR / "{0}_subgroup_{1:04d}.json".format(
                _safe_filename(bucket["pair_id"]), index
            )
            subgroup_existing = _read_json_if_exists(subgroup_path)
            # Validate against a subgroup-specific bucket so source IDs remain constrained.
            subgroup_bucket = copy.deepcopy(bucket)
            subgroup_bucket["source_contributions"] = group
            if (
                isinstance(subgroup_existing, dict)
                and subgroup_existing.get("dependency_hash") == subgroup_dependency_hash
                and isinstance(subgroup_existing.get("raw_synthesis"), dict)
            ):
                subgroup_raw = subgroup_existing["raw_synthesis"]
                subgroup_outputs.append(_validate_bucket_synthesis(subgroup_raw, subgroup_bucket))
            else:
                last_exc = None
                validated_subgroup = None
                for attempt in range(1, BUCKET_VALIDATION_MAX_ATTEMPTS + 1):
                    subgroup_raw = _llm_json(
                        client,
                        BUCKET_SYNTHESIS_SYSTEM,
                        json.dumps(subgroup_payload, ensure_ascii=False, indent=2),
                        expected_shape="object",
                        max_tokens=20_000,
                    )
                    try:
                        validated_subgroup = _validate_bucket_synthesis(subgroup_raw, subgroup_bucket)
                        break
                    except ValueError as exc:
                        last_exc = exc
                        log.warning(
                            "Subgroup synthesis validation failed for %s (group %d), "
                            "attempt %d/%d: %s",
                            bucket["pair_id"],
                            index,
                            attempt,
                            BUCKET_VALIDATION_MAX_ATTEMPTS,
                            exc,
                        )
                if validated_subgroup is None:
                    raise BucketSynthesisError(
                        "Bucket {0} subgroup {1} failed validation after {2} attempts: "
                        "{3}".format(
                            bucket["pair_id"], index, BUCKET_VALIDATION_MAX_ATTEMPTS, last_exc
                        )
                    ) from last_exc
                _write_json(
                    subgroup_path,
                    {
                        "dependency_hash": subgroup_dependency_hash,
                        "raw_synthesis": subgroup_raw,
                        "complete": True,
                    },
                )
                subgroup_outputs.append(validated_subgroup)

        reduce_payload = {
            "pair": {
                "pair_id": bucket["pair_id"],
                "cc_id": bucket["cc_id"],
                "canonical_central_claim": cc["claim"],
                "theme_id": bucket["theme_id"],
                "canonical_theme": theme["theme"],
            },
            "partial_syntheses": subgroup_outputs,
        }
        last_exc = None
        synthesis = None
        for attempt in range(1, BUCKET_VALIDATION_MAX_ATTEMPTS + 1):
            raw = _llm_json(
                client,
                BUCKET_REDUCE_SYSTEM,
                json.dumps(reduce_payload, ensure_ascii=False, indent=2),
                expected_shape="object",
                max_tokens=24_000,
            )
            try:
                synthesis = _validate_bucket_synthesis(raw, bucket)
                break
            except ValueError as exc:
                last_exc = exc
                log.warning(
                    "Reduce-step synthesis validation failed for %s, attempt %d/%d: %s",
                    bucket["pair_id"],
                    attempt,
                    BUCKET_VALIDATION_MAX_ATTEMPTS,
                    exc,
                )
        if synthesis is None:
            raise BucketSynthesisError(
                "Bucket {0} reduce step failed validation after {1} attempts: {2}".format(
                    bucket["pair_id"], BUCKET_VALIDATION_MAX_ATTEMPTS, last_exc
                )
            ) from last_exc

    _write_json(
        checkpoint_path,
        {
            "dependency_hash": dependency_hash,
            "synthesis": synthesis,
            "complete": True,
        },
    )
    return synthesis


def _markdown_escape_inline(text: str) -> str:
    return str(text or "").replace("|", "\\|").replace("\n", " ").strip()


def _source_links_text(filenames: Sequence[str]) -> str:
    return ", ".join("`{0}`".format(name) for name in sorted(set(filenames)))


def _render_argument(argument: Dict[str, Any]) -> List[str]:
    lines = [
        "### Argument: {0}".format(argument.get("conclusion", "")),
        "",
        "**Synthesis of premises across speeches:**  ",
        argument.get("premise_synthesis", "") or "No premise synthesis was produced.",
        "",
        "**Conclusion supported:**  ",
        argument.get("conclusion_supported", "") or argument.get("conclusion", ""),
        "",
        "#### Speech-to-Chapter Relationship Roles",
    ]

    relationship_roles = argument.get("relationship_roles", [])
    if relationship_roles:
        for role in relationship_roles:
            relationship_type = role.get("relationship_type", "")
            sources = _source_links_text(role.get("source_speech_filenames", []))
            line = "- **{0}:** {1}".format(
                _relationship_type_label(relationship_type),
                sources or "No source filename retained",
            )
            explanations = role.get("relationship_explanations", [])
            if explanations:
                line += "  \n  *Why placed here:* {0}".format("; ".join(explanations))
            lines.append(line)
    else:
        lines.append("- No valid speech-to-chapter relationship role was retained.")

    lines.extend(["", "#### Evidence & Support"])

    evidence_items = argument.get("evidence", [])
    if evidence_items:
        for evidence in evidence_items:
            status = _status_name(evidence.get("status"))
            sources = _source_links_text(evidence.get("source_speech_filenames", []))
            basis = evidence.get("verification_basis", "")
            line = "- {0} **{1}** — {2}".format(
                _status_icon(status),
                status,
                evidence.get("item", ""),
            )
            if basis:
                line += "  \n  *Basis:* {0}".format(basis)
            if sources:
                line += "  \n  *Sources:* {0}".format(sources)
            excerpt = _normalise_whitespace(evidence.get("source_excerpt", ""))
            if excerpt:
                if len(excerpt) > MAX_RENDERED_EXCERPT_CHARS:
                    excerpt = excerpt[: MAX_RENDERED_EXCERPT_CHARS - 1] + "…"
                line += "  \n  *Excerpt:* “{0}”".format(excerpt)
            lines.append(line)
    else:
        lines.append("- No separate evidence item was retained for this argument.")

    lines.extend(["", "#### Notable Analogies & Rhetorical Devices"])
    devices = argument.get("rhetorical_devices", [])
    if devices:
        for device in devices:
            sources = _source_links_text(device.get("source_speech_filenames", []))
            explanation = device.get("explanation", "")
            line = "- **{0}**".format(device.get("device", ""))
            if explanation:
                line += " — {0}".format(explanation)
            if sources:
                line += " (Sources: {0})".format(sources)
            lines.append(line)
    else:
        lines.append("- None identified in the mapped source contributions.")

    lines.extend(
        [
            "",
            "#### Evolution Over Time",
            argument.get("evolution_over_time", "")
            or "The available source contributions do not support a reliable temporal comparison.",
        ]
    )

    disagreements = argument.get("disagreements_or_qualifications", [])
    if disagreements:
        lines.extend(["", "#### Disagreements and Qualifications"])
        for item in disagreements:
            lines.append("- {0}".format(item))

    lines.extend(
        [
            "",
            "#### Provenance",
            "- Canonical argument ID: `{0}`".format(argument.get("argument_id", "")),
            "- Source contributions: {0}".format(
                ", ".join(
                    "`{0}`".format(value)
                    for value in argument.get("source_contribution_ids", [])
                )
            ),
            "- Source speeches: {0}".format(
                _source_links_text(argument.get("source_speech_filenames", []))
            ),
            "",
        ]
    )
    return lines


def _theme_to_pairs(pairs: Sequence[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    result = defaultdict(list)
    for pair in pairs:
        result[pair["theme_id"]].append(pair)
    for theme_id in result:
        result[theme_id].sort(key=lambda item: _numeric_id_sort_key(item["cc_id"]))
    return result


def _cc_to_pairs(pairs: Sequence[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    result = defaultdict(list)
    for pair in pairs:
        result[pair["cc_id"]].append(pair)
    for cc_id in result:
        result[cc_id].sort(key=lambda item: _numeric_id_sort_key(item["theme_id"]))
    return result


def _render_shared_theme_cross_index(
    pairs: Sequence[Dict[str, Any]],
    canonical_ccs: Sequence[Dict[str, Any]],
    canonical_themes: Sequence[Dict[str, Any]],
) -> Tuple[List[str], Set[str]]:
    cc_map = {item["cc_id"]: item for item in canonical_ccs}
    theme_map = {item["theme_id"]: item for item in canonical_themes}
    theme_pairs = _theme_to_pairs(pairs)
    lines = ["# Theme Cross-Index", "", "*Themes shared across multiple Canonical Central Claims.*", ""]
    referenced_anchors = set()

    shared_ids = [theme_id for theme_id, items in theme_pairs.items() if len(items) > 1]
    shared_ids.sort(key=lambda theme_id: theme_map.get(theme_id, {}).get("theme", theme_id).lower())
    if not shared_ids:
        lines.append("*No shared Themes were detected in the current canonical model.*")
        return lines, referenced_anchors

    for theme_id in shared_ids:
        theme = theme_map.get(theme_id, {"theme": theme_id})
        lines.append("## {0} (`{1}`)".format(theme["theme"], theme_id))
        for pair in theme_pairs[theme_id]:
            cc = cc_map.get(pair["cc_id"], {"claim": pair["cc_id"]})
            anchor = pair["authoritative_anchor"]
            referenced_anchors.add(anchor)
            lines.append(
                "- [{0}: {1}](#{2})".format(pair["cc_id"], cc["claim"], anchor)
            )
        lines.append("")
    return lines, referenced_anchors


def _render_compendium(
    canonical_ccs: Sequence[Dict[str, Any]],
    canonical_themes: Sequence[Dict[str, Any]],
    pairs: Sequence[Dict[str, Any]],
    syntheses_by_pair: Dict[str, Dict[str, Any]],
    remapped_records: Sequence[Dict[str, Any]],
    canonical_model_version: str,
) -> Tuple[str, Set[str], Set[str]]:
    cc_map = {item["cc_id"]: item for item in canonical_ccs}
    theme_map = {item["theme_id"]: item for item in canonical_themes}
    cc_pairs = _cc_to_pairs(pairs)
    theme_pairs = _theme_to_pairs(pairs)
    categorised_records = [
        record
        for record in remapped_records
        if record.get("canonical_mapping", {}).get("status") == "categorised"
    ]
    dates = sorted(
        record["date"]
        for record in categorised_records
        if record.get("date") and record.get("date") != "Unknown"
    )

    lines = [
        "# Financial Speech Compendium",
        "",
        "- **Canonical model version:** `{0}`".format(canonical_model_version),
        "- **Source transcripts:** {0}".format(len(remapped_records)),
        "- **Confidently categorised transcripts:** {0}".format(len(categorised_records)),
        "- **Canonical Central Claims:** {0}".format(len(canonical_ccs)),
        "- **Canonical Themes:** {0}".format(len(canonical_themes)),
        "- **Canonical CC × Theme pairs:** {0}".format(len(pairs)),
        "- **Corpus date range:** {0}".format(
            "{0} to {1}".format(dates[0], dates[-1]) if dates else "Unknown"
        ),
        "- **Generated:** {0}".format(_utc_now_iso()),
        "",
        "> Evidence statuses in this document are transcript-analysis workflow labels. They are not external fact-checking verdicts.",
        "",
    ]

    anchors = set()
    rendered_pair_ids = set()
    for cc_id in sorted(cc_map, key=_numeric_id_sort_key):
        pair_list = cc_pairs.get(cc_id, [])
        if not pair_list:
            continue
        cc = cc_map[cc_id]
        chapter_anchor = _chapter_anchor(cc_id)
        anchors.add(chapter_anchor)
        lines.extend(
            [
                '<a id="{0}"></a>'.format(chapter_anchor),
                "# Central Claim: {0}".format(cc["claim"]),
                "",
                "_{0}_".format(cc.get("tagline", "")),
                "",
                "**Canonical CC ID:** `{0}`".format(cc_id),
                "",
            ]
        )

        for pair in pair_list:
            pair_id = pair["pair_id"]
            synthesis = syntheses_by_pair.get(pair_id)
            if not synthesis:
                log.error("No synthesis exists for pair %s; section omitted.", pair_id)
                continue
            theme = theme_map[pair["theme_id"]]
            anchor = pair["authoritative_anchor"]
            if anchor in anchors:
                raise ValueError("Duplicate compendium anchor: {0}".format(anchor))
            anchors.add(anchor)
            rendered_pair_ids.add(pair_id)

            other_pairs = [
                other
                for other in theme_pairs.get(pair["theme_id"], [])
                if other["pair_id"] != pair_id
            ]
            cross_note = "None."
            if other_pairs:
                cross_note = "; ".join(
                    "[{0}: {1}](#{2})".format(
                        other["cc_id"],
                        cc_map[other["cc_id"]]["claim"],
                        other["authoritative_anchor"],
                    )
                    for other in other_pairs
                )

            lines.extend(
                [
                    '<a id="{0}"></a>'.format(anchor),
                    "## Theme: {0}".format(theme["theme"]),
                    "",
                    "**Canonical Theme ID:** `{0}`  ".format(pair["theme_id"]),
                    "**Canonical pair ID:** `{0}`  ".format(pair_id),
                    "**This Theme also appears under:** {0}".format(cross_note),
                    "",
                ]
            )
            for argument in synthesis.get("arguments", []):
                lines.extend(_render_argument(argument))

    cross_index_lines, cross_index_anchors = _render_shared_theme_cross_index(
        pairs, canonical_ccs, canonical_themes
    )
    lines.extend(cross_index_lines)
    return "\n".join(lines).rstrip() + "\n", anchors, rendered_pair_ids


def _render_theme_index(
    canonical_ccs: Sequence[Dict[str, Any]],
    canonical_themes: Sequence[Dict[str, Any]],
    pairs: Sequence[Dict[str, Any]],
    syntheses_by_pair: Dict[str, Dict[str, Any]],
    canonical_model_version: str,
) -> Tuple[str, Set[str], Set[str]]:
    cc_map = {item["cc_id"]: item for item in canonical_ccs}
    theme_pairs = _theme_to_pairs(pairs)
    referenced_anchors = set()
    represented_pairs = set()

    lines = [
        "# Complete Theme Index",
        "",
        "- **Canonical model version:** `{0}`".format(canonical_model_version),
        "- **Canonical Themes:** {0}".format(len(canonical_themes)),
        "- **Canonical CC × Theme pairs:** {0}".format(len(pairs)),
        "",
        "This is a navigation view. Full synthesis, evidence, rhetoric, and temporal analysis remain authoritative in `compendium.md`.",
        "",
    ]

    for theme in sorted(canonical_themes, key=lambda item: item["theme"].lower()):
        theme_id = theme["theme_id"]
        pair_list = theme_pairs.get(theme_id, [])
        lines.extend(
            [
                "## {0}".format(theme["theme"]),
                "",
                "**Canonical Theme ID:** `{0}`  ".format(theme_id),
                "**Parent CC count:** {0}".format(len(pair_list)),
                "",
            ]
        )
        if not pair_list:
            lines.append("*No observed Canonical CC × Theme pair currently uses this Theme.*")
            lines.append("")
            continue

        for pair in pair_list:
            represented_pairs.add(pair["pair_id"])
            referenced_anchors.add(pair["authoritative_anchor"])
            cc = cc_map[pair["cc_id"]]
            lines.extend(
                [
                    "### [{0}: {1}](compendium.md#{2})".format(
                        pair["cc_id"], cc["claim"], pair["authoritative_anchor"]
                    ),
                    "",
                    "- Pair ID: `{0}`".format(pair["pair_id"]),
                    "- Authoritative section: [`compendium.md#{0}`](compendium.md#{0})".format(
                        pair["authoritative_anchor"]
                    ),
                    "- Canonical argument conclusions:",
                ]
            )
            synthesis = syntheses_by_pair.get(pair["pair_id"], {})
            arguments = synthesis.get("arguments", [])
            if arguments:
                for argument in arguments:
                    lines.append(
                        "  - `{0}` — {1}".format(
                            argument.get("argument_id", ""),
                            argument.get("conclusion", ""),
                        )
                    )
            else:
                lines.append("  - No canonical argument synthesis is available.")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n", referenced_anchors, represented_pairs


def _collect_unverifiable_records(
    remapped_records: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    collected = []
    for record in remapped_records:
        for claim in record.get("unverifiable_claims", []):
            collected.append(
                {
                    "record_type": "explicit_unverifiable_claim",
                    "speech_id": record.get("speech_id"),
                    "speech_ref": claim.get("speech_ref", record.get("filename")),
                    "claim": claim.get("claim", ""),
                    "reason": claim.get("reason", ""),
                    "memory_check": claim.get("memory_check", "NoInternalBasis"),
                    "memory_note": claim.get("memory_note", ""),
                    "source_excerpt": claim.get("source_excerpt", ""),
                    "source_match": claim.get("source_match", False),
                    "source_location": claim.get("source_location"),
                }
            )
        for theme in record.get("themes", []):
            for argument in theme.get("arguments", []):
                for evidence in argument.get("evidence", []):
                    if _status_name(evidence.get("status")) != "Unverifiable":
                        continue
                    collected.append(
                        {
                            "record_type": "unverifiable_evidence_item",
                            "speech_id": record.get("speech_id"),
                            "speech_ref": record.get("filename"),
                            "claim": evidence.get("item", ""),
                            "reason": evidence.get("verification_basis", ""),
                            "memory_check": "NoInternalBasis",
                            "memory_note": "Evidence workflow status; no separate MEMORY assessment was requested for this item.",
                            "source_excerpt": evidence.get("source_excerpt", ""),
                            "source_match": evidence.get("source_match", False),
                            "source_location": evidence.get("source_location"),
                        }
                    )

    # Exact deduplication only within the same speech reference and claim text.
    by_key = {}
    for item in collected:
        key = (item.get("speech_ref", ""), item.get("claim", ""))
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = item
        elif existing.get("record_type") != "explicit_unverifiable_claim" and item.get("record_type") == "explicit_unverifiable_claim":
            by_key[key] = item
    records = list(by_key.values())
    records.sort(key=lambda item: (item.get("speech_ref", ""), item.get("claim", "")))
    return records


def _render_unverifiable_claims(records: Sequence[Dict[str, Any]]) -> str:
    lines = [
        "# Master Unverifiable Claims List",
        "",
        "**Total unique speech-reference/claim records:** {0}".format(len(records)),
        "",
        "> These records were identified without web search. `MEMORY` is advisory model metadata, not a verification verdict, and no record is excluded because MEMORY is `Corroborated`.",
        "",
    ]
    for index, record in enumerate(records, 1):
        lines.extend(
            [
                "## {0}. {1}".format(index, record.get("speech_ref", "Unknown speech")),
                "",
                "- **TYPE:** {0}".format(record.get("record_type", "")),
                "- **SPEECH_REF:** `{0}`".format(record.get("speech_ref", "")),
                "- **CLAIM:** {0}".format(record.get("claim", "")),
                "- **REASON:** {0}".format(record.get("reason", "")),
                "- **MEMORY:** {0}".format(record.get("memory_check", "NoInternalBasis")),
            ]
        )
        if record.get("memory_note"):
            lines.append("- **MEMORY NOTE:** {0}".format(record["memory_note"]))
        if record.get("source_excerpt"):
            excerpt = _normalise_whitespace(record["source_excerpt"])
            lines.append("- **SOURCE EXCERPT:** “{0}”".format(excerpt))
        lines.append("- **SOURCE MATCH:** {0}".format(bool(record.get("source_match"))))
        if record.get("source_location"):
            lines.append(
                "- **SOURCE LOCATION:** `{0}`".format(
                    json.dumps(record["source_location"], ensure_ascii=False)
                )
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _integrity_checks(
    canonical_ccs: Sequence[Dict[str, Any]],
    canonical_themes: Sequence[Dict[str, Any]],
    classifications: Sequence[Dict[str, Any]],
    pairs: Sequence[Dict[str, Any]],
    syntheses_by_pair: Dict[str, Dict[str, Any]],
    compendium_anchors: Set[str],
    rendered_pair_ids: Set[str],
    theme_index_anchors: Set[str],
    theme_index_pair_ids: Set[str],
    unverifiable_records: Sequence[Dict[str, Any]],
    remapped_records: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    errors = []
    warnings = []
    valid_cc_ids = {item["cc_id"] for item in canonical_ccs}
    valid_theme_ids = {item["theme_id"] for item in canonical_themes}
    pair_ids = [item["pair_id"] for item in pairs]
    pair_id_set = set(pair_ids)

    if len(pair_ids) != len(pair_id_set):
        errors.append("Duplicate pair IDs exist.")
    pair_keys = [(item["cc_id"], item["theme_id"]) for item in pairs]
    if len(pair_keys) != len(set(pair_keys)):
        errors.append("Duplicate CC × Theme relationships exist.")

    for classification in classifications:
        if classification.get("status") == "categorised":
            if classification.get("primary_cc_id") not in valid_cc_ids:
                errors.append(
                    "Classification {0} references invalid CC {1}.".format(
                        classification.get("speech_id"), classification.get("primary_cc_id")
                    )
                )
            relationship_type = _relationship_type_name(
                classification.get("primary_cc_relationship_type")
            )
            if relationship_type is None:
                errors.append(
                    "Classification {0} lacks a valid argumentative relationship type.".format(
                        classification.get("speech_id")
                    )
                )
            if not _normalise_whitespace(
                classification.get("primary_cc_relationship_explanation", "")
            ):
                errors.append(
                    "Classification {0} lacks an argumentative relationship explanation.".format(
                        classification.get("speech_id")
                    )
                )
            for theme_id in classification.get("theme_ids", []):
                if theme_id not in valid_theme_ids:
                    errors.append(
                        "Classification {0} references invalid Theme {1}.".format(
                            classification.get("speech_id"), theme_id
                        )
                    )
            for membership in classification.get("bucket_memberships", []):
                if membership.get("pair_id") not in pair_id_set:
                    errors.append(
                        "Classification {0} references invalid pair {1}.".format(
                            classification.get("speech_id"), membership.get("pair_id")
                        )
                    )

    anchors = []
    for pair in pairs:
        if pair["cc_id"] not in valid_cc_ids or pair["theme_id"] not in valid_theme_ids:
            errors.append("Pair {0} references an invalid canonical entity.".format(pair["pair_id"]))
        anchor = pair.get("authoritative_anchor")
        anchors.append(anchor)
        if anchor not in compendium_anchors:
            errors.append("Pair {0} anchor is absent from compendium.md.".format(pair["pair_id"]))
        if pair["pair_id"] not in syntheses_by_pair:
            errors.append("Pair {0} has no synthesis.".format(pair["pair_id"]))
        if pair["pair_id"] not in rendered_pair_ids:
            errors.append("Pair {0} has no rendered authoritative section.".format(pair["pair_id"]))
    if len(anchors) != len(set(anchors)):
        errors.append("Authoritative pair anchors are not unique.")

    if theme_index_anchors != set(anchors):
        missing = set(anchors) - theme_index_anchors
        extra = theme_index_anchors - set(anchors)
        if missing:
            errors.append("Theme index misses anchors: {0}".format(sorted(missing)))
        if extra:
            errors.append("Theme index references unknown anchors: {0}".format(sorted(extra)))
    if theme_index_pair_ids != pair_id_set:
        errors.append("theme_index.md does not represent every CC × Theme pair exactly once.")

    source_filenames = {record.get("filename") for record in remapped_records}
    classification_by_speech = {
        item.get("speech_id"): item for item in classifications
    }
    source_contribution_map = {}
    for record in remapped_records:
        for contribution in record.get("source_contributions", []):
            contribution_id = contribution.get("contribution_id")
            if contribution_id:
                source_contribution_map[contribution_id] = contribution
            relationship_type = _relationship_type_name(
                contribution.get("primary_cc_relationship_type")
            )
            if relationship_type is None:
                errors.append(
                    "Source contribution {0} lacks a valid argumentative relationship type.".format(
                        contribution_id
                    )
                )
            expected = classification_by_speech.get(contribution.get("speech_id"), {})
            if relationship_type != expected.get("primary_cc_relationship_type"):
                errors.append(
                    "Source contribution {0} does not preserve its speech classification relationship type.".format(
                        contribution_id
                    )
                )

    for pair_id, synthesis in syntheses_by_pair.items():
        for argument in synthesis.get("arguments", []):
            if not argument.get("source_contribution_ids") or not argument.get("source_speech_filenames"):
                errors.append("Argument {0} lacks provenance.".format(argument.get("argument_id")))
            for filename in argument.get("source_speech_filenames", []):
                if filename not in source_filenames:
                    errors.append(
                        "Argument {0} references unknown speech {1}.".format(
                            argument.get("argument_id"), filename
                        )
                    )
            represented_role_contributions = set()
            for role in argument.get("relationship_roles", []):
                relationship_type = _relationship_type_name(
                    role.get("relationship_type")
                )
                if relationship_type is None:
                    errors.append(
                        "Argument {0} contains an invalid relationship role.".format(
                            argument.get("argument_id")
                        )
                    )
                for contribution_id in role.get("source_contribution_ids", []):
                    represented_role_contributions.add(contribution_id)
                    contribution = source_contribution_map.get(contribution_id)
                    if contribution is None:
                        errors.append(
                            "Argument {0} relationship role references unknown contribution {1}.".format(
                                argument.get("argument_id"), contribution_id
                            )
                        )
                    elif relationship_type != contribution.get(
                        "primary_cc_relationship_type"
                    ):
                        errors.append(
                            "Argument {0} misstates the relationship role of contribution {1}.".format(
                                argument.get("argument_id"), contribution_id
                            )
                        )
            if represented_role_contributions != set(
                argument.get("source_contribution_ids", [])
            ):
                errors.append(
                    "Argument {0} relationship-role summary does not cover exactly its source contributions.".format(
                        argument.get("argument_id")
                    )
                )
            for evidence in argument.get("evidence", []):
                if not evidence.get("source_contribution_ids") or not evidence.get("source_speech_filenames"):
                    errors.append(
                        "Evidence in argument {0} lacks provenance.".format(argument.get("argument_id"))
                    )

    explicit_phase1_keys = set()
    for record in remapped_records:
        for claim in record.get("unverifiable_claims", []):
            explicit_phase1_keys.add(
                (claim.get("speech_ref", record.get("filename")), claim.get("claim", ""))
            )
    published_keys = {
        (item.get("speech_ref", ""), item.get("claim", ""))
        for item in unverifiable_records
    }
    missing_unverifiable = explicit_phase1_keys - published_keys
    if missing_unverifiable:
        errors.append(
            "Some explicit Phase 1 unverifiable claims are missing: {0}".format(
                sorted(missing_unverifiable)
            )
        )

    uncategorised_count = sum(
        1
        for item in classifications
        if item.get("status") != "categorised"
    )
    if uncategorised_count:
        warnings.append("{0} speeches remain uncategorised.".format(uncategorised_count))

    checks = {
        "classification_referential_integrity": not any("Classification" in error for error in errors),
        "pair_referential_integrity": not any("Pair" in error or "pair" in error for error in errors),
        "anchor_integrity": not any("anchor" in error.lower() for error in errors),
        "theme_index_completeness": theme_index_pair_ids == pair_id_set,
        "provenance_coverage": not any("provenance" in error.lower() for error in errors),
        "relationship_type_integrity": not any(
            "relationship" in error.lower() for error in errors
        ),
        "unverifiable_completeness": not missing_unverifiable,
    }
    referential_items = 7
    referential_passes = sum(1 for value in checks.values() if value)
    report = {
        "schema_version": SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "generated_at": _utc_now_iso(),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
        "referential_integrity_rate": referential_passes / float(referential_items),
        "counts": {
            "canonical_ccs": len(canonical_ccs),
            "canonical_themes": len(canonical_themes),
            "pairs": len(pairs),
            "synthesized_pairs": len(syntheses_by_pair),
            "compendium_anchors": len(compendium_anchors),
            "theme_index_pairs": len(theme_index_pair_ids),
            "unverifiable_records": len(unverifiable_records),
            "uncategorised_speeches": uncategorised_count,
        },
    }
    return report


def phase5_assemble(
    client: OpenAI,
    remapped_records: Sequence[Dict[str, Any]],
    model: Dict[str, Any],
) -> Dict[str, Any]:
    log.info("=== PHASE 5: ASSEMBLE ===")
    canonical_ccs = model["canonical_ccs"]
    canonical_themes = model["canonical_themes"]
    canonical_model_version = model["manifest"].get("canonical_model_version")
    cc_map = {item["cc_id"]: item for item in canonical_ccs}
    theme_map = {item["theme_id"]: item for item in canonical_themes}

    buckets, pairs = _build_runtime_buckets(remapped_records, model["pairs"])
    nonempty_pairs = []
    for pair in pairs:
        if buckets[pair["pair_id"]]["source_contributions"]:
            nonempty_pairs.append(pair)
        else:
            log.warning("Pair %s has no source contributions and will not be rendered.", pair["pair_id"])
    pairs = nonempty_pairs
    valid_pair_ids = {pair["pair_id"] for pair in pairs}
    buckets = {pair_id: bucket for pair_id, bucket in buckets.items() if pair_id in valid_pair_ids}

    if CLEAN_PHASE5_STALE_BUCKETS:
        for path in PHASE5_BUCKETS_DIR.glob("*.json"):
            checkpoint = _read_json_if_exists(path)
            synthesis = checkpoint.get("synthesis", {}) if isinstance(checkpoint, dict) else {}
            if synthesis.get("pair_id") not in valid_pair_ids:
                path.unlink(missing_ok=True)
        for path in PHASE5_SUBGROUPS_DIR.glob("*.json"):
            if not any(_safe_filename(pair_id) in path.name for pair_id in valid_pair_ids):
                path.unlink(missing_ok=True)

    syntheses_by_pair = {}
    successful_pairs = []
    failed_pair_ids = []
    for index, pair in enumerate(pairs, 1):
        pair_id = pair["pair_id"]
        bucket = buckets[pair_id]
        speech_count = len({item["speech_id"] for item in bucket["source_contributions"]})
        log.info(
            "[%d/%d] Synthesising %s from %d speeches and %d contributions.",
            index,
            len(pairs),
            pair_id,
            speech_count,
            len(bucket["source_contributions"]),
        )
        try:
            synthesis = _synthesise_bucket(
                client,
                bucket,
                cc_map[pair["cc_id"]],
                theme_map[pair["theme_id"]],
            )
        except Exception as exc:
            failed_pair_ids.append(pair_id)
            log.error("Phase 5 failed for bucket %s: %s", pair_id, exc)
            log.debug(traceback.format_exc())
            continue
        syntheses_by_pair[pair_id] = synthesis
        pair["canonical_argument_conclusion_ids"] = [
            argument["argument_id"] for argument in synthesis.get("arguments", [])
        ]
        pair["updated_at"] = _utc_now_iso()
        successful_pairs.append(pair)

    pairs = successful_pairs
    if failed_pair_ids:
        log.warning(
            "Phase 5 skipped %d bucket(s) that failed synthesis after retries: %s",
            len(failed_pair_ids),
            ", ".join(failed_pair_ids),
        )

    # The authoritative pair table is updated with contribution and argument IDs.
    # Only successfully synthesised pairs are written here; failed buckets are
    # left out of this run's table rather than corrupting it with stale/missing data.
    _write_json(CC_THEME_PAIRS_FILE, pairs)

    compendium_text, compendium_anchors, rendered_pair_ids = _render_compendium(
        canonical_ccs,
        canonical_themes,
        pairs,
        syntheses_by_pair,
        remapped_records,
        canonical_model_version,
    )
    _atomic_write_text(COMPENDIUM_FILE, compendium_text)

    if WRITE_THEME_INDEX:
        theme_index_text, theme_index_anchors, theme_index_pair_ids = _render_theme_index(
            canonical_ccs,
            canonical_themes,
            pairs,
            syntheses_by_pair,
            canonical_model_version,
        )
        _atomic_write_text(THEME_INDEX_FILE, theme_index_text)
    else:
        theme_index_anchors = {pair["authoritative_anchor"] for pair in pairs}
        theme_index_pair_ids = {pair["pair_id"] for pair in pairs}
        _atomic_write_text(
            THEME_INDEX_FILE,
            "# Complete Theme Index\n\nTheme-index generation is disabled by configuration.\n",
        )

    unverifiable_records = _collect_unverifiable_records(remapped_records)
    _atomic_write_text(
        UNVERIFIABLE_FILE,
        _render_unverifiable_claims(unverifiable_records),
    )

    integrity_report = _integrity_checks(
        canonical_ccs,
        canonical_themes,
        model["classifications"],
        pairs,
        syntheses_by_pair,
        compendium_anchors,
        rendered_pair_ids,
        theme_index_anchors,
        theme_index_pair_ids,
        unverifiable_records,
        remapped_records,
    )
    _write_json(INTEGRITY_REPORT_FILE, integrity_report)

    dependencies = {
        "canonical_model_version": canonical_model_version,
        "phase4_manifest_hash": (_read_json_if_exists(PHASE4_MANIFEST) or {}).get("manifest_hash"),
        "remapped_record_hashes": sorted(record.get("record_hash", "") for record in remapped_records),
        "pair_table_hash": _hash_json(pairs),
        "bucket_synthesis_hashes": {
            pair_id: synthesis.get("record_hash")
            for pair_id, synthesis in sorted(syntheses_by_pair.items())
        },
        "configuration": _phase_configuration(),
    }
    manifest = _manifest_payload(
        "phase5",
        dependencies,
        [
            COMPENDIUM_FILE,
            THEME_INDEX_FILE,
            UNVERIFIABLE_FILE,
            INTEGRITY_REPORT_FILE,
            CC_THEME_PAIRS_FILE,
        ],
        complete=(integrity_report["status"] == "PASS"),
        extra={
            "canonical_model_version": canonical_model_version,
            "pair_count": len(pairs),
            "canonical_argument_count": sum(
                len(synthesis.get("arguments", []))
                for synthesis in syntheses_by_pair.values()
            ),
            "unverifiable_record_count": len(unverifiable_records),
            "integrity_status": integrity_report["status"],
            "llm_calls_total": _LLM_CALL_COUNT,
            "failed_bucket_count": len(failed_pair_ids),
            "failed_bucket_ids": failed_pair_ids,
        },
    )
    _write_json(PHASE5_MANIFEST, manifest)

    if integrity_report["status"] != "PASS":
        log.error(
            "Phase 5 integrity checks failed with %d error(s). See %s.",
            len(integrity_report["errors"]),
            INTEGRITY_REPORT_FILE,
        )
    else:
        log.info("Phase 5 integrity checks passed.")
    log.info(
        "Phase 5 complete: %s, %s, and %s written.",
        COMPENDIUM_FILE,
        THEME_INDEX_FILE,
        UNVERIFIABLE_FILE,
    )
    return {
        "pairs": pairs,
        "syntheses": syntheses_by_pair,
        "integrity_report": integrity_report,
        "manifest": manifest,
        "failed_bucket_ids": failed_pair_ids,
    }


# ═════════════════════════════════════════════════════════════════════════════
# Command-line entry point
# ═════════════════════════════════════════════════════════════════════════════

def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a canonical financial-speech compendium from transcripts."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable DEBUG logging.",
    )
    parser.add_argument(
        "--reconsolidate",
        action="store_true",
        help="Force Phase 3 canonical rediscovery and reclassification.",
    )
    parser.add_argument(
        "--clear-phase5-cache",
        action="store_true",
        help="Delete cached pair/subgroup syntheses before Phase 5.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    _setup_dirs()
    args = _parse_args(argv)
    _configure_logging(debug=args.debug)

    try:
        if args.clear_phase5_cache:
            if PHASE5_BUCKETS_DIR.exists():
                shutil.rmtree(PHASE5_BUCKETS_DIR)
            if PHASE5_SUBGROUPS_DIR.exists():
                shutil.rmtree(PHASE5_SUBGROUPS_DIR)
            PHASE5_BUCKETS_DIR.mkdir(parents=True, exist_ok=True)
            PHASE5_SUBGROUPS_DIR.mkdir(parents=True, exist_ok=True)
            log.info("Cleared Phase 5 synthesis cache.")

        transcripts = sorted(TRANSCRIPTS_DIR.glob("*.md"))
        if not transcripts:
            log.error(
                "No .md transcripts found in '%s'. Place source files there and rerun.",
                TRANSCRIPTS_DIR,
            )
            return 2

        log.info("Found %d transcripts in %s.", len(transcripts), TRANSCRIPTS_DIR)
        client = _load_env()

        phase1_records = phase1_summarise(client, transcripts)
        if not phase1_records:
            raise RuntimeError("Phase 1 produced no valid speech records.")

        inventory = phase2_inventory(phase1_records)
        model = phase3_consolidate(
            client,
            inventory,
            reconsolidate=(RECONSOLIDATE or args.reconsolidate),
        )
        remapped_records = phase4_remap(inventory, model)
        result = phase5_assemble(client, remapped_records, model)

        if result["integrity_report"]["status"] != "PASS":
            return 3
        log.info("=== PIPELINE COMPLETE — %d LLM calls in this run ===", _LLM_CALL_COUNT)
        return 0
    except KeyboardInterrupt:
        log.error("Pipeline interrupted by user.")
        return 130
    except Exception as exc:
        log.error("Fatal pipeline failure: %s", exc)
        log.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
