"""The Agno judge is instructed to score masked spans and nothing else."""

from galileo_local.catalog import METRICS
from galileo_local.judges import METRIC_JUDGE_INSTRUCTIONS, MetricScore, metric_prompt
from galileo_local.models import Span, SpanType


def test_instructions_forbid_unmasking() -> None:
    text = METRIC_JUDGE_INSTRUCTIONS.lower()
    assert "masked" in text
    assert "never reconstruct" in text
    assert "never the value itself" in text


def test_prompt_contains_only_the_masked_span() -> None:
    span = Span(
        name="llm_completion",
        type=SpanType.LLM,
        input_masked="Dossier [CIMR_CIN_abcd1234].",
        output_masked="Le dossier est en cours.",
        metadata={"layer": "6"},
    )
    metric = next(item for item in METRICS if item.id == "context_adherence")
    prompt = metric_prompt(metric, span)
    assert "context_adherence" in prompt
    assert "[CIMR_CIN_abcd1234]" in prompt
    assert "Score only this metric." in prompt


def test_score_schema_is_bounded() -> None:
    score = MetricScore(
        metric_id="pii",
        score=1.0,
        passed=True,
        rationale="No clear personal data in the masked span.",
    )
    assert score.metric_id == "pii"


def test_metric_judge_builds_an_agno_agent() -> None:
    pytest = __import__("pytest")
    pytest.importorskip("agno")
    from agno.models.openai import OpenAIChat

    from galileo_local.judges import build_metric_judge

    agent = build_metric_judge(OpenAIChat(id="gpt-4o-mini", api_key="test-not-used"))
    assert agent.name == "galileo-metric-judge"
    assert agent.output_schema is MetricScore
    assert agent.telemetry is False
