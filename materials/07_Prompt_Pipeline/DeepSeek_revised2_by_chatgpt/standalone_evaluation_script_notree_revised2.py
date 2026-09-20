#!/usr/bin/env python3
"""
standalone_evaluation_script_notree_revised.py
================================================
Evaluate the artefacts produced by speech_processing_program_notree_revised.py,
including the argumentative-home classification and relationship-aware Phase 5
schema introduced in classification/bucket version 2.1.

This evaluator is intentionally aligned with the revised pipeline's data model:

    source speech records
        -> canonical Central Claims and canonical Themes
        -> persistent Canonical CC x Theme pairs
        -> lossless Phase 4 remapped records and source contributions
        -> pair-specific Phase 5 syntheses
        -> authoritative compendium.md sections and deterministic Theme indexes

It does not require a DeepSeek API key and does not perform web search. Semantic
metrics use the same sentence-transformer model configured by the pipeline.
Structural metrics can still run with --skip-semantic when that model is not
available locally.

Spyder-friendly
---------------
Press Run with no arguments to use the DEFAULT_* paths below. All defaults are
relative to the current working directory. Path() handles Windows and POSIX
path separators.

Metrics and integrity checks
----------------------------
1. Phase and manifest health
   Verifies the revised five-phase directory structure, manifest completion,
   artefact counts, output hashes, and dependency links between phases.

2. Canonical semantic distinctness
   Measures near-duplicate rates separately for canonical Central Claims and
   canonical Themes. Count targets are reported as advisory diagnostics, not
   hard validity requirements.

3. Classification and mapping quality
   Measures categorisation coverage, stored confidence, controlled
   speech-to-chapter relationship types and explanations, relationship-aware
   mapping preservation, Theme-assignment limits, and default pair-membership
   correctness. Assigned-CC embedding similarity is retained as a diagnostic,
   not treated as an equivalence requirement.

4. Usage distributions
   Reports entropy, normalised entropy, Gini concentration, dominant entities,
   and unused canonical entities for CC, Theme, and CC x Theme pair usage.

5. Canonical pair and Theme-sharing structure
   Evaluates the authoritative cc_theme_pairs.json table: uniqueness,
   referential integrity, shared-Theme rate, pair density, source coverage, and
   deterministic aggregation of relationship types by pair.

6. Lossless Phase 4 remapping
   Confirms that Phase 4 preserves Phase 1 local claims, Themes, arguments,
   evidence, analogies, and unverifiable claims while adding canonical mapping
   metadata. It also verifies exact propagation of relationship type,
   explanation, confidence, and classification versions into every source
   contribution.

7. Pair-synthesis provenance
   Validates Phase 5 bucket checkpoints against known Phase 4 source
   contributions. Canonical arguments and evidence must retain valid source
   contribution IDs and source filenames, remain owned by one pair, and contain
   a complete relationship-role summary that does not erase qualification or
   opposition.

8. Publication and index integrity
   Checks that every persistent pair has exactly one authoritative compendium
   anchor, appears exactly once in theme_index.md, and that the shared-Theme
   cross-index contains exactly the expected shared-pair links.

9. Unverifiable-claim completeness
   Reconstructs the expected published list from explicit Phase 1
   unverifiable claims plus evidence labelled Unverifiable. No record may be
   excluded because MEMORY is Corroborated.

10. Canonical-version and stale-checkpoint consistency
    Checks canonical_model_version, base schema/prompt versions, classification
    schema/prompt versions, bucket schema/prompt versions, controlled
    relationship vocabulary, Phase 4 dependencies, and Phase 5 syntheses for
    stale artefacts.

Requirements
------------
Core structural evaluation uses only the Python standard library plus numpy.
Semantic metrics additionally require:

    pip install sentence-transformers scikit-learn numpy
"""

# ── Standard library ─────────────────────────────────────────────────────────
import argparse
import ast
import hashlib
import json
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

# ── Third-party: numpy is used throughout; semantic packages are lazy-loaded ─
try:
    import numpy as np
except ImportError as exc:
    sys.exit(
        "Missing dependency: {0}\nRun: pip install numpy".format(exc)
    )

SentenceTransformer = None
silhouette_score = None


# ═════════════════════════════════════════════════════════════════════════════
# Default paths — revised pipeline layout
# ═════════════════════════════════════════════════════════════════════════════

DEFAULT_PIPELINE_SCRIPT = "./speech_processing_program_notree_revised.py"
DEFAULT_TRANSCRIPTS_DIR = "./transcripts"
DEFAULT_OUTPUT_DIR = "./output"
DEFAULT_METRICS_OUTPUT = "./output/evaluation_metrics.json"

