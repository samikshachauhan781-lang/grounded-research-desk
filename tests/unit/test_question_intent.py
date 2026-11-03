"""Regression tests for question intent and sensitive-query detection."""

from backend.app.rag.question_intent import (
    QuestionIntent,
    detect_metadata_field,
    detect_question_intent,
)


def test_why_was_incident_resolved_is_resolution_not_root_cause() -> None:
    assert (
        detect_question_intent("Why was the incident resolved?")
        == QuestionIntent.RESOLUTION
    )


def test_how_was_incident_fixed_is_resolution() -> None:
    assert (
        detect_question_intent("How was the incident fixed?")
        == QuestionIntent.RESOLUTION
    )


def test_why_did_incident_happen_is_root_cause() -> None:
    assert (
        detect_question_intent("Why did the incident happen?")
        == QuestionIntent.ROOT_CAUSE
    )


def test_why_did_payment_api_fail_is_root_cause() -> None:
    assert (
        detect_question_intent("Why did the Payment API fail?")
        == QuestionIntent.ROOT_CAUSE
    )


def test_credential_policy_question_not_sensitive_field() -> None:
    assert detect_metadata_field("What is the credential rotation policy?") is None


def test_password_reveal_still_sensitive() -> None:
    assert detect_metadata_field("What was the database password?") == "sensitive_missing"
