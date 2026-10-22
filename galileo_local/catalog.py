"""Galileo out-of-the-box metric catalog.

Ids and families follow the public Galileo docs
(https://docs.galileo.ai/concepts/metrics/overview). Multimodal and
text-to-SQL metrics are in the catalog. The chat stream does not
enable them: its spans are text, not images, audio, or SQL.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricSpec:
    id: str
    name: str
    family: str
    kind: str
    span_types: tuple[str, ...]
    cimr_stream: bool
    doc: str


def _m(
    metric_id: str,
    name: str,
    family: str,
    kind: str,
    span_types: tuple[str, ...],
    *,
    cimr_stream: bool,
    doc: str,
) -> MetricSpec:
    return MetricSpec(
        id=metric_id,
        name=name,
        family=family,
        kind=kind,
        span_types=span_types,
        cimr_stream=cimr_stream,
        doc=doc,
    )


_DOCS = "https://docs.galileo.ai/concepts/metrics"

METRICS: tuple[MetricSpec, ...] = (
    _m("action_advancement", "Action Advancement", "agentic", "llm_judge", ("agent",), cimr_stream=True, doc=f"{_DOCS}/agentic/action-advancement"),
    _m("action_completion", "Action Completion", "agentic", "llm_judge", ("agent", "workflow"), cimr_stream=True, doc=f"{_DOCS}/agentic/action-completion"),
    _m("agent_efficiency", "Agent Efficiency", "agentic", "llm_judge", ("agent",), cimr_stream=True, doc=f"{_DOCS}/agentic/agent-efficiency"),
    _m("agent_flow", "Agent Flow", "agentic", "llm_judge", ("agent", "workflow"), cimr_stream=True, doc=f"{_DOCS}/agentic/agent-flow"),
    _m("conversation_quality", "Conversation Quality", "agentic", "llm_judge", ("workflow",), cimr_stream=True, doc=f"{_DOCS}/agentic/conversation-quality"),
    _m("reasoning_coherence", "Reasoning Coherence", "agentic", "llm_judge", ("agent", "llm"), cimr_stream=True, doc=f"{_DOCS}/agentic/reasoning-coherence"),
    _m("tool_selection_quality", "Tool Selection Quality", "agentic", "llm_judge", ("tool", "agent"), cimr_stream=True, doc=f"{_DOCS}/agentic/tool-selection-quality"),
    _m("tool_error", "Tool Error", "agentic", "code", ("tool",), cimr_stream=True, doc=f"{_DOCS}/agentic/tool-error"),
    _m("user_intent_change", "User Intent Change", "agentic", "llm_judge", ("workflow",), cimr_stream=True, doc=f"{_DOCS}/agentic/intent-change"),
    _m("tone", "Tone", "expression", "llm_judge", ("llm",), cimr_stream=True, doc=f"{_DOCS}/expression-and-readability/tone"),
    _m("visual_quality", "Visual Quality", "multimodal", "llm_judge", ("llm",), cimr_stream=False, doc=f"{_DOCS}/multimodal-quality/visual-quality"),
    _m("visual_fidelity", "Visual Fidelity", "multimodal", "llm_judge", ("llm",), cimr_stream=False, doc=f"{_DOCS}/multimodal-quality/visual-fidelity"),
    _m("interruption_detection", "Interruption Detection", "multimodal", "llm_judge", ("llm",), cimr_stream=False, doc=f"{_DOCS}/multimodal-quality/interruption-detection"),
    _m("ground_truth_adherence", "Ground Truth Adherence", "response_quality", "llm_judge", ("llm",), cimr_stream=True, doc=f"{_DOCS}/response-quality/ground-truth-adherence"),
    _m("correctness", "Correctness", "response_quality", "llm_judge", ("llm",), cimr_stream=True, doc=f"{_DOCS}/response-quality/correctness"),
    _m("instruction_adherence", "Instruction Adherence", "response_quality", "llm_judge", ("llm", "agent"), cimr_stream=True, doc=f"{_DOCS}/response-quality/instruction-adherence"),
    _m("chunk_relevance", "Chunk Relevance", "rag_retrieval", "llm_judge", ("retriever",), cimr_stream=True, doc=f"{_DOCS}/rag/retrieval-quality/chunk-relevance"),
    _m("context_relevance", "Context Relevance", "rag_retrieval", "llm_judge", ("retriever",), cimr_stream=True, doc=f"{_DOCS}/rag/retrieval-quality/context-relevance"),
    _m("context_precision", "Context Precision", "rag_retrieval", "llm_judge", ("retriever",), cimr_stream=True, doc=f"{_DOCS}/rag/retrieval-quality/context-precision"),
    _m("precision_at_k", "Precision at K", "rag_retrieval", "code", ("retriever",), cimr_stream=True, doc=f"{_DOCS}/rag/retrieval-quality/precision-at-k"),
    _m("context_adherence", "Context Adherence", "rag_generation", "llm_judge", ("llm",), cimr_stream=True, doc=f"{_DOCS}/rag/generation-quality/context-adherence"),
    _m("completeness", "Completeness", "rag_generation", "llm_judge", ("llm",), cimr_stream=True, doc=f"{_DOCS}/rag/generation-quality/completeness"),
    _m("unsafe_output", "Unsafe Output", "safety", "llm_judge", ("llm",), cimr_stream=True, doc=f"{_DOCS}/safety-and-compliance/unsafe-output"),
    _m("prompt_injection", "Prompt Injection", "safety", "llm_judge", ("llm", "workflow"), cimr_stream=True, doc=f"{_DOCS}/safety-and-compliance/prompt-injection"),
    _m("pii", "PII", "safety", "code", ("workflow", "agent", "llm", "retriever", "tool"), cimr_stream=True, doc=f"{_DOCS}/safety-and-compliance/pii"),
    _m("sexism", "Sexism", "safety", "llm_judge", ("llm",), cimr_stream=True, doc=f"{_DOCS}/safety-and-compliance/sexism"),
    _m("toxicity", "Toxicity", "safety", "llm_judge", ("llm",), cimr_stream=True, doc=f"{_DOCS}/safety-and-compliance/toxicity"),
    _m("sql_correctness", "SQL Correctness", "text_to_sql", "code", ("tool", "llm"), cimr_stream=False, doc=f"{_DOCS}/text2sql/sql-correctness"),
    _m("sql_adherence", "SQL Adherence", "text_to_sql", "llm_judge", ("llm",), cimr_stream=False, doc=f"{_DOCS}/text2sql/sql-adherence"),
    _m("sql_injection", "SQL Injection", "text_to_sql", "code", ("llm", "tool"), cimr_stream=False, doc=f"{_DOCS}/text2sql/sql-injection"),
    _m("sql_efficiency", "SQL Efficiency", "text_to_sql", "llm_judge", ("llm",), cimr_stream=False, doc=f"{_DOCS}/text2sql/sql-efficiency"),
)

CUSTOM_METRIC_KINDS: tuple[str, ...] = ("llm_judge", "code", "composite")


def metrics_for_cimr_stream() -> tuple[MetricSpec, ...]:
    """Metrics enabled on the CIMR gateway log stream."""
    return tuple(metric for metric in METRICS if metric.cimr_stream)


def metrics_for_span(span_type: str) -> tuple[MetricSpec, ...]:
    """CIMR-stream metrics whose span types include ``span_type``."""
    return tuple(
        metric
        for metric in metrics_for_cimr_stream()
        if span_type in metric.span_types
    )
