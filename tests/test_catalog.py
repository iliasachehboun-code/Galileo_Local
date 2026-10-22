"""The catalog is the Galileo metric surface we commit to implement."""

from galileo_local.catalog import (
    CUSTOM_METRIC_KINDS,
    METRICS,
    metrics_for_cimr_stream,
    metrics_for_span,
)

EXPECTED_IDS = {
    "action_advancement",
    "action_completion",
    "agent_efficiency",
    "agent_flow",
    "conversation_quality",
    "reasoning_coherence",
    "tool_selection_quality",
    "tool_error",
    "user_intent_change",
    "tone",
    "visual_quality",
    "visual_fidelity",
    "interruption_detection",
    "ground_truth_adherence",
    "correctness",
    "instruction_adherence",
    "chunk_relevance",
    "context_relevance",
    "context_precision",
    "precision_at_k",
    "context_adherence",
    "completeness",
    "unsafe_output",
    "prompt_injection",
    "pii",
    "sexism",
    "toxicity",
    "sql_correctness",
    "sql_adherence",
    "sql_injection",
    "sql_efficiency",
}


def test_catalog_matches_galileo_surface() -> None:
    assert {metric.id for metric in METRICS} == EXPECTED_IDS
    assert len(METRICS) == len(EXPECTED_IDS)


def test_every_metric_points_at_galileo_docs() -> None:
    for metric in METRICS:
        assert metric.doc.startswith("https://docs.galileo.ai/concepts/metrics/")
        assert metric.kind in {"llm_judge", "code"}


def test_cimr_stream_skips_multimodal_and_sql() -> None:
    enabled = {metric.id for metric in metrics_for_cimr_stream()}
    assert "pii" in enabled
    assert "context_adherence" in enabled
    assert "prompt_injection" in enabled
    assert "visual_quality" not in enabled
    assert "sql_injection" not in enabled
    assert len(enabled) == 24


def test_pii_metric_applies_to_every_span_type() -> None:
    for span_type in ("workflow", "agent", "llm", "retriever", "tool"):
        ids = {metric.id for metric in metrics_for_span(span_type)}
        assert "pii" in ids


def test_custom_metric_kinds_cover_galileo() -> None:
    assert CUSTOM_METRIC_KINDS == ("llm_judge", "code", "composite")
