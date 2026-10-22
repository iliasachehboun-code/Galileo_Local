"""Oracle detects clear personal data. Layer 8 still refuses free text."""

import pytest
from pydantic import ValidationError

from galileo_local.models import Span, SpanType, Trace, rehydration_span
from galileo_local.pii_oracle import find_clear_pii


def test_oracle_names_kinds_not_values() -> None:
    kinds = find_clear_pii("écrire à marie.dupont@cimr.ma")
    assert kinds == ["email"]
    assert "marie.dupont" not in " ".join(kinds)


def test_masked_placeholders_are_not_pii() -> None:
    text = (
        "Dossier [CIMR_CIN_abcd1234], contact [EMAIL_deadbeef], "
        "RIB [CIMR_RIB_ffff0000]."
    )
    assert find_clear_pii(text) == []


def test_chat_trace_with_clear_text_is_valid() -> None:
    trace = Trace(
        project="galileo-local",
        log_stream="chat",
        session_id="sess_7f3a",
        request_id="req_01",
        name="chat_agent",
        spans=[
            Span(
                name="agent",
                type=SpanType.AGENT,
                input_masked="Quelle est la procédure de liquidation ?",
                output_masked="Voici les étapes principales.",
                metadata={"role": "assistant"},
            ),
            Span(
                name="llm",
                type=SpanType.LLM,
                input_masked="Quelle est la procédure de liquidation ?",
                output_masked="Voici les étapes principales.",
                metadata={"model": "gpt-4o-mini"},
            ),
            rehydration_span(token_count=2, status="ok"),
        ],
    )
    assert trace.spans[-1].output_masked == ""
    assert trace.spans[-1].metadata["token_count"] == "2"


def test_clear_email_in_a_span_is_accepted_and_detected() -> None:
    span = Span(
        name="llm_completion",
        type=SpanType.LLM,
        input_masked="Contacter marie.dupont@cimr.ma",
        output_masked="ok",
    )
    assert find_clear_pii(span.input_masked) == ["email"]


def test_disguised_personal_values_are_detected() -> None:
    cases = (
        ("iban", "virer sur ma64011519000001205000530121"),
        ("iban", "virer sur MA64 0115 1900 0001 2050 0053 0121"),
        ("phone", "rappel au 06 12 34 56 78"),
        ("phone", "rappel au +212 612345678"),
        ("email", "écrire à marie.\u200bdupont@cimr.ma"),
    )
    for kind, text in cases:
        kinds = find_clear_pii(text)
        assert kind in kinds
        assert "marie" not in " ".join(kinds)
        assert "640115" not in " ".join(kinds)
        Span(name="layer_6", type=SpanType.WORKFLOW, input_masked=text, output_masked="")


def test_invisible_cut_does_not_hide_iban_or_digits() -> None:
    cut = "\u200b"
    cases = (
        ("iban", f"x{cut}MA64011519000001205000530121"),
        ("iban", f"a{cut}ma64011519000001205000530121"),
        ("iban", f"a{cut}MA64 0115 1900 0001 2050 0053 0121"),
        ("long_digit_run", f"compte{cut}123456789012"),
    )
    for kind, text in cases:
        kinds = find_clear_pii(text)
        assert kind in kinds
        assert "640115" not in " ".join(kinds)
        assert "123456789012" not in " ".join(kinds)


def test_clear_phone_and_iban_are_detected() -> None:
    assert "phone" in find_clear_pii("rappel au 0612345678")
    assert "iban" in find_clear_pii("virer sur MA64011519000001205000530121")


def test_metadata_cannot_be_named_like_a_clear_field() -> None:
    with pytest.raises(ValidationError, match="forbidden metadata keys"):
        Span(
            name="layer_3",
            type=SpanType.WORKFLOW,
            metadata={"email": "[EMAIL_deadbeef]"},
        )


def test_rehydrated_answer_must_not_use_layer_8_as_a_side_door() -> None:
    with pytest.raises(ValidationError, match="layer 8"):
        Span(
            name="layer_8_rehydration",
            type=SpanType.WORKFLOW,
            output_masked="Bonjour marie.dupont@cimr.ma",
            metadata={"layer": "8", "status": "ok"},
        )