# Fallbacks used when the pipeline script cannot be parsed.
FALLBACK_EMBEDDING_MODEL = "mukaj/fin-mpnet-base"
FALLBACK_CC_DEDUP_THRESHOLD = 0.85
FALLBACK_THEME_DEDUP_THRESHOLD = 0.85
FALLBACK_CLASSIFICATION_CONFIDENCE_MIN = 0.70
FALLBACK_THEME_MAPPING_CONFIDENCE_MIN = 0.55
FALLBACK_MAX_THEMES_PER_SPEECH = 3
FALLBACK_CC_RATIO_MIN = 0.06
FALLBACK_CC_RATIO_MAX = 0.08
FALLBACK_THEME_RATIO_MIN = 0.12
FALLBACK_THEME_RATIO_MAX = 0.16
FALLBACK_SCHEMA_VERSION = "2.0"
FALLBACK_PROMPT_VERSION = "2.0"
FALLBACK_CLASSIFICATION_PROMPT_VERSION = "2.1"
FALLBACK_CLASSIFICATION_SCHEMA_VERSION = "2.1"
FALLBACK_BUCKET_PROMPT_VERSION = "2.1"
FALLBACK_BUCKET_SCHEMA_VERSION = "2.1"
FALLBACK_PRIMARY_CC_RELATIONSHIP_TYPES = (
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

# Evaluation-only warning thresholds. These do not alter pipeline output.
LOW_ASSIGNED_CC_SIMILARITY = 0.45
DOMINANT_CC_PCT = 25.0
DOMINANT_PAIR_PCT = 15.0
HEALTH_COMPLETION_PCT = 95.0
LOW_PROVENANCE_COVERAGE_PCT = 98.0


# ═════════════════════════════════════════════════════════════════════════════
# Data classes
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class PipelineConfig:
    """Configuration values read from speech_processing_program_notree_revised.py."""

    embedding_model: str = FALLBACK_EMBEDDING_MODEL
    cc_dedup_threshold: float = FALLBACK_CC_DEDUP_THRESHOLD
    theme_dedup_threshold: float = FALLBACK_THEME_DEDUP_THRESHOLD
    classification_confidence_min: float = FALLBACK_CLASSIFICATION_CONFIDENCE_MIN
    theme_mapping_confidence_min: float = FALLBACK_THEME_MAPPING_CONFIDENCE_MIN
    max_themes_per_speech: int = FALLBACK_MAX_THEMES_PER_SPEECH
    cc_ratio_min: float = FALLBACK_CC_RATIO_MIN
    cc_ratio_max: float = FALLBACK_CC_RATIO_MAX
    theme_ratio_min: float = FALLBACK_THEME_RATIO_MIN
    theme_ratio_max: float = FALLBACK_THEME_RATIO_MAX
    schema_version: str = FALLBACK_SCHEMA_VERSION
    prompt_version: str = FALLBACK_PROMPT_VERSION
    classification_prompt_version: str = FALLBACK_CLASSIFICATION_PROMPT_VERSION
    classification_schema_version: str = FALLBACK_CLASSIFICATION_SCHEMA_VERSION
    bucket_prompt_version: str = FALLBACK_BUCKET_PROMPT_VERSION
    bucket_schema_version: str = FALLBACK_BUCKET_SCHEMA_VERSION
    primary_cc_relationship_types: Tuple[str, ...] = FALLBACK_PRIMARY_CC_RELATIONSHIP_TYPES
    assembly_bucket_limit: int = 20
    bucket_subgroup_size: int = 10
    target_counts_are_hard: bool = False
    allow_secondary_cc_contributions: bool = False
    source: str = "fallback defaults"


@dataclass
class Paths:
    """All revised pipeline paths derived from output_dir."""

    pipeline_script: Path
    transcripts_dir: Path
    output_dir: Path
    metrics_output: Path

    checkpoints_dir: Path = field(init=False)
    phase1_dir: Path = field(init=False)
    phase2_dir: Path = field(init=False)
    phase3_dir: Path = field(init=False)
    phase4_dir: Path = field(init=False)
    phase5_dir: Path = field(init=False)
    phase5_buckets_dir: Path = field(init=False)
    phase5_subgroups_dir: Path = field(init=False)

    phase1_manifest: Path = field(init=False)
    master_inventory: Path = field(init=False)
    inventory_manifest: Path = field(init=False)
    duplicate_diagnostics: Path = field(init=False)

    canonical_ccs: Path = field(init=False)
    canonical_themes: Path = field(init=False)
    local_mappings: Path = field(init=False)
    classifications: Path = field(init=False)
    cc_theme_pairs: Path = field(init=False)
    secondary_contributions: Path = field(init=False)
    canonical_history: Path = field(init=False)
    canonical_manifest: Path = field(init=False)

    uncategorised: Path = field(init=False)
    phase4_manifest: Path = field(init=False)

    phase5_manifest: Path = field(init=False)
    compendium: Path = field(init=False)
    theme_index: Path = field(init=False)
    unverifiable: Path = field(init=False)
    integrity_report: Path = field(init=False)

    def __post_init__(self) -> None:
        self.checkpoints_dir = self.output_dir / "checkpoints"
        self.phase1_dir = self.checkpoints_dir / "phase1"
        self.phase2_dir = self.checkpoints_dir / "phase2"
        self.phase3_dir = self.checkpoints_dir / "phase3"
        self.phase4_dir = self.checkpoints_dir / "phase4"
        self.phase5_dir = self.checkpoints_dir / "phase5"
        self.phase5_buckets_dir = self.phase5_dir / "buckets"
        self.phase5_subgroups_dir = self.phase5_dir / "subgroups"

        self.phase1_manifest = self.phase1_dir / "manifest.json"
        self.master_inventory = self.phase2_dir / "master_inventory.json"
        self.inventory_manifest = self.phase2_dir / "inventory_manifest.json"
        self.duplicate_diagnostics = self.phase2_dir / "near_duplicate_diagnostics.json"

        self.canonical_ccs = self.phase3_dir / "canonical_ccs.json"
        self.canonical_themes = self.phase3_dir / "canonical_themes.json"
        self.local_mappings = self.phase3_dir / "local_to_canonical_mappings.json"
        self.classifications = self.phase3_dir / "speech_classifications.json"
        self.cc_theme_pairs = self.phase3_dir / "cc_theme_pairs.json"
        self.secondary_contributions = self.phase3_dir / "secondary_cc_contributions.json"
        self.canonical_history = self.phase3_dir / "canonical_history.json"
        self.canonical_manifest = self.phase3_dir / "manifest.json"

        self.uncategorised = self.phase4_dir / "uncategorised.jsonl"
        self.phase4_manifest = self.phase4_dir / "manifest.json"

        self.phase5_manifest = self.phase5_dir / "manifest.json"
        self.compendium = self.output_dir / "compendium.md"
        self.theme_index = self.output_dir / "theme_index.md"
        self.unverifiable = self.output_dir / "unverifiable_claims.md"
        self.integrity_report = self.output_dir / "integrity_report.json"


@dataclass
class EvaluationData:
    """Loaded pipeline artefacts."""

    phase1_records: List[Dict[str, Any]]
    phase1_wrappers: Dict[str, Dict[str, Any]]
    inventory: List[Dict[str, Any]]
    canonical_ccs: List[Dict[str, Any]]
    canonical_themes: List[Dict[str, Any]]
    mappings: List[Dict[str, Any]]
    classifications: List[Dict[str, Any]]
    pairs: List[Dict[str, Any]]
    secondary_contributions: List[Dict[str, Any]]
    phase4_records: List[Dict[str, Any]]
    phase4_wrappers: Dict[str, Dict[str, Any]]
    bucket_syntheses: Dict[str, Dict[str, Any]]
    bucket_wrappers: Dict[str, Dict[str, Any]]
    manifests: Dict[str, Dict[str, Any]]
    integrity_report: Dict[str, Any]
    compendium_text: str
    theme_index_text: str
    unverifiable_text: str


# ═════════════════════════════════════════════════════════════════════════════
# Basic utilities
# ═════════════════════════════════════════════════════════════════════════════


def _read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("Could not parse JSON file {0}: {1}".format(path, exc))


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_file(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    return _sha256_bytes(path.read_bytes())


def _normalise_whitespace(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalise_key(value: Any) -> str:
    text = _normalise_whitespace(value).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()



def _relationship_type_name(value: Any, allowed: Sequence[str]) -> Optional[str]:
    """Normalise and validate the controlled speech-to-CC relationship type."""
    text = _normalise_whitespace(value).lower().replace("-", "_").replace(" ", "_")
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
    return text if text in set(allowed) else None


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
    return labels.get(value, str(value or "").replace("_", " ").title())


def _safe_pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator) * 100.0


def _summary_stats(values: Sequence[float]) -> Dict[str, Optional[float]]:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if not clean:
        return {
            "count": 0,
            "minimum": None,
            "maximum": None,
            "mean": None,
            "median": None,
            "p10": None,
            "p90": None,
        }
    array = np.asarray(clean, dtype=float)
    return {
        "count": len(clean),
        "minimum": round(float(np.min(array)), 6),
        "maximum": round(float(np.max(array)), 6),
        "mean": round(float(np.mean(array)), 6),
        "median": round(float(np.median(array)), 6),
        "p10": round(float(np.percentile(array, 10)), 6),
        "p90": round(float(np.percentile(array, 90)), 6),
    }


def _gini_from_counts(counts: Sequence[int]) -> float:
    values = np.asarray([float(value) for value in counts if value >= 0], dtype=float)
    if values.size == 0 or float(values.sum()) == 0.0:
        return 0.0
    values = np.sort(values)
    n = values.size
    index = np.arange(1, n + 1)
    return float((2.0 * np.sum(index * values) / (n * np.sum(values))) - (n + 1.0) / n)


def _entropy_from_counts(counts: Sequence[int]) -> Tuple[float, float, float]:
    values = np.asarray([float(value) for value in counts if value > 0], dtype=float)
    if values.size == 0:
        return 0.0, 0.0, 0.0
    probabilities = values / values.sum()
    entropy = float(-np.sum(probabilities * np.log(probabilities)))
    max_entropy = float(np.log(values.size)) if values.size > 1 else 0.0
    pct = entropy / max_entropy * 100.0 if max_entropy > 0.0 else 100.0
    return entropy, max_entropy, pct


def _distribution_report(
    counts: Mapping[str, int],
    labels: Optional[Mapping[str, str]] = None,
    total_available: Optional[int] = None,
) -> Dict[str, Any]:
    labels = labels or {}
    total = int(sum(counts.values()))
    values = list(counts.values())
    entropy, max_entropy, entropy_pct = _entropy_from_counts(values)
    gini = _gini_from_counts(values)
    rows = []
    for entity_id, count in counts.items():
        rows.append(
            {
                "id": entity_id,
                "label": labels.get(entity_id, entity_id),
                "count": int(count),
                "pct": round(_safe_pct(count, total), 4),
            }
        )
    rows.sort(key=lambda item: (-item["count"], item["id"]))
    used = set(counts)
    available_ids = set(labels)
    unused = sorted(available_ids - used)
    return {
        "total_assignments": total,
        "distinct_used": len(counts),
        "total_available": total_available if total_available is not None else len(labels),
        "unused_ids": unused,
        "entropy": round(entropy, 6),
        "max_entropy": round(max_entropy, 6),
        "normalised_entropy_pct": round(entropy_pct, 4),
        "gini": round(gini, 6),
        "per_entity": rows,
    }


def _candidate_count_range(total: int, minimum_ratio: float, maximum_ratio: float) -> Tuple[int, int]:
    minimum = max(1, round(total * minimum_ratio))
    maximum = max(minimum, round(total * maximum_ratio))
    return minimum, maximum


def _looks_like_proposition(text: str) -> bool:
    words = _normalise_whitespace(text).split()
    if len(words) < 4:
        return False
    common_verbs = {
        "is", "are", "was", "were", "be", "becomes", "became", "causes", "cause",
        "creates", "create", "drives", "drive", "leads", "lead", "produces", "produce",
        "increases", "increase", "reduces", "reduce", "distorts", "distort", "requires",
        "require", "prevents", "prevent", "encourages", "encourage", "undermines",
        "undermine", "functions", "function", "represents", "represent", "depends",
        "affects", "affect", "will", "can", "must", "should", "may", "does", "do",
        "has", "have", "makes", "make", "results", "result", "transfers", "transfer",
    }
    lowered = {re.sub(r"[^a-z]", "", word.lower()) for word in words}
    return bool(lowered & common_verbs)


def _looks_like_theme(text: str) -> bool:
    clean = _normalise_whitespace(text)
    if not clean or len(clean.split()) > 14:
        return False
    # This is deliberately only a warning heuristic. Noun phrases can contain
    # participles, and some finance terms resemble verbs.
    return not bool(re.search(r"\b(is|are|was|were|will|causes?|creates?|drives?|leads?|produces?)\b", clean.lower()))


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


# ═════════════════════════════════════════════════════════════════════════════
# Pipeline configuration parser
# ═════════════════════════════════════════════════════════════════════════════


def _literal_assignments_from_python(path: Path) -> Dict[str, Any]:
    """Read simple top-level literal assignments without importing the pipeline."""
    if not path.exists():
        return {}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except Exception:
        return {}
    assignments = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        try:
            assignments[target.id] = ast.literal_eval(node.value)
        except Exception:
            continue
    return assignments


def load_pipeline_config(path: Path) -> PipelineConfig:
    values = _literal_assignments_from_python(path)
    config = PipelineConfig()
    mappings = {
        "EMBEDDING_MODEL_NAME": "embedding_model",
        "CC_DEDUP_THRESHOLD": "cc_dedup_threshold",
        "THEME_DEDUP_THRESHOLD": "theme_dedup_threshold",
        "CLASSIFICATION_CONFIDENCE_MIN": "classification_confidence_min",
        "THEME_MAPPING_CONFIDENCE_MIN": "theme_mapping_confidence_min",
        "MAX_THEMES_PER_SPEECH": "max_themes_per_speech",
        "CC_RATIO_MIN": "cc_ratio_min",
        "CC_RATIO_MAX": "cc_ratio_max",
        "THEME_RATIO_MIN": "theme_ratio_min",
        "THEME_RATIO_MAX": "theme_ratio_max",
        "SCHEMA_VERSION": "schema_version",
        "PROMPT_VERSION": "prompt_version",
        "CLASSIFICATION_PROMPT_VERSION": "classification_prompt_version",
        "CLASSIFICATION_SCHEMA_VERSION": "classification_schema_version",
        "BUCKET_PROMPT_VERSION": "bucket_prompt_version",
        "BUCKET_SCHEMA_VERSION": "bucket_schema_version",
        "PRIMARY_CC_RELATIONSHIP_TYPES": "primary_cc_relationship_types",
        "ASSEMBLY_BUCKET_LIMIT": "assembly_bucket_limit",
        "BUCKET_SUBGROUP_SIZE": "bucket_subgroup_size",
        "TARGET_COUNTS_ARE_HARD": "target_counts_are_hard",
        "ALLOW_SECONDARY_CC_CONTRIBUTIONS": "allow_secondary_cc_contributions",
    }
    for source_name, destination_name in mappings.items():
        if source_name in values:
            setattr(config, destination_name, values[source_name])
    config.primary_cc_relationship_types = tuple(config.primary_cc_relationship_types)
    if values:
        config.source = str(path)
    return config


# ═════════════════════════════════════════════════════════════════════════════
# Artefact loaders
# ═════════════════════════════════════════════════════════════════════════════


def _load_wrapped_records(
    directory: Path,
    payload_key: str,
    exclude_names: Optional[Set[str]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    exclude_names = exclude_names or set()
    records = []
    wrappers = {}
    if not directory.exists():
        return records, wrappers
    for path in sorted(directory.glob("*.json")):
        if path.name in exclude_names:
            continue
        raw = _read_json(path, default=None)
        if not isinstance(raw, dict):
            continue
        payload = raw.get(payload_key)
        if not isinstance(payload, dict):
            continue
        records.append(payload)
        wrappers[path.name] = raw
    return records, wrappers


def load_evaluation_data(paths: Paths) -> EvaluationData:
    phase1_records, phase1_wrappers = _load_wrapped_records(
        paths.phase1_dir, "record", {"manifest.json"}
    )
    phase4_records, phase4_wrappers = _load_wrapped_records(
        paths.phase4_dir, "record", {"manifest.json"}
    )
    bucket_records, bucket_wrappers = _load_wrapped_records(
        paths.phase5_buckets_dir, "synthesis", set()
    )
    bucket_syntheses = {
        record.get("pair_id", ""): record
        for record in bucket_records
        if record.get("pair_id")
    }

    manifests = {
        "phase1": _read_json(paths.phase1_manifest, {}) or {},
        "phase2": _read_json(paths.inventory_manifest, {}) or {},
        "phase3": _read_json(paths.canonical_manifest, {}) or {},
        "phase4": _read_json(paths.phase4_manifest, {}) or {},
        "phase5": _read_json(paths.phase5_manifest, {}) or {},
    }

    return EvaluationData(
        phase1_records=phase1_records,
        phase1_wrappers=phase1_wrappers,
        inventory=_read_json(paths.master_inventory, []) or [],
        canonical_ccs=_read_json(paths.canonical_ccs, []) or [],
        canonical_themes=_read_json(paths.canonical_themes, []) or [],
        mappings=_read_json(paths.local_mappings, []) or [],
        classifications=_read_json(paths.classifications, []) or [],
        pairs=_read_json(paths.cc_theme_pairs, []) or [],
        secondary_contributions=_read_json(paths.secondary_contributions, []) or [],
        phase4_records=phase4_records,
        phase4_wrappers=phase4_wrappers,
        bucket_syntheses=bucket_syntheses,
        bucket_wrappers=bucket_wrappers,
        manifests=manifests,
        integrity_report=_read_json(paths.integrity_report, {}) or {},
        compendium_text=_read_text(paths.compendium),
        theme_index_text=_read_text(paths.theme_index),
        unverifiable_text=_read_text(paths.unverifiable),
    )


# ═════════════════════════════════════════════════════════════════════════════
# Semantic model helpers
# ═════════════════════════════════════════════════════════════════════════════


def _load_semantic_dependencies() -> None:
    global SentenceTransformer, silhouette_score
    if SentenceTransformer is not None and silhouette_score is not None:
        return
    try:
        from sentence_transformers import SentenceTransformer as _SentenceTransformer
        from sklearn.metrics import silhouette_score as _silhouette_score
    except ImportError as exc:
        raise RuntimeError(
            "Semantic evaluation dependencies are unavailable: {0}. "
            "Install with: pip install sentence-transformers scikit-learn numpy, "
            "or run with --skip-semantic.".format(exc)
        )
    SentenceTransformer = _SentenceTransformer
    silhouette_score = _silhouette_score


def _encode(model: Any, texts: Sequence[str]) -> np.ndarray:
    if not texts:
        return np.empty((0, 0), dtype=float)
    return np.asarray(
        model.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
        ),
        dtype=float,
    )


def semantic_near_duplicates(
    entities: Sequence[Dict[str, Any]],
    id_key: str,
    text_key: str,
    model: Any,
    threshold: float,
) -> Dict[str, Any]:
    clean = [entity for entity in entities if _normalise_whitespace(entity.get(text_key, ""))]
    if len(clean) < 2:
        return {
            "entity_count": len(clean),
            "possible_pair_count": 0,
            "near_duplicate_pair_count": 0,
            "pair_rate": 0.0,
            "affected_entity_count": 0,
            "affected_entity_rate": 0.0,
            "pairs": [],
        }
    texts = [_normalise_whitespace(item[text_key]) for item in clean]
    embeddings = _encode(model, texts)
    similarities = embeddings @ embeddings.T
    pairs = []
    affected = set()
    for left in range(len(clean)):
        for right in range(left + 1, len(clean)):
            similarity = float(similarities[left, right])
            if similarity >= threshold:
                affected.add(clean[left].get(id_key, str(left)))
                affected.add(clean[right].get(id_key, str(right)))
                pairs.append(
                    {
                        "left_id": clean[left].get(id_key, ""),
                        "left_text": texts[left],
                        "right_id": clean[right].get(id_key, ""),
                        "right_text": texts[right],
                        "similarity": round(similarity, 6),
                    }
                )
    pairs.sort(key=lambda item: -item["similarity"])
    possible = len(clean) * (len(clean) - 1) // 2
    return {
        "entity_count": len(clean),
        "possible_pair_count": possible,
        "near_duplicate_pair_count": len(pairs),
        "pair_rate": round(len(pairs) / float(possible), 8) if possible else 0.0,
        "affected_entity_count": len(affected),
        "affected_entity_rate": round(len(affected) / float(len(clean)), 8),
        "pairs": pairs,
    }


# ═════════════════════════════════════════════════════════════════════════════
# Metric 1 — phase, manifest, and dependency health
# ═════════════════════════════════════════════════════════════════════════════


def _manifest_output_hash_checks(
    manifest: Dict[str, Any],
    project_root: Path,
) -> Dict[str, Any]:
    mismatches = []
    missing = []
    skipped_self_references = []
    checked = 0
    outputs = manifest.get("outputs", {}) if isinstance(manifest, dict) else {}
    if not isinstance(outputs, dict):
        outputs = {}
    for raw_path, expected_hash in outputs.items():
        raw = Path(raw_path)
        # Some pipeline phases may accidentally include their own manifest in
        # the output-hash table on a rerun. A manifest cannot reliably hash
        # itself because writing the new hash changes the file. Ignore that
        # self-reference rather than reporting a false stale-output warning.
        if raw.name == "manifest.json":
            skipped_self_references.append(raw_path)
            continue
        candidates = [raw]
        if not raw.is_absolute():
            candidates.append(project_root / raw)
        path = next((candidate for candidate in candidates if candidate.exists()), None)
        if path is None:
            missing.append(raw_path)
            continue
        checked += 1
        actual_hash = _hash_file(path)
        if actual_hash != expected_hash:
            mismatches.append(
                {
                    "path": raw_path,
                    "resolved_path": str(path),
                    "expected_hash": expected_hash,
                    "actual_hash": actual_hash,
                }
            )
    return {
        "declared_output_count": len(outputs),
        "checked_output_count": checked,
        "missing_outputs": missing,
        "hash_mismatches": mismatches,
        "skipped_self_referential_manifest_outputs": skipped_self_references,
        "pass": not missing and not mismatches,
    }


def phase_and_manifest_health(paths: Paths, data: EvaluationData) -> Dict[str, Any]:
    transcript_count = len(list(paths.transcripts_dir.glob("*.txt"))) if paths.transcripts_dir.exists() else 0
    phase1_count = len(data.phase1_records)
    inventory_count = len(data.inventory)
    classification_count = len(data.classifications)
    phase4_count = len(data.phase4_records)
    categorised_count = sum(1 for item in data.classifications if item.get("status") == "categorised")
    nonempty_pair_count = sum(1 for pair in data.pairs if pair.get("source_contribution_ids") or pair.get("source_speech_ids"))
    bucket_count = len(data.bucket_syntheses)

    final_outputs = {
        "compendium.md": paths.compendium.exists(),
        "theme_index.md": paths.theme_index.exists(),
        "unverifiable_claims.md": paths.unverifiable.exists(),
        "integrity_report.json": paths.integrity_report.exists(),
    }

    phases = {
        "phase1": {
            "expected": transcript_count,
            "completed": phase1_count,
            "rate_pct": round(_safe_pct(phase1_count, transcript_count), 4),
            "manifest_complete": bool(data.manifests["phase1"].get("complete")),
        },
        "phase2": {
            "expected": phase1_count,
            "completed": inventory_count,
            "rate_pct": round(_safe_pct(inventory_count, phase1_count), 4),
            "manifest_complete": bool(data.manifests["phase2"].get("complete")),
        },
        "phase3": {
            "expected": inventory_count,
            "completed": classification_count,
            "rate_pct": round(_safe_pct(classification_count, inventory_count), 4),
            "manifest_complete": bool(data.manifests["phase3"].get("complete")),
            "categorised_count": categorised_count,
        },
        "phase4": {
            "expected": inventory_count,
            "completed": phase4_count,
            "rate_pct": round(_safe_pct(phase4_count, inventory_count), 4),
            "manifest_complete": bool(data.manifests["phase4"].get("complete")),
        },
        "phase5": {
            "expected_pair_syntheses": nonempty_pair_count,
            "completed_pair_syntheses": bucket_count,
            "rate_pct": round(_safe_pct(bucket_count, nonempty_pair_count), 4),
            "manifest_complete": bool(data.manifests["phase5"].get("complete")),
            "final_outputs": final_outputs,
            "integrity_status": data.integrity_report.get("status"),
        },
    }

    hash_checks = {
        phase: _manifest_output_hash_checks(manifest, paths.output_dir.parent)
        for phase, manifest in data.manifests.items()
    }

    dependency_links = []
    phase1_hash = data.manifests["phase1"].get("manifest_hash")
    phase2_hash = data.manifests["phase2"].get("manifest_hash")
    phase3_hash = data.manifests["phase3"].get("manifest_hash")
    phase4_hash = data.manifests["phase4"].get("manifest_hash")

    expected_links = [
        (
            "phase2 -> phase1",
            data.manifests["phase2"].get("dependencies", {}).get("phase1_manifest_hash"),
            phase1_hash,
        ),
        (
            "phase3 -> phase2",
            data.manifests["phase3"].get("dependencies", {}).get("inventory_manifest_hash"),
            phase2_hash,
        ),
        (
            "phase4 -> phase3",
            data.manifests["phase4"].get("dependencies", {}).get("phase3_manifest_hash"),
            phase3_hash,
        ),
        (
            "phase5 -> phase4",
            data.manifests["phase5"].get("dependencies", {}).get("phase4_manifest_hash"),
            phase4_hash,
        ),
    ]
    for name, recorded, actual in expected_links:
        dependency_links.append(
            {
                "link": name,
                "recorded_hash": recorded,
                "actual_hash": actual,
                "pass": bool(recorded and actual and recorded == actual),
            }
        )

    warnings = []
    errors = []
    for phase, item in phases.items():
        rate = item.get("rate_pct", 0.0)
        if phase != "phase5" and item["expected"] > 0 and rate < HEALTH_COMPLETION_PCT:
            errors.append("{0} completion is {1:.1f}%".format(phase, rate))
        if not item.get("manifest_complete"):
            errors.append("{0} manifest is absent or incomplete".format(phase))
    if nonempty_pair_count and phases["phase5"]["rate_pct"] < HEALTH_COMPLETION_PCT:
        errors.append("Phase 5 pair-synthesis completion is below 95%")
    for name, exists in final_outputs.items():
        if not exists:
            errors.append("Missing final output: {0}".format(name))
    for phase, check in hash_checks.items():
        if not check["pass"]:
            warnings.append("{0} manifest output hashes are stale or incomplete".format(phase))
    for link in dependency_links:
        if not link["pass"]:
            warnings.append("Dependency hash mismatch: {0}".format(link["link"]))

    return {
        "transcript_count": transcript_count,
        "phases": phases,
        "manifest_output_hashes": hash_checks,
        "dependency_links": dependency_links,
        "errors": errors,
        "warnings": warnings,
        "status": "PASS" if not errors else "FAIL",
    }


# ═════════════════════════════════════════════════════════════════════════════
# Metric 2 — canonical entity quality
# ═════════════════════════════════════════════════════════════════════════════


def canonical_entity_quality(
    data: EvaluationData,
    config: PipelineConfig,
    model: Optional[Any],
) -> Dict[str, Any]:
    speech_count = len(data.inventory)
    cc_range = _candidate_count_range(speech_count, config.cc_ratio_min, config.cc_ratio_max)
    theme_range = _candidate_count_range(speech_count, config.theme_ratio_min, config.theme_ratio_max)

    cc_labels = [item.get("claim", "") for item in data.canonical_ccs]
    theme_labels = [item.get("theme", "") for item in data.canonical_themes]
    cc_form_failures = [
        {"cc_id": item.get("cc_id"), "claim": item.get("claim", "")}
        for item in data.canonical_ccs
        if not _looks_like_proposition(item.get("claim", ""))
    ]
    theme_form_failures = [
        {"theme_id": item.get("theme_id"), "theme": item.get("theme", "")}
        for item in data.canonical_themes
        if not _looks_like_theme(item.get("theme", ""))
    ]

    exact_cc_duplicates = [
        text for text, count in Counter(_normalise_key(value) for value in cc_labels if value).items() if count > 1
    ]
    exact_theme_duplicates = [
        text for text, count in Counter(_normalise_key(value) for value in theme_labels if value).items() if count > 1
    ]

    if model is not None:
        cc_semantic = semantic_near_duplicates(
            data.canonical_ccs, "cc_id", "claim", model, config.cc_dedup_threshold
        )
        theme_semantic = semantic_near_duplicates(
            data.canonical_themes, "theme_id", "theme", model, config.theme_dedup_threshold
        )
    else:
        cc_semantic = {"skipped": True, "reason": "--skip-semantic"}
        theme_semantic = {"skipped": True, "reason": "--skip-semantic"}

    warnings = []
    if not (cc_range[0] <= len(data.canonical_ccs) <= cc_range[1]):
        warnings.append(
            "Canonical CC count {0} is outside advisory range {1}-{2}.".format(
                len(data.canonical_ccs), cc_range[0], cc_range[1]
            )
        )
    if not (theme_range[0] <= len(data.canonical_themes) <= theme_range[1]):
        warnings.append(
            "Canonical Theme count {0} is outside advisory range {1}-{2}.".format(
                len(data.canonical_themes), theme_range[0], theme_range[1]
            )
        )
    if exact_cc_duplicates:
        warnings.append("Exact duplicate canonical CC labels exist.")
    if exact_theme_duplicates:
        warnings.append("Exact duplicate canonical Theme labels exist.")

    return {
        "canonical_cc_count": len(data.canonical_ccs),
        "canonical_theme_count": len(data.canonical_themes),
        "advisory_cc_count_range": list(cc_range),
        "advisory_theme_count_range": list(theme_range),
        "targets_are_hard": config.target_counts_are_hard,
        "cc_form_warning_count": len(cc_form_failures),
        "cc_form_warnings": cc_form_failures,
        "theme_form_warning_count": len(theme_form_failures),
        "theme_form_warnings": theme_form_failures,
        "exact_duplicate_cc_keys": exact_cc_duplicates,
        "exact_duplicate_theme_keys": exact_theme_duplicates,
        "cc_semantic_near_duplicates": cc_semantic,
        "theme_semantic_near_duplicates": theme_semantic,
        "warnings": warnings,
    }


# ═════════════════════════════════════════════════════════════════════════════
# Metric 3 — classification and mapping quality
# ═════════════════════════════════════════════════════════════════════════════


def classification_and_mapping_quality(
    data: EvaluationData,
    config: PipelineConfig,
    model: Optional[Any],
) -> Dict[str, Any]:
    valid_cc_ids = {item.get("cc_id") for item in data.canonical_ccs}
    valid_theme_ids = {item.get("theme_id") for item in data.canonical_themes}
    pair_map = {item.get("pair_id"): item for item in data.pairs}
    inventory_by_speech = {item.get("speech_id"): item for item in data.inventory}
    cc_by_id = {item.get("cc_id"): item for item in data.canonical_ccs}
    allowed_relationship_types = tuple(config.primary_cc_relationship_types)
    allowed_relationship_set = set(allowed_relationship_types)

    categorised = [
        item for item in data.classifications
        if item.get("status") == "categorised"
    ]
    uncategorised = [
        item for item in data.classifications
        if item.get("status") != "categorised"
    ]
    confidences = [
        float(item.get("primary_cc_confidence", 0.0))
        for item in categorised
    ]

    errors = []
    warnings = []
    invalid_cc = []
    invalid_themes = []
    invalid_memberships = []
    invalid_theme_counts = []
    cross_cc_default_memberships = []
    duplicate_theme_assignments = []
    invalid_relationship_types = []
    missing_relationship_explanations = []
    classification_version_mismatches = []
    cc_mapping_mismatches = []
    uncategorised_without_rejection_reason = []

    cc_mappings_by_speech = defaultdict(list)
    for mapping in data.mappings:
        if mapping.get("mapping_type") == "local_cc_to_canonical_cc":
            cc_mappings_by_speech[mapping.get("speech_id")].append(mapping)

    relationship_type_distribution = Counter()
    relationship_type_by_cc = defaultdict(Counter)
    rejection_reason_distribution = Counter()

    for item in categorised:
        speech_id = item.get("speech_id")
        cc_id = item.get("primary_cc_id")
        theme_ids = item.get("theme_ids", []) or []
        memberships = item.get("bucket_memberships", []) or []

        relationship_type = _relationship_type_name(
            item.get("primary_cc_relationship_type"),
            allowed_relationship_types,
        )
        explanation = _normalise_whitespace(
            item.get("primary_cc_relationship_explanation", "")
        )
        if relationship_type is None:
            invalid_relationship_types.append(
                {
                    "speech_id": speech_id,
                    "filename": item.get("filename"),
                    "value": item.get("primary_cc_relationship_type"),
                }
            )
        else:
            relationship_type_distribution[relationship_type] += 1
            relationship_type_by_cc[cc_id][relationship_type] += 1
        if not explanation:
            missing_relationship_explanations.append(
                {"speech_id": speech_id, "filename": item.get("filename")}
            )

        if (
            item.get("classification_prompt_version")
            != config.classification_prompt_version
            or item.get("classification_schema_version")
            != config.classification_schema_version
        ):
            classification_version_mismatches.append(
                {
                    "speech_id": speech_id,
                    "prompt_version": item.get("classification_prompt_version"),
                    "schema_version": item.get("classification_schema_version"),
                }
            )

        if cc_id not in valid_cc_ids:
            invalid_cc.append({"speech_id": speech_id, "cc_id": cc_id})
        for theme_id in theme_ids:
            if theme_id not in valid_theme_ids:
                invalid_themes.append(
                    {"speech_id": speech_id, "theme_id": theme_id}
                )
        if not (1 <= len(theme_ids) <= config.max_themes_per_speech):
            invalid_theme_counts.append(
                {"speech_id": speech_id, "theme_ids": theme_ids}
            )
        if len(theme_ids) != len(set(theme_ids)):
            duplicate_theme_assignments.append(
                {"speech_id": speech_id, "theme_ids": theme_ids}
            )

        expected_pair_ids = set()
        for theme_id in theme_ids:
            matching_pair = [
                pair_id
                for pair_id, pair in pair_map.items()
                if pair.get("cc_id") == cc_id
                and pair.get("theme_id") == theme_id
            ]
            expected_pair_ids.update(matching_pair)
        actual_pair_ids = {
            membership.get("pair_id") for membership in memberships
        }
        if expected_pair_ids != actual_pair_ids:
            invalid_memberships.append(
                {
                    "speech_id": speech_id,
                    "expected_pair_ids": sorted(expected_pair_ids),
                    "actual_pair_ids": sorted(
                        value for value in actual_pair_ids if value
                    ),
                }
            )
        for membership in memberships:
            pair = pair_map.get(membership.get("pair_id"))
            if not pair:
                continue
            if pair.get("cc_id") != cc_id:
                cross_cc_default_memberships.append(
                    {
                        "speech_id": speech_id,
                        "primary_cc_id": cc_id,
                        "pair_id": pair.get("pair_id"),
                        "pair_cc_id": pair.get("cc_id"),
                    }
                )

        mappings = cc_mappings_by_speech.get(speech_id, [])
        if len(mappings) != 1:
            cc_mapping_mismatches.append(
                {
                    "speech_id": speech_id,
                    "reason": "Expected exactly one local-CC mapping.",
                    "mapping_count": len(mappings),
                }
            )
        else:
            mapping = mappings[0]
            mapping_type = _relationship_type_name(
                mapping.get("relationship_type"),
                allowed_relationship_types,
            )
            mismatch_fields = []
            if mapping.get("canonical_cc_id") != cc_id:
                mismatch_fields.append("canonical_cc_id")
            if mapping_type != relationship_type:
                mismatch_fields.append("relationship_type")
            if _normalise_whitespace(
                mapping.get("relationship_explanation", "")
            ) != explanation:
                mismatch_fields.append("relationship_explanation")
            if (
                mapping.get("classification_prompt_version")
                != config.classification_prompt_version
            ):
                mismatch_fields.append("classification_prompt_version")
            if (
                mapping.get("classification_schema_version")
                != config.classification_schema_version
            ):
                mismatch_fields.append("classification_schema_version")
            if mismatch_fields:
                cc_mapping_mismatches.append(
                    {
                        "speech_id": speech_id,
                        "mismatch_fields": mismatch_fields,
                    }
                )

    for item in uncategorised:
        reasons = item.get("classification_rejection_reasons", []) or []
        if not reasons:
            uncategorised_without_rejection_reason.append(
                {
                    "speech_id": item.get("speech_id"),
                    "filename": item.get("filename"),
                }
            )
        for reason in reasons:
            rejection_reason_distribution[_normalise_whitespace(reason)] += 1

        if (
            item.get("classification_prompt_version")
            != config.classification_prompt_version
            or item.get("classification_schema_version")
            != config.classification_schema_version
        ):
            classification_version_mismatches.append(
                {
                    "speech_id": item.get("speech_id"),
                    "prompt_version": item.get(
                        "classification_prompt_version"
                    ),
                    "schema_version": item.get(
                        "classification_schema_version"
                    ),
                }
            )
        if item.get("primary_cc_relationship_type") not in (None, "", "NONE"):
            invalid_relationship_types.append(
                {
                    "speech_id": item.get("speech_id"),
                    "filename": item.get("filename"),
                    "value": item.get("primary_cc_relationship_type"),
                    "status": "uncategorised",
                }
            )

    below_confidence = [
        {
            "speech_id": item.get("speech_id"),
            "filename": item.get("filename"),
            "confidence": float(
                item.get("primary_cc_confidence", 0.0)
            ),
        }
        for item in categorised
        if float(item.get("primary_cc_confidence", 0.0))
        < config.classification_confidence_min
    ]

    semantic = {
        "skipped": True,
        "interpretation": (
            "Assigned-CC embedding similarity is a diagnostic only. Under the "
            "argumentative-home classifier, mechanisms, applications, "
            "qualifications, opposition, and historical examples need not "
            "paraphrase the complete canonical Central Claim."
        ),
    }
    if model is not None and categorised:
        triples = []
        for item in categorised:
            source = inventory_by_speech.get(item.get("speech_id"))
            cc = cc_by_id.get(item.get("primary_cc_id"))
            if (
                source
                and cc
                and source.get("central_claim")
                and cc.get("claim")
            ):
                triples.append(
                    (item, source["central_claim"], cc["claim"])
                )

        local_texts = [item[1] for item in triples]
        assigned_texts = [item[2] for item in triples]
        local_embeddings = _encode(model, local_texts)
        assigned_embeddings = _encode(model, assigned_texts)
        assigned_similarities = np.sum(
            local_embeddings * assigned_embeddings,
            axis=1,
        )

        all_cc_ids = [
            item.get("cc_id") for item in data.canonical_ccs
        ]
        all_cc_embeddings = _encode(
            model,
            [item.get("claim", "") for item in data.canonical_ccs],
        )
        matrix = (
            local_embeddings @ all_cc_embeddings.T
            if len(all_cc_embeddings)
            else np.empty((len(triples), 0))
        )

        low_alignment = []
        non_best_assignments = []
        assignment_gaps = []
        similarities_by_relationship_type = defaultdict(list)
        for index, (
            classification,
            local_text,
            _assigned_text,
        ) in enumerate(triples):
            assigned_similarity = float(
                assigned_similarities[index]
            )
            relationship_type = _relationship_type_name(
                classification.get(
                    "primary_cc_relationship_type"
                ),
                allowed_relationship_types,
            )
            if relationship_type:
                similarities_by_relationship_type[
                    relationship_type
                ].append(assigned_similarity)

            best_index = (
                int(np.argmax(matrix[index]))
                if matrix.shape[1]
                else -1
            )
            best_similarity = (
                float(matrix[index, best_index])
                if best_index >= 0
                else assigned_similarity
            )
            best_cc_id = (
                all_cc_ids[best_index]
                if best_index >= 0
                else classification.get("primary_cc_id")
            )
            gap = assigned_similarity - best_similarity
            assignment_gaps.append(gap)
            if assigned_similarity < LOW_ASSIGNED_CC_SIMILARITY:
                low_alignment.append(
                    {
                        "speech_id": classification.get(
                            "speech_id"
                        ),
                        "filename": classification.get(
                            "filename"
                        ),
                        "assigned_cc_id": classification.get(
                            "primary_cc_id"
                        ),
                        "relationship_type": relationship_type,
                        "assigned_similarity": round(
                            assigned_similarity,
                            6,
                        ),
                        "local_central_claim": local_text,
                    }
                )
            if best_cc_id != classification.get(
                "primary_cc_id"
            ):
                non_best_assignments.append(
                    {
                        "speech_id": classification.get(
                            "speech_id"
                        ),
                        "assigned_cc_id": classification.get(
                            "primary_cc_id"
                        ),
                        "relationship_type": relationship_type,
                        "embedding_best_cc_id": best_cc_id,
                        "assigned_similarity": round(
                            assigned_similarity,
                            6,
                        ),
                        "best_similarity": round(
                            best_similarity,
                            6,
                        ),
                        "gap": round(gap, 6),
                    }
                )

        silhouette_value = None
        labels = [
            item[0].get("primary_cc_id") for item in triples
        ]
        unique_labels = set(labels)
        if (
            len(triples) >= 3
            and 2 <= len(unique_labels) < len(triples)
        ):
            try:
                silhouette_value = float(
                    silhouette_score(
                        local_embeddings,
                        labels,
                        metric="cosine",
                    )
                )
            except Exception as exc:
                warnings.append(
                    "Silhouette score could not be computed: "
                    + str(exc)
                )

        semantic = {
            "mapped_speech_count": len(triples),
            "assigned_cc_similarity": _summary_stats(
                assigned_similarities.tolist()
            ),
            "assigned_cc_similarity_by_relationship_type": {
                relationship_type: _summary_stats(values)
                for relationship_type, values
                in sorted(
                    similarities_by_relationship_type.items()
                )
            },
            "assignment_gap_vs_embedding_best": _summary_stats(
                assignment_gaps
            ),
            "low_alignment_threshold": LOW_ASSIGNED_CC_SIMILARITY,
            "low_alignment_count": len(low_alignment),
            "low_alignment_records": low_alignment,
            "embedding_best_differs_count": len(
                non_best_assignments
            ),
            "embedding_best_differs_records": (
                non_best_assignments
            ),
            "silhouette_score_cosine": (
                round(silhouette_value, 6)
                if silhouette_value is not None
                else None
            ),
            "interpretation": (
                "These metrics measure propositional embedding "
                "proximity, not whether the selected chapter is the "
                "best argumentative home. Lower similarity can be "
                "legitimate for mechanisms, applications, "
                "qualifications, opposition, or historical examples."
            ),
        }

    theme_mapping_confidences = [
        float(item.get("confidence", 0.0))
        for item in data.mappings
        if item.get("mapping_type")
        == "local_theme_to_canonical_theme"
        and item.get("canonical_theme_id")
    ]
    low_theme_mappings = [
        item
        for item in data.mappings
        if item.get("mapping_type")
        == "local_theme_to_canonical_theme"
        and item.get("canonical_theme_id")
        and float(item.get("confidence", 0.0))
        < config.theme_mapping_confidence_min
    ]

    if invalid_cc:
        errors.append(
            "Categorised speeches reference invalid CC IDs."
        )
    if invalid_themes:
        errors.append(
            "Categorised speeches reference invalid Theme IDs."
        )
    if invalid_memberships:
        errors.append(
            "Default pair memberships do not exactly match "
            "primary CC x assigned Themes."
        )
    if cross_cc_default_memberships:
        errors.append(
            "Default memberships cross the speech's primary CC."
        )
    if invalid_relationship_types:
        errors.append(
            "Classifications contain invalid or missing controlled "
            "speech-to-CC relationship types."
        )
    if missing_relationship_explanations:
        errors.append(
            "Some categorised speeches lack a nonempty "
            "speech-to-chapter relationship explanation."
        )
    if classification_version_mismatches:
        errors.append(
            "Classification records do not use the configured "
            "classification prompt/schema versions."
        )
    if cc_mapping_mismatches:
        errors.append(
            "Local-CC mapping records do not preserve the "
            "classification relationship fields exactly."
        )
    if below_confidence:
        warnings.append(
            "Some categorised speeches fall below the configured "
            "CC confidence minimum."
        )
    if low_theme_mappings:
        warnings.append(
            "Some selected Theme mappings fall below the configured "
            "Theme confidence minimum."
        )
    if uncategorised_without_rejection_reason:
        warnings.append(
            "Some uncategorised speeches have no explicit "
            "classification rejection reason."
        )

    return {
        "classification_record_count": len(
            data.classifications
        ),
        "categorised_count": len(categorised),
        "uncategorised_count": len(uncategorised),
        "categorisation_rate_pct": round(
            _safe_pct(
                len(categorised),
                len(data.classifications),
            ),
            4,
        ),
        "primary_cc_confidence": _summary_stats(
            confidences
        ),
        "classification_confidence_min": (
            config.classification_confidence_min
        ),
        "classification_prompt_version": (
            config.classification_prompt_version
        ),
        "classification_schema_version": (
            config.classification_schema_version
        ),
        "allowed_relationship_types": list(
            allowed_relationship_types
        ),
        "relationship_type_distribution": {
            key: relationship_type_distribution.get(key, 0)
            for key in allowed_relationship_types
        },
        "relationship_type_by_cc": {
            cc_id: {
                key: counts.get(key, 0)
                for key in allowed_relationship_types
            }
            for cc_id, counts in sorted(
                relationship_type_by_cc.items()
            )
        },
        "nonaffirmative_classification_count": (
            relationship_type_distribution.get(
                "qualification",
                0,
            )
            + relationship_type_distribution.get(
                "opposition",
                0,
            )
        ),
        "invalid_relationship_types": (
            invalid_relationship_types
        ),
        "missing_relationship_explanations": (
            missing_relationship_explanations
        ),
        "classification_version_mismatches": (
            classification_version_mismatches
        ),
        "local_cc_mapping_mismatches": (
            cc_mapping_mismatches
        ),
        "uncategorised_rejection_reason_distribution": dict(
            rejection_reason_distribution
        ),
        "uncategorised_without_rejection_reason": (
            uncategorised_without_rejection_reason
        ),
        "below_confidence_count": len(below_confidence),
        "below_confidence_records": below_confidence,
        "theme_mapping_confidence": _summary_stats(
            theme_mapping_confidences
        ),
        "theme_mapping_confidence_min": (
            config.theme_mapping_confidence_min
        ),
        "low_theme_mapping_count": len(
            low_theme_mappings
        ),
        "invalid_primary_cc_references": invalid_cc,
        "invalid_theme_references": invalid_themes,
        "invalid_theme_assignment_counts": (
            invalid_theme_counts
        ),
        "duplicate_theme_assignments": (
            duplicate_theme_assignments
        ),
        "invalid_default_pair_memberships": (
            invalid_memberships
        ),
        "cross_cc_default_memberships": (
            cross_cc_default_memberships
        ),
        "secondary_contribution_count": len(
            data.secondary_contributions
        ),
        "semantic_alignment": semantic,
        "errors": errors,
        "warnings": warnings,
        "status": "PASS" if not errors else "FAIL",
    }


# ═════════════════════════════════════════════════════════════════════════════
# Metric 4 — usage distributions
# ═════════════════════════════════════════════════════════════════════════════


def usage_distributions(data: EvaluationData) -> Dict[str, Any]:
    cc_labels = {item.get("cc_id"): item.get("claim", "") for item in data.canonical_ccs}
    theme_labels = {item.get("theme_id"): item.get("theme", "") for item in data.canonical_themes}
    pair_labels = {
        item.get("pair_id"): "{0} x {1}".format(item.get("cc_id"), item.get("theme_id"))
        for item in data.pairs
    }

    categorised = [item for item in data.classifications if item.get("status") == "categorised"]
    cc_counts = Counter(item.get("primary_cc_id") for item in categorised if item.get("primary_cc_id"))
    theme_counts = Counter()
    pair_membership_counts = Counter()
    for item in categorised:
        theme_counts.update(item.get("theme_ids", []) or [])
        pair_membership_counts.update(
            membership.get("pair_id")
            for membership in (item.get("bucket_memberships", []) or [])
            if membership.get("pair_id")
        )

    cc_report = _distribution_report(cc_counts, cc_labels, len(data.canonical_ccs))
    theme_report = _distribution_report(theme_counts, theme_labels, len(data.canonical_themes))
    pair_report = _distribution_report(pair_membership_counts, pair_labels, len(data.pairs))

    warnings = []
    if cc_report["per_entity"] and cc_report["per_entity"][0]["pct"] > DOMINANT_CC_PCT:
        warnings.append(
            "Dominant CC {0} contains {1:.2f}% of categorised speeches.".format(
                cc_report["per_entity"][0]["id"], cc_report["per_entity"][0]["pct"]
            )
        )
    if pair_report["per_entity"] and pair_report["per_entity"][0]["pct"] > DOMINANT_PAIR_PCT:
        warnings.append(
            "Dominant pair {0} contains {1:.2f}% of pair memberships.".format(
                pair_report["per_entity"][0]["id"], pair_report["per_entity"][0]["pct"]
            )
        )

    return {
        "canonical_cc_usage": cc_report,
        "canonical_theme_usage": theme_report,
        "pair_membership_usage": pair_report,
        "warnings": warnings,
    }


# ═════════════════════════════════════════════════════════════════════════════
# Metric 5 — authoritative pair and Theme-sharing structure
# ═════════════════════════════════════════════════════════════════════════════


def pair_and_theme_structure(
    data: EvaluationData,
    config: PipelineConfig,
) -> Dict[str, Any]:
    valid_cc_ids = {
        item.get("cc_id") for item in data.canonical_ccs
    }
    valid_theme_ids = {
        item.get("theme_id") for item in data.canonical_themes
    }
    valid_speech_ids = {
        item.get("speech_id") for item in data.inventory
    }
    allowed_relationship_types = tuple(
        config.primary_cc_relationship_types
    )

    pair_ids = [
        item.get("pair_id") for item in data.pairs
    ]
    pair_keys = [
        (item.get("cc_id"), item.get("theme_id"))
        for item in data.pairs
    ]
    duplicate_pair_ids = [
        value
        for value, count in Counter(pair_ids).items()
        if count > 1
    ]
    duplicate_pair_keys = [
        {"cc_id": value[0], "theme_id": value[1]}
        for value, count in Counter(pair_keys).items()
        if count > 1
    ]

    classification_by_speech = {
        item.get("speech_id"): item
        for item in data.classifications
    }
    expected_sources_by_pair = defaultdict(set)
    expected_relationship_sources_by_pair = defaultdict(
        lambda: defaultdict(set)
    )
    for classification in data.classifications:
        if classification.get("status") != "categorised":
            continue
        speech_id = classification.get("speech_id")
        cc_id = classification.get("primary_cc_id")
        relationship_type = _relationship_type_name(
            classification.get(
                "primary_cc_relationship_type"
            ),
            allowed_relationship_types,
        )
        for theme_id in classification.get("theme_ids", []) or []:
            pair_id = "PAIR-{0}-{1}".format(cc_id, theme_id)
            expected_sources_by_pair[pair_id].add(speech_id)
            if relationship_type:
                expected_relationship_sources_by_pair[
                    pair_id
                ][relationship_type].add(speech_id)

    invalid_pairs = []
    invalid_source_speech_ids = []
    empty_pairs = []
    pair_source_mismatches = []
    pair_relationship_source_mismatches = []
    pair_relationship_count_mismatches = []
    invalid_pair_relationship_types = []

    for pair in data.pairs:
        pair_id = pair.get("pair_id")
        if (
            pair.get("cc_id") not in valid_cc_ids
            or pair.get("theme_id") not in valid_theme_ids
        ):
            invalid_pairs.append(pair)

        actual_sources = set(
            pair.get("source_speech_ids", []) or []
        )
        bad_sources = [
            speech_id
            for speech_id in actual_sources
            if speech_id not in valid_speech_ids
        ]
        if bad_sources:
            invalid_source_speech_ids.append(
                {
                    "pair_id": pair_id,
                    "speech_ids": sorted(bad_sources),
                }
            )
        expected_sources = expected_sources_by_pair.get(
            pair_id,
            set(),
        )
        if actual_sources != expected_sources:
            pair_source_mismatches.append(
                {
                    "pair_id": pair_id,
                    "expected_source_speech_ids": sorted(
                        expected_sources
                    ),
                    "actual_source_speech_ids": sorted(
                        actual_sources
                    ),
                }
            )

        raw_role_sources = (
            pair.get("relationship_type_speech_ids", {})
            or {}
        )
        actual_role_sources = {}
        for raw_type, speech_ids in raw_role_sources.items():
            relationship_type = _relationship_type_name(
                raw_type,
                allowed_relationship_types,
            )
            if relationship_type is None:
                invalid_pair_relationship_types.append(
                    {
                        "pair_id": pair_id,
                        "relationship_type": raw_type,
                    }
                )
                continue
            actual_role_sources[relationship_type] = set(
                speech_ids or []
            )

        expected_role_sources = {
            relationship_type: set(speech_ids)
            for relationship_type, speech_ids
            in expected_relationship_sources_by_pair.get(
                pair_id,
                {},
            ).items()
        }
        if actual_role_sources != expected_role_sources:
            pair_relationship_source_mismatches.append(
                {
                    "pair_id": pair_id,
                    "expected": {
                        key: sorted(value)
                        for key, value in sorted(
                            expected_role_sources.items()
                        )
                    },
                    "actual": {
                        key: sorted(value)
                        for key, value in sorted(
                            actual_role_sources.items()
                        )
                    },
                }
            )

        actual_counts = {
            key: int(value)
            for key, value in (
                pair.get("relationship_type_counts", {})
                or {}
            ).items()
        }
        expected_counts = {
            key: len(value)
            for key, value in expected_role_sources.items()
        }
        if actual_counts != expected_counts:
            pair_relationship_count_mismatches.append(
                {
                    "pair_id": pair_id,
                    "expected": expected_counts,
                    "actual": actual_counts,
                }
            )

        if (
            not pair.get("source_speech_ids")
            and not pair.get("source_contribution_ids")
        ):
            empty_pairs.append(pair_id)

    theme_to_ccs = defaultdict(set)
    cc_to_themes = defaultdict(set)
    for pair in data.pairs:
        theme_to_ccs[pair.get("theme_id")].add(
            pair.get("cc_id")
        )
        cc_to_themes[pair.get("cc_id")].add(
            pair.get("theme_id")
        )

    shared_themes = []
    for theme in data.canonical_themes:
        theme_id = theme.get("theme_id")
        cc_ids = sorted(
            value
            for value in theme_to_ccs.get(
                theme_id,
                set(),
            )
            if value
        )
        if len(cc_ids) > 1:
            shared_themes.append(
                {
                    "theme_id": theme_id,
                    "theme": theme.get("theme", ""),
                    "cc_count": len(cc_ids),
                    "cc_ids": cc_ids,
                }
            )
    shared_themes.sort(
        key=lambda item: (
            -item["cc_count"],
            item["theme_id"],
        )
    )

    unused_themes = sorted(
        valid_theme_ids - set(theme_to_ccs)
    )
    ccs_without_pairs = sorted(
        valid_cc_ids - set(cc_to_themes)
    )
    possible_pairs = (
        len(valid_cc_ids) * len(valid_theme_ids)
    )
    pair_density = (
        len(data.pairs) / float(possible_pairs)
        if possible_pairs
        else 0.0
    )

    relationship_pair_distribution = Counter()
    for pair in data.pairs:
        for relationship_type in (
            pair.get("relationship_type_speech_ids", {})
            or {}
        ):
            normalised = _relationship_type_name(
                relationship_type,
                allowed_relationship_types,
            )
            if normalised:
                relationship_pair_distribution[
                    normalised
                ] += 1

    errors = []
    warnings = []
    if duplicate_pair_ids:
        errors.append("Duplicate pair IDs exist.")
    if duplicate_pair_keys:
        errors.append(
            "Duplicate CC x Theme relationships exist."
        )
    if invalid_pairs:
        errors.append(
            "Some pairs reference invalid canonical entities."
        )
    if invalid_source_speech_ids:
        errors.append(
            "Some pairs reference unknown source speech IDs."
        )
    if pair_source_mismatches:
        errors.append(
            "Persistent pair source-speech lists do not exactly "
            "match the current classifications."
        )
    if (
        invalid_pair_relationship_types
        or pair_relationship_source_mismatches
        or pair_relationship_count_mismatches
    ):
        errors.append(
            "Persistent pairs do not deterministically preserve "
            "classification relationship-type aggregation."
        )
    if empty_pairs:
        warnings.append(
            "Some persistent pairs have no current source "
            "speeches or contributions."
        )
    if unused_themes:
        warnings.append(
            "Some canonical Themes have no observed persistent pair."
        )
    if ccs_without_pairs:
        warnings.append(
            "Some canonical CCs have no observed persistent pair."
        )

    return {
        "pair_count": len(data.pairs),
        "possible_pair_count": possible_pairs,
        "pair_density": round(pair_density, 8),
        "duplicate_pair_ids": duplicate_pair_ids,
        "duplicate_pair_relationships": duplicate_pair_keys,
        "invalid_pairs": invalid_pairs,
        "invalid_source_speech_ids": (
            invalid_source_speech_ids
        ),
        "pair_source_speech_mismatches": (
            pair_source_mismatches
        ),
        "invalid_pair_relationship_types": (
            invalid_pair_relationship_types
        ),
        "pair_relationship_source_mismatches": (
            pair_relationship_source_mismatches
        ),
        "pair_relationship_count_mismatches": (
            pair_relationship_count_mismatches
        ),
        "relationship_type_pair_distribution": {
            key: relationship_pair_distribution.get(key, 0)
            for key in allowed_relationship_types
        },
        "empty_pair_ids": empty_pairs,
        "shared_theme_count": len(shared_themes),
        "shared_theme_rate": round(
            _safe_pct(
                len(shared_themes),
                len(data.canonical_themes),
            )
            / 100.0,
            8,
        ),
        "shared_themes": shared_themes,
        "unused_theme_ids": unused_themes,
        "cc_ids_without_pairs": ccs_without_pairs,
        "themes_per_cc": _summary_stats(
            [len(value) for value in cc_to_themes.values()]
        ),
        "ccs_per_used_theme": _summary_stats(
            [
                len(value)
                for value in theme_to_ccs.values()
            ]
        ),
        "errors": errors,
        "warnings": warnings,
        "status": "PASS" if not errors else "FAIL",
    }


# ═════════════════════════════════════════════════════════════════════════════
# Metric 6 — lossless remap and contribution coverage
# ═════════════════════════════════════════════════════════════════════════════


def _count_local_arguments(record: Dict[str, Any]) -> int:
    return sum(
        len(theme.get("arguments", []) or [])
        for theme in record.get("themes", []) or []
    )


def lossless_remap_quality(
    data: EvaluationData,
    config: PipelineConfig,
) -> Dict[str, Any]:
    inventory_by_speech = {
        item.get("speech_id"): item
        for item in data.inventory
    }
    phase4_by_speech = {
        item.get("speech_id"): item
        for item in data.phase4_records
    }
    classification_by_speech = {
        item.get("speech_id"): item
        for item in data.classifications
    }
    pair_ids = {
        item.get("pair_id") for item in data.pairs
    }
    allowed_relationship_types = tuple(
        config.primary_cc_relationship_types
    )

    missing_remapped = sorted(
        set(inventory_by_speech) - set(phase4_by_speech)
    )
    extra_remapped = sorted(
        set(phase4_by_speech) - set(inventory_by_speech)
    )
    changed_fields = []
    phase1_hash_mismatches = []
    canonical_mapping_mismatches = []
    orphan_contributions = []
    contribution_relationship_mismatches = []
    contribution_ids = []
    categorized_argument_total = 0
    mapped_argument_total = 0
    source_contribution_total = 0
    unmapped_argument_total = 0
    uncategorised_argument_total = 0
    relationship_propagation_checked = 0
    relationship_propagation_valid = 0

    preserved_fields = (
        "speech_id",
        "filename",
        "stem",
        "date",
        "source_hash",
        "central_claim",
        "themes",
        "unverifiable_claims",
        "claims_inventory",
    )

    for speech_id in sorted(
        set(inventory_by_speech) & set(phase4_by_speech)
    ):
        source = inventory_by_speech[speech_id]
        remapped = phase4_by_speech[speech_id]
        for field_name in preserved_fields:
            if source.get(field_name) != remapped.get(
                field_name
            ):
                changed_fields.append(
                    {
                        "speech_id": speech_id,
                        "filename": source.get("filename"),
                        "field": field_name,
                    }
                )
        if (
            remapped.get("phase1_record_hash")
            != source.get("record_hash")
        ):
            phase1_hash_mismatches.append(speech_id)

        source_classification = classification_by_speech.get(
            speech_id,
            {},
        )
        if (
            remapped.get("canonical_mapping")
            != source_classification
        ):
            canonical_mapping_mismatches.append(speech_id)

        local_argument_count = _count_local_arguments(source)
        mapping = remapped.get("canonical_mapping", {})
        contributions = (
            remapped.get("source_contributions", [])
            or []
        )
        unmapped = remapped.get("unmapped_arguments", []) or []
        contribution_ids.extend(
            item.get("contribution_id")
            for item in contributions
        )

        expected_type = _relationship_type_name(
            source_classification.get(
                "primary_cc_relationship_type"
            ),
            allowed_relationship_types,
        )
        expected_explanation = _normalise_whitespace(
            source_classification.get(
                "primary_cc_relationship_explanation",
                "",
            )
        )
        expected_confidence = float(
            source_classification.get(
                "primary_cc_confidence",
                0.0,
            )
        )

        for contribution in contributions:
            if contribution.get("pair_id") not in pair_ids:
                orphan_contributions.append(
                    {
                        "speech_id": speech_id,
                        "contribution_id": contribution.get(
                            "contribution_id"
                        ),
                        "pair_id": contribution.get(
                            "pair_id"
                        ),
                    }
                )

            relationship_propagation_checked += 1
            mismatch_fields = []
            actual_type = _relationship_type_name(
                contribution.get(
                    "primary_cc_relationship_type"
                ),
                allowed_relationship_types,
            )
            if actual_type != expected_type:
                mismatch_fields.append(
                    "primary_cc_relationship_type"
                )
            if _normalise_whitespace(
                contribution.get(
                    "primary_cc_relationship_explanation",
                    "",
                )
            ) != expected_explanation:
                mismatch_fields.append(
                    "primary_cc_relationship_explanation"
                )
            try:
                actual_confidence = float(
                    contribution.get(
                        "primary_cc_confidence",
                        0.0,
                    )
                )
            except (TypeError, ValueError):
                actual_confidence = float("nan")
            if (
                not math.isfinite(actual_confidence)
                or abs(
                    actual_confidence - expected_confidence
                ) > 1e-12
            ):
                mismatch_fields.append(
                    "primary_cc_confidence"
                )
            if (
                contribution.get(
                    "classification_prompt_version"
                )
                != config.classification_prompt_version
            ):
                mismatch_fields.append(
                    "classification_prompt_version"
                )
            if (
                contribution.get(
                    "classification_schema_version"
                )
                != config.classification_schema_version
            ):
                mismatch_fields.append(
                    "classification_schema_version"
                )

            if mismatch_fields:
                contribution_relationship_mismatches.append(
                    {
                        "speech_id": speech_id,
                        "contribution_id": contribution.get(
                            "contribution_id"
                        ),
                        "mismatch_fields": mismatch_fields,
                    }
                )
            else:
                relationship_propagation_valid += 1

        if mapping.get("status") == "categorised":
            categorized_argument_total += (
                local_argument_count
            )
            mapped_local_argument_ids = {
                contribution.get("local_argument_id")
                for contribution in contributions
                if contribution.get("local_argument_id")
            }
            unmapped_local_argument_ids = {
                item.get("local_argument_id")
                for item in unmapped
                if item.get("local_argument_id")
            }
            mapped_argument_total += len(
                mapped_local_argument_ids
            )
            source_contribution_total += len(
                contributions
            )
            unmapped_argument_total += len(
                unmapped_local_argument_ids
            )
        else:
            uncategorised_argument_total += (
                local_argument_count
            )

    duplicate_contribution_ids = [
        value
        for value, count in Counter(
            value for value in contribution_ids if value
        ).items()
        if count > 1
    ]
    categorized_coverage = _safe_pct(
        mapped_argument_total + unmapped_argument_total,
        categorized_argument_total,
    )
    mapped_rate = _safe_pct(
        mapped_argument_total,
        categorized_argument_total,
    )
    relationship_propagation_pct = _safe_pct(
        relationship_propagation_valid,
        relationship_propagation_checked,
    )

    errors = []
    warnings = []
    if missing_remapped:
        errors.append(
            "Inventory speeches are missing Phase 4 "
            "remapped records."
        )
    if extra_remapped:
        errors.append(
            "Phase 4 contains records absent from the inventory."
        )
    if changed_fields:
        errors.append(
            "Phase 4 changed source-level fields and is not "
            "lossless."
        )
    if phase1_hash_mismatches:
        errors.append(
            "Phase 4 phase1_record_hash values do not match "
            "inventory records."
        )
    if canonical_mapping_mismatches:
        errors.append(
            "Phase 4 canonical_mapping differs from the "
            "Phase 3 classification."
        )
    if orphan_contributions:
        errors.append(
            "Some source contributions reference nonexistent pairs."
        )
    if duplicate_contribution_ids:
        errors.append(
            "Duplicate source contribution IDs exist."
        )
    if contribution_relationship_mismatches:
        errors.append(
            "Some source contributions do not preserve the "
            "speech-to-chapter relationship fields and "
            "classification versions exactly."
        )
    if (
        categorized_argument_total
        and categorized_coverage < 100.0
    ):
        errors.append(
            "Some categorised local arguments are neither "
            "mapped nor explicitly flagged unmapped."
        )
    if unmapped_argument_total:
        warnings.append(
            "Some categorised local arguments remain explicitly "
            "unmapped."
        )

    return {
        "inventory_record_count": len(data.inventory),
        "phase4_record_count": len(data.phase4_records),
        "missing_remapped_speech_ids": missing_remapped,
        "extra_remapped_speech_ids": extra_remapped,
        "changed_source_fields": changed_fields,
        "phase1_record_hash_mismatches": (
            phase1_hash_mismatches
        ),
        "canonical_mapping_mismatches": (
            canonical_mapping_mismatches
        ),
        "duplicate_contribution_ids": (
            duplicate_contribution_ids
        ),
        "orphan_contributions": orphan_contributions,
        "contribution_relationship_mismatches": (
            contribution_relationship_mismatches
        ),
        "relationship_propagation_checked_count": (
            relationship_propagation_checked
        ),
        "relationship_propagation_valid_count": (
            relationship_propagation_valid
        ),
        "relationship_propagation_pct": round(
            relationship_propagation_pct,
            6,
        ),
        "categorised_local_argument_count": (
            categorized_argument_total
        ),
        "mapped_local_argument_count": (
            mapped_argument_total
        ),
        "source_contribution_count": (
            source_contribution_total
        ),
        "explicitly_unmapped_argument_count": (
            unmapped_argument_total
        ),
        "uncategorised_local_argument_count": (
            uncategorised_argument_total
        ),
        "categorised_argument_accounting_pct": round(
            categorized_coverage,
            6,
        ),
        "categorised_argument_mapped_pct": round(
            mapped_rate,
            6,
        ),
        "errors": errors,
        "warnings": warnings,
        "status": "PASS" if not errors else "FAIL",
    }


# ═════════════════════════════════════════════════════════════════════════════
# Metric 7 — pair synthesis and provenance
# ═════════════════════════════════════════════════════════════════════════════


def pair_synthesis_provenance(
    data: EvaluationData,
    config: PipelineConfig,
) -> Dict[str, Any]:
    pair_map = {
        item.get("pair_id"): item for item in data.pairs
    }
    allowed_relationship_types = tuple(
        config.primary_cc_relationship_types
    )
    nonaffirmative_types = {
        "qualification",
        "opposition",
    }

    contribution_map = {}
    contribution_ids_by_pair = defaultdict(set)
    filename_by_contribution = {}
    for record in data.phase4_records:
        for contribution in (
            record.get("source_contributions", [])
            or []
        ):
            contribution_id = contribution.get(
                "contribution_id"
            )
            if not contribution_id:
                continue
            contribution_map[contribution_id] = contribution
            contribution_ids_by_pair[
                contribution.get("pair_id")
            ].add(contribution_id)
            filename_by_contribution[
                contribution_id
            ] = contribution.get("filename")

    invalid_bucket_pairs = []
    invalid_argument_ownership = []
    source_free_arguments = []
    invalid_argument_contributions = []
    invalid_argument_filenames = []
    source_free_evidence = []
    invalid_evidence_contributions = []
    source_free_devices = []
    argument_ids = []
    referenced_contributions = set()
    pair_table_argument_mismatches = []
    pair_table_contribution_mismatches = []
    synthesis_contribution_mismatches = []
    pair_table_source_speech_mismatches = []

    invalid_relationship_roles = []
    role_coverage_mismatches = []
    role_filename_mismatches = []
    role_explanation_mismatches = []
    nonaffirmative_rendering_mismatches = []
    relationship_role_distribution = Counter()
    arguments_with_valid_relationship_roles = 0

    nonempty_pair_ids = {
        pair_id
        for pair_id, contribution_ids
        in contribution_ids_by_pair.items()
        if contribution_ids
    }
    bucket_pair_ids = set(data.bucket_syntheses)
    missing_bucket_pairs = sorted(
        nonempty_pair_ids - bucket_pair_ids
    )
    extra_bucket_pairs = sorted(
        bucket_pair_ids - set(pair_map)
    )

    argument_count = 0
    evidence_count = 0
    device_count = 0
    arguments_with_valid_provenance = 0
    evidence_with_valid_provenance = 0
    devices_with_valid_provenance = 0

    for pair_id, synthesis in data.bucket_syntheses.items():
        if pair_id not in pair_map:
            invalid_bucket_pairs.append(pair_id)
            continue

        if (
            synthesis.get("bucket_prompt_version")
            != config.bucket_prompt_version
            or synthesis.get("bucket_schema_version")
            != config.bucket_schema_version
        ):
            invalid_bucket_pairs.append(
                {
                    "pair_id": pair_id,
                    "reason": "bucket prompt/schema version mismatch",
                }
            )

        pair_valid_contributions = (
            contribution_ids_by_pair.get(
                pair_id,
                set(),
            )
        )
        pair_table_contribution_ids = set(
            pair_map[pair_id].get(
                "source_contribution_ids",
                [],
            )
            or []
        )
        if (
            pair_table_contribution_ids
            != pair_valid_contributions
        ):
            pair_table_contribution_mismatches.append(
                {
                    "pair_id": pair_id,
                    "known_contribution_ids": sorted(
                        pair_valid_contributions
                    ),
                    "pair_table_contribution_ids": sorted(
                        pair_table_contribution_ids
                    ),
                }
            )

        synthesis_contribution_ids = set(
            synthesis.get("source_contribution_ids", [])
            or []
        )
        if (
            synthesis_contribution_ids
            != pair_valid_contributions
        ):
            synthesis_contribution_mismatches.append(
                {
                    "pair_id": pair_id,
                    "known_contribution_ids": sorted(
                        pair_valid_contributions
                    ),
                    "synthesis_contribution_ids": sorted(
                        synthesis_contribution_ids
                    ),
                }
            )

        expected_source_speech_ids = {
            contribution_map[value].get("speech_id")
            for value in pair_valid_contributions
            if (
                value in contribution_map
                and contribution_map[value].get("speech_id")
            )
        }
        pair_table_source_speech_ids = set(
            pair_map[pair_id].get(
                "source_speech_ids",
                [],
            )
            or []
        )
        if (
            pair_table_source_speech_ids
            != expected_source_speech_ids
        ):
            pair_table_source_speech_mismatches.append(
                {
                    "pair_id": pair_id,
                    "expected_source_speech_ids": sorted(
                        expected_source_speech_ids
                    ),
                    "pair_table_source_speech_ids": sorted(
                        pair_table_source_speech_ids
                    ),
                }
            )

        synthesis_argument_ids = []
        for argument in (
            synthesis.get("arguments", []) or []
        ):
            argument_count += 1
            argument_id = argument.get("argument_id")
            argument_ids.append(argument_id)
            synthesis_argument_ids.append(argument_id)

            if argument.get("pair_id") != pair_id:
                invalid_argument_ownership.append(
                    {
                        "argument_id": argument_id,
                        "synthesis_pair_id": pair_id,
                        "argument_pair_id": argument.get(
                            "pair_id"
                        ),
                    }
                )

            source_ids = set(
                argument.get(
                    "source_contribution_ids",
                    [],
                )
                or []
            )
            filenames = set(
                argument.get(
                    "source_speech_filenames",
                    [],
                )
                or []
            )
            if not source_ids or not filenames:
                source_free_arguments.append(argument_id)
            bad_source_ids = sorted(
                source_ids - pair_valid_contributions
            )
            if bad_source_ids:
                invalid_argument_contributions.append(
                    {
                        "argument_id": argument_id,
                        "invalid_contribution_ids": (
                            bad_source_ids
                        ),
                    }
                )
            expected_filenames = {
                filename_by_contribution.get(value)
                for value in source_ids
                if filename_by_contribution.get(value)
            }
            if filenames != expected_filenames:
                invalid_argument_filenames.append(
                    {
                        "argument_id": argument_id,
                        "expected_filenames": sorted(
                            expected_filenames
                        ),
                        "actual_filenames": sorted(
                            filenames
                        ),
                    }
                )
            if (
                source_ids
                and filenames
                and not bad_source_ids
                and filenames == expected_filenames
            ):
                arguments_with_valid_provenance += 1
                referenced_contributions.update(source_ids)

            expected_role_groups = defaultdict(set)
            expected_role_filenames = defaultdict(set)
            expected_role_explanations = defaultdict(set)
            for contribution_id in source_ids:
                contribution = contribution_map.get(
                    contribution_id
                )
                if not contribution:
                    continue
                relationship_type = _relationship_type_name(
                    contribution.get(
                        "primary_cc_relationship_type"
                    ),
                    allowed_relationship_types,
                )
                if relationship_type is None:
                    continue
                expected_role_groups[
                    relationship_type
                ].add(contribution_id)
                if contribution.get("filename"):
                    expected_role_filenames[
                        relationship_type
                    ].add(contribution.get("filename"))
                explanation = _normalise_whitespace(
                    contribution.get(
                        "primary_cc_relationship_explanation",
                        "",
                    )
                )
                if explanation:
                    expected_role_explanations[
                        relationship_type
                    ].add(explanation)

            actual_role_groups = defaultdict(set)
            seen_role_contribution_ids = []
            relationship_roles = (
                argument.get("relationship_roles", [])
                or []
            )
            for role in relationship_roles:
                relationship_type = _relationship_type_name(
                    role.get("relationship_type"),
                    allowed_relationship_types,
                )
                if relationship_type is None:
                    invalid_relationship_roles.append(
                        {
                            "argument_id": argument_id,
                            "relationship_type": role.get(
                                "relationship_type"
                            ),
                        }
                    )
                    continue
                relationship_role_distribution[
                    relationship_type
                ] += 1
                role_source_ids = set(
                    role.get(
                        "source_contribution_ids",
                        [],
                    )
                    or []
                )
                seen_role_contribution_ids.extend(
                    role_source_ids
                )
                actual_role_groups[
                    relationship_type
                ].update(role_source_ids)

                expected_role_source_ids = (
                    expected_role_groups.get(
                        relationship_type,
                        set(),
                    )
                )
                if (
                    role_source_ids
                    != expected_role_source_ids
                ):
                    invalid_relationship_roles.append(
                        {
                            "argument_id": argument_id,
                            "relationship_type": (
                                relationship_type
                            ),
                            "expected_contribution_ids": sorted(
                                expected_role_source_ids
                            ),
                            "actual_contribution_ids": sorted(
                                role_source_ids
                            ),
                        }
                    )

                actual_role_filenames = set(
                    role.get(
                        "source_speech_filenames",
                        [],
                    )
                    or []
                )
                if (
                    actual_role_filenames
                    != expected_role_filenames.get(
                        relationship_type,
                        set(),
                    )
                ):
                    role_filename_mismatches.append(
                        {
                            "argument_id": argument_id,
                            "relationship_type": (
                                relationship_type
                            ),
                            "expected": sorted(
                                expected_role_filenames.get(
                                    relationship_type,
                                    set(),
                                )
                            ),
                            "actual": sorted(
                                actual_role_filenames
                            ),
                        }
                    )

                actual_explanations = {
                    _normalise_whitespace(value)
                    for value in (
                        role.get(
                            "relationship_explanations",
                            [],
                        )
                        or []
                    )
                    if _normalise_whitespace(value)
                }
                if (
                    actual_explanations
                    != expected_role_explanations.get(
                        relationship_type,
                        set(),
                    )
                ):
                    role_explanation_mismatches.append(
                        {
                            "argument_id": argument_id,
                            "relationship_type": (
                                relationship_type
                            ),
                            "expected": sorted(
                                expected_role_explanations.get(
                                    relationship_type,
                                    set(),
                                )
                            ),
                            "actual": sorted(
                                actual_explanations
                            ),
                        }
                    )

            duplicate_role_contribution_ids = [
                value
                for value, count in Counter(
                    seen_role_contribution_ids
                ).items()
                if count > 1
            ]
            if (
                actual_role_groups != expected_role_groups
                or duplicate_role_contribution_ids
            ):
                role_coverage_mismatches.append(
                    {
                        "argument_id": argument_id,
                        "expected": {
                            key: sorted(value)
                            for key, value in sorted(
                                expected_role_groups.items()
                            )
                        },
                        "actual": {
                            key: sorted(value)
                            for key, value in sorted(
                                actual_role_groups.items()
                            )
                        },
                        "duplicate_role_contribution_ids": (
                            duplicate_role_contribution_ids
                        ),
                    }
                )
            else:
                arguments_with_valid_relationship_roles += 1

            disagreements = [
                _normalise_whitespace(value)
                for value in (
                    argument.get(
                        "disagreements_or_qualifications",
                        [],
                    )
                    or []
                )
                if _normalise_whitespace(value)
            ]
            disagreements_text = " ".join(
                disagreements
            ).lower()
            for relationship_type in nonaffirmative_types:
                if relationship_type not in expected_role_groups:
                    continue
                label = _relationship_type_label(
                    relationship_type
                ).lower()
                readable = relationship_type.replace(
                    "_",
                    " ",
                )
                if (
                    not disagreements
                    or (
                        label not in disagreements_text
                        and readable not in disagreements_text
                    )
                ):
                    nonaffirmative_rendering_mismatches.append(
                        {
                            "argument_id": argument_id,
                            "relationship_type": (
                                relationship_type
                            ),
                            "disagreements_or_qualifications": (
                                disagreements
                            ),
                        }
                    )

            for evidence in (
                argument.get("evidence", []) or []
            ):
                evidence_count += 1
                evidence_source_ids = set(
                    evidence.get(
                        "source_contribution_ids",
                        [],
                    )
                    or []
                )
                evidence_filenames = set(
                    evidence.get(
                        "source_speech_filenames",
                        [],
                    )
                    or []
                )
                if (
                    not evidence_source_ids
                    or not evidence_filenames
                ):
                    source_free_evidence.append(
                        {
                            "argument_id": argument_id,
                            "item": evidence.get("item", ""),
                        }
                    )
                bad_evidence_ids = sorted(
                    evidence_source_ids
                    - pair_valid_contributions
                )
                if bad_evidence_ids:
                    invalid_evidence_contributions.append(
                        {
                            "argument_id": argument_id,
                            "item": evidence.get("item", ""),
                            "invalid_contribution_ids": (
                                bad_evidence_ids
                            ),
                        }
                    )
                expected_evidence_filenames = {
                    filename_by_contribution.get(value)
                    for value in evidence_source_ids
                    if filename_by_contribution.get(value)
                }
                if (
                    evidence_source_ids
                    and evidence_filenames
                    and not bad_evidence_ids
                    and evidence_filenames
                    == expected_evidence_filenames
                ):
                    evidence_with_valid_provenance += 1
                    referenced_contributions.update(
                        evidence_source_ids
                    )

            for device in (
                argument.get(
                    "rhetorical_devices",
                    [],
                )
                or []
            ):
                device_count += 1
                device_source_ids = set(
                    device.get(
                        "source_contribution_ids",
                        [],
                    )
                    or []
                )
                device_filenames = set(
                    device.get(
                        "source_speech_filenames",
                        [],
                    )
                    or []
                )
                if (
                    not device_source_ids
                    or not device_filenames
                ):
                    source_free_devices.append(
                        {
                            "argument_id": argument_id,
                            "device": device.get(
                                "device",
                                "",
                            ),
                        }
                    )
                bad_device_ids = (
                    device_source_ids
                    - pair_valid_contributions
                )
                expected_device_filenames = {
                    filename_by_contribution.get(value)
                    for value in device_source_ids
                    if filename_by_contribution.get(value)
                }
                if (
                    device_source_ids
                    and device_filenames
                    and not bad_device_ids
                    and device_filenames
                    == expected_device_filenames
                ):
                    devices_with_valid_provenance += 1
                    referenced_contributions.update(
                        device_source_ids
                    )

        pair_argument_ids = set(
            pair_map[pair_id].get(
                "canonical_argument_conclusion_ids",
                [],
            )
            or []
        )
        if pair_argument_ids != set(
            synthesis_argument_ids
        ):
            pair_table_argument_mismatches.append(
                {
                    "pair_id": pair_id,
                    "pair_table_argument_ids": sorted(
                        pair_argument_ids
                    ),
                    "synthesis_argument_ids": sorted(
                        value
                        for value in synthesis_argument_ids
                        if value
                    ),
                }
            )

    duplicate_argument_ids = [
        value
        for value, count in Counter(
            value for value in argument_ids if value
        ).items()
        if count > 1
    ]
    all_contribution_ids = set(contribution_map)
    unreferenced_contributions = sorted(
        all_contribution_ids
        - referenced_contributions
    )

    errors = []
    warnings = []
    if missing_bucket_pairs:
        errors.append(
            "Nonempty persistent pairs are missing Phase 5 "
            "syntheses."
        )
    if extra_bucket_pairs or invalid_bucket_pairs:
        errors.append(
            "Phase 5 contains syntheses for unknown pairs or "
            "uses stale bucket versions."
        )
    if invalid_argument_ownership:
        errors.append(
            "Canonical arguments are not owned by their "
            "synthesis pair."
        )
    if (
        source_free_arguments
        or invalid_argument_contributions
        or invalid_argument_filenames
    ):
        errors.append(
            "Some canonical arguments lack valid provenance."
        )
    if (
        source_free_evidence
        or invalid_evidence_contributions
    ):
        errors.append(
            "Some evidence items lack valid provenance."
        )
    if duplicate_argument_ids:
        errors.append(
            "Canonical argument IDs are not globally unique."
        )
    if pair_table_argument_mismatches:
        errors.append(
            "Pair argument-ID lists do not match bucket syntheses."
        )
    if pair_table_contribution_mismatches:
        errors.append(
            "Persistent pair source-contribution lists do not "
            "match Phase 4 contributions."
        )
    if synthesis_contribution_mismatches:
        errors.append(
            "Bucket synthesis source-contribution lists do not "
            "match Phase 4 contributions."
        )
    if pair_table_source_speech_mismatches:
        errors.append(
            "Persistent pair source-speech lists do not match "
            "Phase 4 contributions."
        )
    if (
        invalid_relationship_roles
        or role_coverage_mismatches
        or role_filename_mismatches
        or role_explanation_mismatches
    ):
        errors.append(
            "Canonical argument relationship-role summaries do "
            "not exactly preserve their source contributions."
        )
    if nonaffirmative_rendering_mismatches:
        errors.append(
            "Some qualification or opposition contributions are "
            "not explicitly retained in disagreements or "
            "qualifications."
        )
    if unreferenced_contributions:
        warnings.append(
            "Some Phase 4 source contributions are not cited by "
            "any canonical argument, evidence item, or device."
        )

    return {
        "known_source_contribution_count": len(
            all_contribution_ids
        ),
        "bucket_synthesis_count": len(
            data.bucket_syntheses
        ),
        "bucket_prompt_version": (
            config.bucket_prompt_version
        ),
        "bucket_schema_version": (
            config.bucket_schema_version
        ),
        "missing_bucket_pair_ids": missing_bucket_pairs,
        "extra_bucket_pair_ids": extra_bucket_pairs,
        "invalid_bucket_pair_ids": invalid_bucket_pairs,
        "canonical_argument_count": argument_count,
        "canonical_argument_valid_provenance_pct": round(
            _safe_pct(
                arguments_with_valid_provenance,
                argument_count,
            ),
            6,
        ),
        "canonical_argument_valid_relationship_roles_pct": round(
            _safe_pct(
                arguments_with_valid_relationship_roles,
                argument_count,
            ),
            6,
        ),
        "relationship_role_distribution": {
            key: relationship_role_distribution.get(key, 0)
            for key in allowed_relationship_types
        },
        "invalid_relationship_roles": (
            invalid_relationship_roles
        ),
        "role_coverage_mismatches": (
            role_coverage_mismatches
        ),
        "role_filename_mismatches": (
            role_filename_mismatches
        ),
        "role_explanation_mismatches": (
            role_explanation_mismatches
        ),
        "nonaffirmative_rendering_mismatches": (
            nonaffirmative_rendering_mismatches
        ),
        "evidence_item_count": evidence_count,
        "evidence_valid_provenance_pct": round(
            _safe_pct(
                evidence_with_valid_provenance,
                evidence_count,
            ),
            6,
        ),
        "rhetorical_device_count": device_count,
        "rhetorical_device_valid_provenance_pct": round(
            _safe_pct(
                devices_with_valid_provenance,
                device_count,
            ),
            6,
        ),
        "source_free_argument_ids": source_free_arguments,
        "invalid_argument_ownership": (
            invalid_argument_ownership
        ),
        "invalid_argument_contributions": (
            invalid_argument_contributions
        ),
        "invalid_argument_filenames": (
            invalid_argument_filenames
        ),
        "source_free_evidence": source_free_evidence,
        "invalid_evidence_contributions": (
            invalid_evidence_contributions
        ),
        "source_free_rhetorical_devices": (
            source_free_devices
        ),
        "duplicate_argument_ids": duplicate_argument_ids,
        "pair_table_argument_mismatches": (
            pair_table_argument_mismatches
        ),
        "pair_table_contribution_mismatches": (
            pair_table_contribution_mismatches
        ),
        "synthesis_contribution_mismatches": (
            synthesis_contribution_mismatches
        ),
        "pair_table_source_speech_mismatches": (
            pair_table_source_speech_mismatches
        ),
        "referenced_source_contribution_count": len(
            referenced_contributions
        ),
        "source_contribution_reference_coverage_pct": round(
            _safe_pct(
                len(referenced_contributions),
                len(all_contribution_ids),
            ),
            6,
        ),
        "unreferenced_source_contribution_ids": (
            unreferenced_contributions
        ),
        "errors": errors,
        "warnings": warnings,
        "status": "PASS" if not errors else "FAIL",
    }


# ═════════════════════════════════════════════════════════════════════════════
# Metric 8 — publication and index integrity
# ═════════════════════════════════════════════════════════════════════════════


def _extract_html_anchors(markdown: str) -> List[str]:
    return re.findall(r'<a\s+id="([^"]+)"\s*></a>', markdown)


def _extract_compendium_pair_ids(markdown: str) -> List[str]:
    return re.findall(r"\*\*Canonical pair ID:\*\*\s*`([^`]+)`", markdown)


def _extract_theme_index_pair_ids(markdown: str) -> List[str]:
    return re.findall(r"^- Pair ID:\s*`([^`]+)`\s*$", markdown, flags=re.MULTILINE)


def _extract_theme_index_theme_ids(markdown: str) -> List[str]:
    return re.findall(r"\*\*Canonical Theme ID:\*\*\s*`([^`]+)`", markdown)


def _extract_theme_index_compendium_anchors(markdown: str) -> List[str]:
    return re.findall(r"compendium\.md#([A-Za-z0-9_-]+)", markdown)


def _extract_cross_index_section(markdown: str) -> str:
    marker = "# Theme Cross-Index"
    position = markdown.find(marker)
    return markdown[position:] if position >= 0 else ""


def _extract_cross_index_anchors(markdown: str) -> List[str]:
    section = _extract_cross_index_section(markdown)
    return re.findall(r"\]\(#([A-Za-z0-9_-]+)\)", section)


def _extract_model_versions(markdown: str) -> List[str]:
    return re.findall(r"\*\*Canonical model version:\*\*\s*`([^`]+)`", markdown)


def publication_and_index_integrity(
    data: EvaluationData,
) -> Dict[str, Any]:
    pair_ids = [
        item.get("pair_id") for item in data.pairs
    ]
    pair_id_set = set(pair_ids)
    pair_anchor_map = {
        item.get("pair_id"): item.get(
            "authoritative_anchor"
        )
        for item in data.pairs
    }
    expected_anchors = {
        value
        for value in pair_anchor_map.values()
        if value
    }

    compendium_anchors = _extract_html_anchors(
        data.compendium_text
    )
    compendium_anchor_counts = Counter(
        compendium_anchors
    )
    pair_anchor_counts = {
        anchor: compendium_anchor_counts.get(anchor, 0)
        for anchor in expected_anchors
    }
    missing_compendium_anchors = sorted(
        anchor
        for anchor, count in pair_anchor_counts.items()
        if count == 0
    )
    duplicate_compendium_pair_anchors = sorted(
        anchor
        for anchor, count in pair_anchor_counts.items()
        if count > 1
    )

    compendium_pair_ids = _extract_compendium_pair_ids(
        data.compendium_text
    )
    theme_index_pair_ids = _extract_theme_index_pair_ids(
        data.theme_index_text
    )
    theme_index_theme_ids = _extract_theme_index_theme_ids(
        data.theme_index_text
    )
    theme_index_anchors = (
        _extract_theme_index_compendium_anchors(
            data.theme_index_text
        )
    )
    cross_index_anchors = _extract_cross_index_anchors(
        data.compendium_text
    )

    expected_shared_pair_anchors = set()
    theme_to_pairs = defaultdict(list)
    for pair in data.pairs:
        theme_to_pairs[pair.get("theme_id")].append(pair)
    for pair_list in theme_to_pairs.values():
        if len(pair_list) > 1:
            expected_shared_pair_anchors.update(
                pair.get("authoritative_anchor")
                for pair in pair_list
                if pair.get("authoritative_anchor")
            )

    canonical_theme_ids = {
        item.get("theme_id")
        for item in data.canonical_themes
    }
    compendium_versions = _extract_model_versions(
        data.compendium_text
    )
    theme_index_versions = _extract_model_versions(
        data.theme_index_text
    )
    canonical_model_version = data.manifests.get(
        "phase3",
        {},
    ).get("canonical_model_version")

    canonical_argument_count = sum(
        len(synthesis.get("arguments", []) or [])
        for synthesis in data.bucket_syntheses.values()
    )
    relationship_role_heading_count = (
        data.compendium_text.count(
            "#### Speech-to-Chapter Relationship Roles"
        )
    )

    errors = []
    warnings = []
    if missing_compendium_anchors:
        errors.append(
            "Persistent pair anchors are missing from "
            "compendium.md."
        )
    if duplicate_compendium_pair_anchors:
        errors.append(
            "Persistent pair anchors occur more than once in "
            "compendium.md."
        )
    if Counter(compendium_pair_ids) != Counter(pair_ids):
        errors.append(
            "compendium.md does not render every persistent pair "
            "exactly once."
        )
    if Counter(theme_index_pair_ids) != Counter(pair_ids):
        errors.append(
            "theme_index.md does not list every persistent pair "
            "exactly once."
        )
    if (
        set(theme_index_theme_ids) != canonical_theme_ids
        or len(theme_index_theme_ids)
        != len(canonical_theme_ids)
    ):
        errors.append(
            "theme_index.md does not represent every canonical "
            "Theme exactly once."
        )
    if set(theme_index_anchors) != expected_anchors:
        errors.append(
            "theme_index.md anchor links do not exactly match "
            "persistent pair anchors."
        )
    if (
        set(cross_index_anchors)
        != expected_shared_pair_anchors
    ):
        errors.append(
            "The compendium Theme Cross-Index does not exactly "
            "represent shared pairs."
        )
    if not _extract_cross_index_section(
        data.compendium_text
    ):
        errors.append(
            "compendium.md has no Theme Cross-Index section."
        )
    if (
        relationship_role_heading_count
        != canonical_argument_count
    ):
        errors.append(
            "compendium.md does not render exactly one "
            "Speech-to-Chapter Relationship Roles subsection "
            "for every canonical argument."
        )
    if canonical_model_version:
        if compendium_versions != [
            canonical_model_version
        ]:
            errors.append(
                "compendium.md canonical model version is absent, "
                "duplicated, or stale."
            )
        if theme_index_versions != [
            canonical_model_version
        ]:
            errors.append(
                "theme_index.md canonical model version is "
                "absent, duplicated, or stale."
            )
    if (
        data.integrity_report
        and data.integrity_report.get("status") != "PASS"
    ):
        warnings.append(
            "The pipeline's own integrity_report.json does not "
            "report PASS."
        )

    return {
        "persistent_pair_count": len(data.pairs),
        "expected_pair_anchor_count": len(
            expected_anchors
        ),
        "compendium_total_anchor_count": len(
            compendium_anchors
        ),
        "missing_compendium_pair_anchors": (
            missing_compendium_anchors
        ),
        "duplicate_compendium_pair_anchors": (
            duplicate_compendium_pair_anchors
        ),
        "compendium_pair_id_count": len(
            compendium_pair_ids
        ),
        "theme_index_pair_id_count": len(
            theme_index_pair_ids
        ),
        "theme_index_theme_id_count": len(
            theme_index_theme_ids
        ),
        "theme_index_anchor_reference_count": len(
            theme_index_anchors
        ),
        "expected_shared_cross_index_anchor_count": len(
            expected_shared_pair_anchors
        ),
        "actual_shared_cross_index_anchor_count": len(
            cross_index_anchors
        ),
        "canonical_argument_count": canonical_argument_count,
        "relationship_role_heading_count": (
            relationship_role_heading_count
        ),
        "missing_theme_index_pair_ids": sorted(
            pair_id_set - set(theme_index_pair_ids)
        ),
        "extra_theme_index_pair_ids": sorted(
            set(theme_index_pair_ids) - pair_id_set
        ),
        "missing_cross_index_anchors": sorted(
            expected_shared_pair_anchors
            - set(cross_index_anchors)
        ),
        "extra_cross_index_anchors": sorted(
            set(cross_index_anchors)
            - expected_shared_pair_anchors
        ),
        "canonical_model_version": canonical_model_version,
        "compendium_model_versions": compendium_versions,
        "theme_index_model_versions": theme_index_versions,
        "pipeline_integrity_report_status": (
            data.integrity_report.get("status")
        ),
        "pipeline_integrity_checks": (
            data.integrity_report.get("checks", {})
        ),
        "errors": errors,
        "warnings": warnings,
        "status": "PASS" if not errors else "FAIL",
    }


# ═════════════════════════════════════════════════════════════════════════════
# Metric 9 — unverifiable-claim completeness
# ═════════════════════════════════════════════════════════════════════════════


def _status_name(value: Any) -> str:
    clean = _normalise_whitespace(value).lower()
    if clean in {"verified", "✅ verified", "✅"}:
        return "Verified"
    if clean in {"disputed", "❌ disputed", "❌"}:
        return "Disputed"
    return "Unverifiable"


def _expected_unverifiable_records(remapped_records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    collected = []
    for record in remapped_records:
        for claim in record.get("unverifiable_claims", []) or []:
            collected.append(
                {
                    "record_type": "explicit_unverifiable_claim",
                    "speech_ref": claim.get("speech_ref", record.get("filename", "")),
                    "claim": claim.get("claim", ""),
                    "reason": claim.get("reason", ""),
                    "memory_check": claim.get("memory_check", "NoInternalBasis"),
                    "memory_note": claim.get("memory_note", ""),
                    "source_excerpt": claim.get("source_excerpt", ""),
                    "source_match": bool(claim.get("source_match")),
                    "source_location": claim.get("source_location"),
                }
            )
        for theme in record.get("themes", []) or []:
            for argument in theme.get("arguments", []) or []:
                for evidence in argument.get("evidence", []) or []:
                    if _status_name(evidence.get("status")) != "Unverifiable":
                        continue
                    collected.append(
                        {
                            "record_type": "unverifiable_evidence_item",
                            "speech_ref": evidence.get("source_speech_filename", record.get("filename", "")),
                            "claim": evidence.get("item", ""),
                            "reason": evidence.get("verification_basis", ""),
                            "memory_check": "NoInternalBasis",
                            "memory_note": "Evidence workflow status; no separate MEMORY assessment was requested for this item.",
                            "source_excerpt": evidence.get("source_excerpt", ""),
                            "source_match": bool(evidence.get("source_match")),
                            "source_location": evidence.get("source_location"),
                        }
                    )

    by_key = {}
    for item in collected:
        key = (item.get("speech_ref", ""), item.get("claim", ""))
        current = by_key.get(key)
        if current is None:
            by_key[key] = item
        elif (
            current.get("record_type") != "explicit_unverifiable_claim"
            and item.get("record_type") == "explicit_unverifiable_claim"
        ):
            by_key[key] = item
    return sorted(by_key.values(), key=lambda item: (item.get("speech_ref", ""), item.get("claim", "")))


def _parse_published_unverifiable(markdown: str) -> List[Dict[str, str]]:
    records = []
    current = {}
    for line in markdown.splitlines():
        match = re.match(r"- \*\*(TYPE|SPEECH_REF|CLAIM|REASON|MEMORY):\*\*\s*(.*)$", line)
        if not match:
            continue
        key = match.group(1).lower()
        value = match.group(2).strip().strip("`")
        if key == "type" and current:
            if current.get("speech_ref") is not None and current.get("claim") is not None:
                records.append(current)
            current = {}
        current[key] = value
    if current and current.get("speech_ref") is not None and current.get("claim") is not None:
        records.append(current)
    return records


def unverifiable_claim_completeness(data: EvaluationData) -> Dict[str, Any]:
    expected = _expected_unverifiable_records(data.phase4_records)
    published = _parse_published_unverifiable(data.unverifiable_text)
    expected_by_key = {(item["speech_ref"], item["claim"]): item for item in expected}
    published_by_key = {(item.get("speech_ref", ""), item.get("claim", "")): item for item in published}
    missing = sorted(expected_by_key.keys() - published_by_key.keys())
    extra = sorted(published_by_key.keys() - expected_by_key.keys())
    duplicate_published = [
        {"speech_ref": key[0], "claim": key[1], "count": count}
        for key, count in Counter((item.get("speech_ref", ""), item.get("claim", "")) for item in published).items()
        if count > 1
    ]
    explicit_count = sum(1 for item in expected if item.get("record_type") == "explicit_unverifiable_claim")
    evidence_count = sum(1 for item in expected if item.get("record_type") == "unverifiable_evidence_item")
    memory_counts = Counter(item.get("memory_check", "NoInternalBasis") for item in expected)
    source_match_count = sum(1 for item in expected if item.get("source_match"))
    corroborated_expected = {
        key for key, item in expected_by_key.items() if item.get("memory_check") == "Corroborated"
    }
    corroborated_missing = sorted(corroborated_expected - published_by_key.keys())

    errors = []
    warnings = []
    if missing:
        errors.append("Expected unverifiable records are missing from unverifiable_claims.md.")
    if extra:
        errors.append("unverifiable_claims.md contains records not reconstructed from Phase 4.")
    if duplicate_published:
        errors.append("unverifiable_claims.md contains duplicate speech-reference/claim records.")
    if corroborated_missing:
        errors.append("MEMORY: Corroborated records were improperly omitted.")
    if expected and source_match_count < len(expected):
        warnings.append("Some unverifiable records lack an exact source-excerpt match.")

    return {
        "expected_unique_record_count": len(expected),
        "published_unique_record_count": len(published_by_key),
        "explicit_unverifiable_claim_count": explicit_count,
        "unverifiable_evidence_item_count": evidence_count,
        "memory_distribution": dict(memory_counts),
        "source_match_count": source_match_count,
        "source_match_rate_pct": round(_safe_pct(source_match_count, len(expected)), 6),
        "missing_records": [
            {"speech_ref": key[0], "claim": key[1]} for key in missing
        ],
        "extra_records": [
            {"speech_ref": key[0], "claim": key[1]} for key in extra
        ],
        "duplicate_published_records": duplicate_published,
        "missing_corroborated_records": [
            {"speech_ref": key[0], "claim": key[1]} for key in corroborated_missing
        ],
        "errors": errors,
        "warnings": warnings,
        "status": "PASS" if not errors else "FAIL",
    }


# ═════════════════════════════════════════════════════════════════════════════
# Metric 10 — canonical-version and stale-checkpoint consistency
# ═════════════════════════════════════════════════════════════════════════════


def version_and_staleness_consistency(
    data: EvaluationData,
    config: PipelineConfig,
) -> Dict[str, Any]:
    phase3_manifest = data.manifests.get("phase3", {})
    phase4_manifest = data.manifests.get("phase4", {})
    phase5_manifest = data.manifests.get("phase5", {})
    phase3_version = phase3_manifest.get(
        "canonical_model_version"
    )
    phase4_version = phase4_manifest.get(
        "canonical_model_version"
    )
    phase5_version = phase5_manifest.get(
        "canonical_model_version"
    )
    allowed_relationship_types = list(
        config.primary_cc_relationship_types
    )

    version_mismatches = []
    if phase3_version:
        for phase, value in (
            ("phase4", phase4_version),
            ("phase5", phase5_version),
        ):
            if value != phase3_version:
                version_mismatches.append(
                    {
                        "phase": phase,
                        "expected": phase3_version,
                        "actual": value,
                    }
                )

    phase4_record_mismatches = [
        {
            "speech_id": record.get("speech_id"),
            "filename": record.get("filename"),
            "canonical_model_version": record.get(
                "canonical_model_version"
            ),
        }
        for record in data.phase4_records
        if (
            phase3_version
            and record.get("canonical_model_version")
            != phase3_version
        )
    ]
    bucket_version_mismatches = [
        {
            "pair_id": pair_id,
            "canonical_model_version": synthesis.get(
                "canonical_model_version"
            ),
        }
        for pair_id, synthesis
        in data.bucket_syntheses.items()
        if (
            phase3_version
            and synthesis.get("canonical_model_version")
            != phase3_version
        )
    ]
    pair_version_mismatches = [
        {
            "pair_id": pair.get("pair_id"),
            "canonical_model_version": pair.get(
                "canonical_model_version"
            ),
        }
        for pair in data.pairs
        if (
            phase3_version
            and pair.get("canonical_model_version")
            != phase3_version
        )
    ]

    schema_mismatches = []
    prompt_mismatches = []
    classification_version_mismatches = []
    bucket_prompt_schema_mismatches = []
    relationship_vocabulary_mismatches = []

    for phase, manifest in data.manifests.items():
        if (
            manifest
            and manifest.get("schema_version")
            != config.schema_version
        ):
            schema_mismatches.append(
                {
                    "artefact": phase + " manifest",
                    "actual": manifest.get("schema_version"),
                }
            )
        if (
            manifest
            and manifest.get("prompt_version")
            != config.prompt_version
        ):
            prompt_mismatches.append(
                {
                    "artefact": phase + " manifest",
                    "actual": manifest.get("prompt_version"),
                }
            )

        configuration = manifest.get(
            "configuration",
            {},
        ) if manifest else {}
        if configuration:
            if (
                configuration.get(
                    "classification_prompt_version"
                )
                != config.classification_prompt_version
                or configuration.get(
                    "classification_schema_version"
                )
                != config.classification_schema_version
            ):
                classification_version_mismatches.append(
                    {
                        "artefact": phase + " manifest configuration",
                        "prompt_version": configuration.get(
                            "classification_prompt_version"
                        ),
                        "schema_version": configuration.get(
                            "classification_schema_version"
                        ),
                    }
                )
            if (
                configuration.get("bucket_prompt_version")
                != config.bucket_prompt_version
                or configuration.get("bucket_schema_version")
                != config.bucket_schema_version
            ):
                bucket_prompt_schema_mismatches.append(
                    {
                        "artefact": phase + " manifest configuration",
                        "prompt_version": configuration.get(
                            "bucket_prompt_version"
                        ),
                        "schema_version": configuration.get(
                            "bucket_schema_version"
                        ),
                    }
                )
            if (
                configuration.get(
                    "primary_cc_relationship_types"
                )
                != allowed_relationship_types
            ):
                relationship_vocabulary_mismatches.append(
                    {
                        "artefact": phase + " manifest configuration",
                        "actual": configuration.get(
                            "primary_cc_relationship_types"
                        ),
                    }
                )

    if phase3_manifest:
        if (
            phase3_manifest.get(
                "classification_prompt_version"
            )
            != config.classification_prompt_version
            or phase3_manifest.get(
                "classification_schema_version"
            )
            != config.classification_schema_version
        ):
            classification_version_mismatches.append(
                {
                    "artefact": "phase3 manifest",
                    "prompt_version": phase3_manifest.get(
                        "classification_prompt_version"
                    ),
                    "schema_version": phase3_manifest.get(
                        "classification_schema_version"
                    ),
                }
            )
        if (
            phase3_manifest.get(
                "primary_cc_relationship_types"
            )
            != allowed_relationship_types
        ):
            relationship_vocabulary_mismatches.append(
                {
                    "artefact": "phase3 manifest",
                    "actual": phase3_manifest.get(
                        "primary_cc_relationship_types"
                    ),
                }
            )

    for record in data.phase1_records:
        if (
            record.get("schema_version")
            != config.schema_version
        ):
            schema_mismatches.append(
                {
                    "artefact": record.get("filename"),
                    "actual": record.get("schema_version"),
                }
            )
        if (
            record.get("prompt_version")
            != config.prompt_version
        ):
            prompt_mismatches.append(
                {
                    "artefact": record.get("filename"),
                    "actual": record.get("prompt_version"),
                }
            )

    for classification in data.classifications:
        if (
            classification.get(
                "classification_prompt_version"
            )
            != config.classification_prompt_version
            or classification.get(
                "classification_schema_version"
            )
            != config.classification_schema_version
        ):
            classification_version_mismatches.append(
                {
                    "artefact": "classification "
                    + str(classification.get("speech_id")),
                    "prompt_version": classification.get(
                        "classification_prompt_version"
                    ),
                    "schema_version": classification.get(
                        "classification_schema_version"
                    ),
                }
            )

    for mapping in data.mappings:
        if (
            mapping.get("mapping_type")
            == "local_cc_to_canonical_cc"
            and (
                mapping.get(
                    "classification_prompt_version"
                )
                != config.classification_prompt_version
                or mapping.get(
                    "classification_schema_version"
                )
                != config.classification_schema_version
            )
        ):
            classification_version_mismatches.append(
                {
                    "artefact": "local-CC mapping "
                    + str(mapping.get("speech_id")),
                    "prompt_version": mapping.get(
                        "classification_prompt_version"
                    ),
                    "schema_version": mapping.get(
                        "classification_schema_version"
                    ),
                }
            )

    for record in data.phase4_records:
        if (
            record.get("schema_version")
            != config.schema_version
        ):
            schema_mismatches.append(
                {
                    "artefact": record.get("filename"),
                    "actual": record.get("schema_version"),
                }
            )
        if (
            record.get("prompt_version")
            != config.prompt_version
        ):
            prompt_mismatches.append(
                {
                    "artefact": record.get("filename"),
                    "actual": record.get("prompt_version"),
                }
            )
        mapping = record.get("canonical_mapping", {})
        if (
            mapping.get("classification_prompt_version")
            != config.classification_prompt_version
            or mapping.get("classification_schema_version")
            != config.classification_schema_version
        ):
            classification_version_mismatches.append(
                {
                    "artefact": "Phase 4 mapping "
                    + str(record.get("speech_id")),
                    "prompt_version": mapping.get(
                        "classification_prompt_version"
                    ),
                    "schema_version": mapping.get(
                        "classification_schema_version"
                    ),
                }
            )
        for contribution in (
            record.get("source_contributions", [])
            or []
        ):
            if (
                contribution.get(
                    "classification_prompt_version"
                )
                != config.classification_prompt_version
                or contribution.get(
                    "classification_schema_version"
                )
                != config.classification_schema_version
            ):
                classification_version_mismatches.append(
                    {
                        "artefact": "source contribution "
                        + str(
                            contribution.get(
                                "contribution_id"
                            )
                        ),
                        "prompt_version": contribution.get(
                            "classification_prompt_version"
                        ),
                        "schema_version": contribution.get(
                            "classification_schema_version"
                        ),
                    }
                )

    for pair_id, synthesis in data.bucket_syntheses.items():
        if (
            synthesis.get("schema_version")
            != config.schema_version
        ):
            schema_mismatches.append(
                {
                    "artefact": "bucket " + str(pair_id),
                    "actual": synthesis.get("schema_version"),
                }
            )
        if (
            synthesis.get("prompt_version")
            != config.prompt_version
        ):
            prompt_mismatches.append(
                {
                    "artefact": "bucket " + str(pair_id),
                    "actual": synthesis.get("prompt_version"),
                }
            )
        if (
            synthesis.get("bucket_prompt_version")
            != config.bucket_prompt_version
            or synthesis.get("bucket_schema_version")
            != config.bucket_schema_version
        ):
            bucket_prompt_schema_mismatches.append(
                {
                    "artefact": "bucket " + str(pair_id),
                    "prompt_version": synthesis.get(
                        "bucket_prompt_version"
                    ),
                    "schema_version": synthesis.get(
                        "bucket_schema_version"
                    ),
                }
            )

    wrapper_dependency_mismatches = []
    inventory_by_speech = {
        item.get("speech_id"): item
        for item in data.inventory
    }
    expected_mapping_configuration = {
        "classification_confidence_min": (
            config.classification_confidence_min
        ),
        "theme_mapping_confidence_min": (
            config.theme_mapping_confidence_min
        ),
        "max_themes_per_speech": (
            config.max_themes_per_speech
        ),
        "allow_secondary_cc_contributions": (
            config.allow_secondary_cc_contributions
        ),
    }
    for filename, wrapper in data.phase4_wrappers.items():
        record = wrapper.get("record", {})
        dependencies = wrapper.get("dependencies", {})
        source = inventory_by_speech.get(
            record.get("speech_id"),
            {},
        )
        expected = {
            "source_hash": source.get("source_hash"),
            "phase1_record_hash": source.get("record_hash"),
            "canonical_model_version": phase3_version,
            "schema_version": config.schema_version,
            "prompt_version": config.prompt_version,
            "classification_prompt_version": (
                config.classification_prompt_version
            ),
            "classification_schema_version": (
                config.classification_schema_version
            ),
            "primary_cc_relationship_types": (
                allowed_relationship_types
            ),
            "mapping_configuration": (
                expected_mapping_configuration
            ),
        }
        actual = {
            key: dependencies.get(key) for key in expected
        }
        if actual != expected:
            wrapper_dependency_mismatches.append(
                {
                    "checkpoint": filename,
                    "expected": expected,
                    "actual": actual,
                }
            )

    incomplete_wrappers = []
    for filename, wrapper in (
        list(data.phase1_wrappers.items())
        + list(data.phase4_wrappers.items())
        + list(data.bucket_wrappers.items())
    ):
        if not wrapper.get("complete"):
            incomplete_wrappers.append(filename)

    errors = []
    warnings = []
    if (
        version_mismatches
        or phase4_record_mismatches
        or bucket_version_mismatches
        or pair_version_mismatches
    ):
        errors.append(
            "Canonical model versions are inconsistent across "
            "dependent artefacts."
        )
    if schema_mismatches:
        errors.append(
            "Base schema versions do not match the current "
            "pipeline configuration."
        )
    if prompt_mismatches:
        errors.append(
            "Base prompt versions do not match the current "
            "pipeline configuration."
        )
    if classification_version_mismatches:
        errors.append(
            "Classification prompt/schema versions are stale or "
            "inconsistent."
        )
    if bucket_prompt_schema_mismatches:
        errors.append(
            "Bucket prompt/schema versions are stale or "
            "inconsistent."
        )
    if relationship_vocabulary_mismatches:
        errors.append(
            "The controlled speech-to-CC relationship vocabulary "
            "is stale or inconsistent."
        )
    if wrapper_dependency_mismatches:
        errors.append(
            "Phase 4 checkpoint dependencies are stale or "
            "malformed."
        )
    if incomplete_wrappers:
        warnings.append(
            "Some checkpoint wrappers are not marked complete."
        )

    return {
        "configured_schema_version": config.schema_version,
        "configured_prompt_version": config.prompt_version,
        "configured_classification_prompt_version": (
            config.classification_prompt_version
        ),
        "configured_classification_schema_version": (
            config.classification_schema_version
        ),
        "configured_bucket_prompt_version": (
            config.bucket_prompt_version
        ),
        "configured_bucket_schema_version": (
            config.bucket_schema_version
        ),
        "configured_relationship_types": (
            allowed_relationship_types
        ),
        "phase3_canonical_model_version": phase3_version,
        "phase4_canonical_model_version": phase4_version,
        "phase5_canonical_model_version": phase5_version,
        "manifest_version_mismatches": (
            version_mismatches
        ),
        "phase4_record_version_mismatches": (
            phase4_record_mismatches
        ),
        "pair_version_mismatches": pair_version_mismatches,
        "bucket_version_mismatches": (
            bucket_version_mismatches
        ),
        "schema_mismatches": schema_mismatches,
        "prompt_mismatches": prompt_mismatches,
        "classification_version_mismatches": (
            classification_version_mismatches
        ),
        "bucket_prompt_schema_mismatches": (
            bucket_prompt_schema_mismatches
        ),
        "relationship_vocabulary_mismatches": (
            relationship_vocabulary_mismatches
        ),
        "phase4_wrapper_dependency_mismatches": (
            wrapper_dependency_mismatches
        ),
        "incomplete_checkpoint_wrappers": (
            incomplete_wrappers
        ),
        "errors": errors,
        "warnings": warnings,
        "status": "PASS" if not errors else "FAIL",
    }


# ═════════════════════════════════════════════════════════════════════════════
# Overall evaluation and printing
# ═════════════════════════════════════════════════════════════════════════════


def _section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def _status_symbol(status: str) -> str:
    return "PASS" if status == "PASS" else "FAIL"


def _print_top_rows(rows: Sequence[Dict[str, Any]], limit: int = 10) -> None:
    for row in rows[:limit]:
        print(
            "  {0:18s} {1:5d}  {2:7.2f}%  {3}".format(
                str(row.get("id", ""))[:18],
                int(row.get("count", 0)),
                float(row.get("pct", 0.0)),
                _normalise_whitespace(row.get("label", ""))[:80],
            )
        )


def print_report(metrics: Dict[str, Any]) -> None:
    _section("REVISED SPEECH COMPENDIUM PIPELINE EVALUATION")
    print("Pipeline configuration source: {0}".format(metrics["pipeline_config"]["source"]))
    print("Semantic metrics: {0}".format("enabled" if metrics["semantic_metrics_enabled"] else "skipped"))

    health = metrics["phase_and_manifest_health"]
    _section("1. Phase and manifest health — {0}".format(_status_symbol(health["status"])))
    for phase_name, phase in health["phases"].items():
        if phase_name == "phase5":
            print(
                "  {0:8s}: pair syntheses {1}/{2} ({3:.1f}%), manifest_complete={4}, integrity={5}".format(
                    phase_name,
                    phase["completed_pair_syntheses"],
                    phase["expected_pair_syntheses"],
                    phase["rate_pct"],
                    phase["manifest_complete"],
                    phase["integrity_status"],
                )
            )
        else:
            print(
                "  {0:8s}: {1}/{2} ({3:.1f}%), manifest_complete={4}".format(
                    phase_name,
                    phase["completed"],
                    phase["expected"],
                    phase["rate_pct"],
                    phase["manifest_complete"],
                )
            )
    for message in health["errors"]:
        print("  ERROR: " + message)
    for message in health["warnings"]:
        print("  WARNING: " + message)

    canonical = metrics["canonical_entity_quality"]
    _section("2. Canonical entity quality")
    print(
        "  CCs: {0} (advisory range {1}-{2}); Themes: {3} (advisory range {4}-{5})".format(
            canonical["canonical_cc_count"],
            canonical["advisory_cc_count_range"][0],
            canonical["advisory_cc_count_range"][1],
            canonical["canonical_theme_count"],
            canonical["advisory_theme_count_range"][0],
            canonical["advisory_theme_count_range"][1],
        )
    )
    for key, label in (
        ("cc_semantic_near_duplicates", "CC"),
        ("theme_semantic_near_duplicates", "Theme"),
    ):
        result = canonical[key]
        if result.get("skipped"):
            print("  {0} semantic duplicate metric skipped.".format(label))
        else:
            print(
                "  {0} near-duplicate pairs: {1}; affected entities: {2:.2f}%".format(
                    label,
                    result["near_duplicate_pair_count"],
                    result["affected_entity_rate"] * 100.0,
                )
            )
            for pair in result["pairs"][:5]:
                print(
                    "    {0:.3f}: {1} <-> {2}".format(
                        pair["similarity"], pair["left_id"], pair["right_id"]
                    )
                )

    classification = metrics["classification_and_mapping_quality"]
    _section("3. Classification and mapping — {0}".format(_status_symbol(classification["status"])))
    print(
        "  Categorised: {0}/{1} ({2:.2f}%); uncategorised: {3}".format(
            classification["categorised_count"],
            classification["classification_record_count"],
            classification["categorisation_rate_pct"],
            classification["uncategorised_count"],
        )
    )
    print("  Primary-CC confidence: {0}".format(classification["primary_cc_confidence"]))
    print("  Relationship types: {0}".format(classification["relationship_type_distribution"]))
    print(
        "  Qualification/opposition classifications: {0}".format(
            classification["nonaffirmative_classification_count"]
        )
    )
    semantic = classification["semantic_alignment"]
    if not semantic.get("skipped"):
        print("  Assigned-CC cosine similarity: {0}".format(semantic["assigned_cc_similarity"]))
        print("  Silhouette score: {0}".format(semantic["silhouette_score_cosine"]))
        print("  Low semantic alignments (diagnostic only): {0}".format(semantic["low_alignment_count"]))
        print("  Similarity by relationship type: {0}".format(
            semantic.get("assigned_cc_similarity_by_relationship_type", {})
        ))
    for message in classification["errors"]:
        print("  ERROR: " + message)
    for message in classification["warnings"]:
        print("  WARNING: " + message)

    usage = metrics["usage_distributions"]
    _section("4. Usage distributions")
    for key, title in (
        ("canonical_cc_usage", "Canonical CC usage"),
        ("canonical_theme_usage", "Canonical Theme usage"),
        ("pair_membership_usage", "Pair membership usage"),
    ):
        report = usage[key]
        print(
            "\n  {0}: entropy={1:.2f}% of max, Gini={2:.4f}, used={3}/{4}".format(
                title,
                report["normalised_entropy_pct"],
                report["gini"],
                report["distinct_used"],
                report["total_available"],
            )
        )
        _print_top_rows(report["per_entity"], 5)

    pairs = metrics["pair_and_theme_structure"]
    _section("5. Pair and Theme-sharing structure — {0}".format(_status_symbol(pairs["status"])))
    print(
        "  Persistent pairs: {0}; density: {1:.4f}%; shared Themes: {2} ({3:.2f}%)".format(
            pairs["pair_count"],
            pairs["pair_density"] * 100.0,
            pairs["shared_theme_count"],
            pairs["shared_theme_rate"] * 100.0,
        )
    )
    print("  Themes per CC: {0}".format(pairs["themes_per_cc"]))
    print("  CCs per used Theme: {0}".format(pairs["ccs_per_used_theme"]))
    print(
        "  Relationship types represented across pairs: {0}".format(
            pairs["relationship_type_pair_distribution"]
        )
    )
    for message in pairs["errors"]:
        print("  ERROR: " + message)
    for message in pairs["warnings"]:
        print("  WARNING: " + message)

    remap = metrics["lossless_remap_quality"]
    _section("6. Lossless Phase 4 remapping — {0}".format(_status_symbol(remap["status"])))
    print(
        "  Records: {0}/{1}; categorised argument accounting: {2:.2f}%; mapped: {3:.2f}%".format(
            remap["phase4_record_count"],
            remap["inventory_record_count"],
            remap["categorised_argument_accounting_pct"],
            remap["categorised_argument_mapped_pct"],
        )
    )
    print(
        "  Contributions: {0}; explicitly unmapped arguments: {1}".format(
            remap["source_contribution_count"],
            remap["explicitly_unmapped_argument_count"],
        )
    )
    print(
        "  Relationship propagation into source contributions: {0:.2f}%".format(
            remap["relationship_propagation_pct"]
        )
    )
    for message in remap["errors"]:
        print("  ERROR: " + message)
    for message in remap["warnings"]:
        print("  WARNING: " + message)

    provenance = metrics["pair_synthesis_provenance"]
    _section("7. Pair synthesis provenance — {0}".format(_status_symbol(provenance["status"])))
    print(
        "  Arguments: {0} ({1:.2f}% valid provenance); evidence: {2} ({3:.2f}%); devices: {4} ({5:.2f}%)".format(
            provenance["canonical_argument_count"],
            provenance["canonical_argument_valid_provenance_pct"],
            provenance["evidence_item_count"],
            provenance["evidence_valid_provenance_pct"],
            provenance["rhetorical_device_count"],
            provenance["rhetorical_device_valid_provenance_pct"],
        )
    )
    print(
        "  Source contribution reference coverage: {0:.2f}%".format(
            provenance["source_contribution_reference_coverage_pct"]
        )
    )
    print(
        "  Arguments with exact relationship-role coverage: {0:.2f}%".format(
            provenance["canonical_argument_valid_relationship_roles_pct"]
        )
    )
    print(
        "  Relationship roles in canonical arguments: {0}".format(
            provenance["relationship_role_distribution"]
        )
    )
    for message in provenance["errors"]:
        print("  ERROR: " + message)
    for message in provenance["warnings"]:
        print("  WARNING: " + message)

    publication = metrics["publication_and_index_integrity"]
    _section("8. Publication and index integrity — {0}".format(_status_symbol(publication["status"])))
    print(
        "  Pair anchors: expected {0}; compendium pair IDs {1}; Theme-index pair IDs {2}; Theme IDs {3}".format(
            publication["expected_pair_anchor_count"],
            publication["compendium_pair_id_count"],
            publication["theme_index_pair_id_count"],
            publication["theme_index_theme_id_count"],
        )
    )
    print(
        "  Shared cross-index links: expected {0}; actual {1}".format(
            publication["expected_shared_cross_index_anchor_count"],
            publication["actual_shared_cross_index_anchor_count"],
        )
    )
    print(
        "  Relationship-role subsections: {0}/{1} canonical arguments".format(
            publication["relationship_role_heading_count"],
            publication["canonical_argument_count"],
        )
    )
    for message in publication["errors"]:
        print("  ERROR: " + message)
    for message in publication["warnings"]:
        print("  WARNING: " + message)

    unverifiable = metrics["unverifiable_claim_completeness"]
    _section("9. Unverifiable-claim completeness — {0}".format(_status_symbol(unverifiable["status"])))
    print(
        "  Expected/published: {0}/{1}; explicit claims: {2}; unverifiable evidence: {3}; source match: {4:.2f}%".format(
            unverifiable["expected_unique_record_count"],
            unverifiable["published_unique_record_count"],
            unverifiable["explicit_unverifiable_claim_count"],
            unverifiable["unverifiable_evidence_item_count"],
            unverifiable["source_match_rate_pct"],
        )
    )
    print("  MEMORY distribution: {0}".format(unverifiable["memory_distribution"]))
    for message in unverifiable["errors"]:
        print("  ERROR: " + message)
    for message in unverifiable["warnings"]:
        print("  WARNING: " + message)

    versions = metrics["version_and_staleness_consistency"]
    _section("10. Version and checkpoint consistency — {0}".format(_status_symbol(versions["status"])))
    print(
        "  Canonical model versions: Phase 3={0}, Phase 4={1}, Phase 5={2}".format(
            versions["phase3_canonical_model_version"],
            versions["phase4_canonical_model_version"],
            versions["phase5_canonical_model_version"],
        )
    )
    print(
        "  Configured base schema/prompt versions: {0}/{1}".format(
            versions["configured_schema_version"],
            versions["configured_prompt_version"],
        )
    )
    print(
        "  Classification schema/prompt versions: {0}/{1}".format(
            versions["configured_classification_schema_version"],
            versions["configured_classification_prompt_version"],
        )
    )
    print(
        "  Bucket schema/prompt versions: {0}/{1}".format(
            versions["configured_bucket_schema_version"],
            versions["configured_bucket_prompt_version"],
        )
    )
    for message in versions["errors"]:
        print("  ERROR: " + message)
    for message in versions["warnings"]:
        print("  WARNING: " + message)

    _section("OVERALL RESULT — {0}".format(metrics["overall_status"]))
    print("Critical failed sections: {0}".format(metrics["failed_sections"] or "None"))
    print("Total warnings: {0}".format(metrics["warning_count"]))


def evaluate(
    paths: Paths,
    config: PipelineConfig,
    skip_semantic: bool = False,
) -> Dict[str, Any]:
    data = load_evaluation_data(paths)

    model = None
    semantic_error = None
    if not skip_semantic:
        try:
            _load_semantic_dependencies()
            print("Loading semantic model: {0}".format(config.embedding_model))
            model = SentenceTransformer(config.embedding_model)
        except Exception as exc:
            semantic_error = str(exc)
            print("WARNING: semantic metrics disabled: {0}".format(exc))

    sections = {
        "phase_and_manifest_health": phase_and_manifest_health(paths, data),
        "canonical_entity_quality": canonical_entity_quality(data, config, model),
        "classification_and_mapping_quality": classification_and_mapping_quality(data, config, model),
        "usage_distributions": usage_distributions(data),
        "pair_and_theme_structure": pair_and_theme_structure(data, config),
        "lossless_remap_quality": lossless_remap_quality(data, config),
        "pair_synthesis_provenance": pair_synthesis_provenance(data, config),
        "publication_and_index_integrity": publication_and_index_integrity(data),
        "unverifiable_claim_completeness": unverifiable_claim_completeness(data),
        "version_and_staleness_consistency": version_and_staleness_consistency(data, config),
    }

    status_sections = [
        "phase_and_manifest_health",
        "classification_and_mapping_quality",
        "pair_and_theme_structure",
        "lossless_remap_quality",
        "pair_synthesis_provenance",
        "publication_and_index_integrity",
        "unverifiable_claim_completeness",
        "version_and_staleness_consistency",
    ]
    failed_sections = [
        name for name in status_sections if sections[name].get("status") == "FAIL"
    ]
    warning_count = 0
    for value in sections.values():
        if isinstance(value, dict):
            warning_count += len(value.get("warnings", []) or [])

    metrics = {
        "evaluator": "standalone_evaluation_script_notree_revised.py",
        "compatible_pipeline": "speech_processing_program_notree_revised.py argumentative-home schema 2.1",
        "pipeline_config": _json_safe(config.__dict__),
        "paths": {
            "pipeline_script": str(paths.pipeline_script),
            "transcripts_dir": str(paths.transcripts_dir),
            "output_dir": str(paths.output_dir),
        },
        "semantic_metrics_enabled": model is not None,
        "semantic_metrics_error": semantic_error,
        **sections,
        "failed_sections": failed_sections,
        "warning_count": warning_count,
        "overall_status": "PASS" if not failed_sections else "FAIL",
    }
    return _json_safe(metrics)


# ═════════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════════


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate artefacts from speech_processing_program_notree_revised.py (argumentative-home schema 2.1)."
    )
    parser.add_argument(
        "--pipeline-script",
        default=DEFAULT_PIPELINE_SCRIPT,
        help="Path to the revised pipeline script, used to read thresholds and versions.",
    )
    parser.add_argument(
        "--transcripts",
        default=DEFAULT_TRANSCRIPTS_DIR,
        help="Directory containing source .txt transcripts.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Pipeline output directory containing checkpoints and final Markdown files.",
    )
    parser.add_argument(
        "--metrics-output",
        default=DEFAULT_METRICS_OUTPUT,
        help="JSON file written by this evaluator.",
    )
    parser.add_argument(
        "--skip-semantic",
        action="store_true",
        help="Run structural evaluation without loading sentence-transformers/sklearn.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the embedding model read from the pipeline script.",
    )
    parser.add_argument(
        "--cc-threshold",
        type=float,
        default=None,
        help="Override canonical-CC near-duplicate threshold.",
    )
    parser.add_argument(
        "--theme-threshold",
        type=float,
        default=None,
        help="Override canonical-Theme near-duplicate threshold.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 2 when any critical structural section fails.",
    )
    args, unknown = parser.parse_known_args(argv)
    if unknown:
        print("Ignoring unrecognised arguments: {0}".format(unknown))
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    paths = Paths(
        pipeline_script=Path(args.pipeline_script),
        transcripts_dir=Path(args.transcripts),
        output_dir=Path(args.output_dir),
        metrics_output=Path(args.metrics_output),
    )
    config = load_pipeline_config(paths.pipeline_script)
    if args.model:
        config.embedding_model = args.model
    if args.cc_threshold is not None:
        config.cc_dedup_threshold = args.cc_threshold
    if args.theme_threshold is not None:
        config.theme_dedup_threshold = args.theme_threshold

    metrics = evaluate(paths, config, skip_semantic=args.skip_semantic)
    print_report(metrics)

    paths.metrics_output.parent.mkdir(parents=True, exist_ok=True)
    paths.metrics_output.write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("\nMetrics written to: {0}".format(paths.metrics_output))

    if args.strict and metrics["overall_status"] != "PASS":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
