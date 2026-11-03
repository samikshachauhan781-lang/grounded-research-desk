"""Regression tests for question intent and sensitive-query detection."""

from backend.app.rag.question_intent import (
    QuestionIntent,
    asks_for_development_status,
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


def test_incident_commander_project_question_is_not_command_intent() -> None:
    assert (
        detect_question_intent("What is the DevOps Incident Commander project about?")
        == QuestionIntent.GENERAL
    )


def test_explain_incident_commander_directory_is_not_command_intent() -> None:
    assert (
        detect_question_intent("Explain the Incident Commander directory.")
        == QuestionIntent.GENERAL
    )


def test_what_command_should_i_run_is_command_intent() -> None:
    assert detect_question_intent("What command should I run?") == QuestionIntent.COMMAND


def test_terminal_command_phrase_is_command_intent() -> None:
    assert (
        detect_question_intent("Give me the terminal command to start the server.")
        == QuestionIntent.COMMAND
    )


def test_how_do_i_run_from_terminal_is_command_intent() -> None:
    assert (
        detect_question_intent("How do I run this project from the terminal?")
        == QuestionIntent.COMMAND
    )


def test_commander_in_question_does_not_trigger_asks_for_command() -> None:
    from backend.app.rag.question_intent import asks_for_command

    assert asks_for_command("What is the DevOps Incident Commander project about?") is False
    assert asks_for_command("What command should I run?") is True


def test_reported_development_status_is_status_oriented() -> None:
    q = "What is the reported development status of the project?"
    assert asks_for_development_status(q) is True
    assert detect_question_intent(q) == QuestionIntent.GENERAL


def test_internal_software_project_not_status_oriented() -> None:
    assert asks_for_development_status("Is this an internal software project?") is False


def test_application_architecture_not_status_oriented() -> None:
    assert asks_for_development_status("What is the application architecture?") is False
