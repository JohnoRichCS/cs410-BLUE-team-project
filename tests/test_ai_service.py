from services.ai_service import analyze_claim, normalize_verdict, validate_result


def test_valid_result_is_preserved():
    result = validate_result({
        "verdict": "Supported",
        "confidence": 88,
        "summary": "The evidence supports the claim.",
        "explanation": "The supplied evidence supports the claim."
    })

    assert result["verdict"] == "Supported"
    assert result["confidence"] == 88


def test_invalid_verdict_becomes_uncertain():
    result = validate_result({
        "verdict": "Maybe",
        "confidence": 50,
        "summary": "Test",
        "explanation": "Test"
    })

    assert result["verdict"] == "Uncertain"


def test_high_confidence_is_limited():
    result = validate_result({
        "verdict": "Supported",
        "confidence": 150,
        "summary": "Test",
        "explanation": "Test"
    })

    assert result["confidence"] == 100


def test_negative_confidence_is_limited():
    result = validate_result({
        "verdict": "Unsupported",
        "confidence": -10,
        "summary": "Test",
        "explanation": "Test"
    })

    assert result["confidence"] == 0


def test_uncertain_confidence_is_limited():
    result = validate_result({
        "verdict": "Uncertain",
        "confidence": 99,
        "summary": "Insufficient evidence.",
        "explanation": "The evidence does not address the claim."
    })

    assert result["confidence"] == 69


def test_empty_claim_does_not_call_api():
    result = analyze_claim("", [])

    assert result["verdict"] == "Unable to verify"
    assert result["confidence"] == 0
    assert result["summary"] == "No claim was provided."


def test_no_evidence_returns_unable_to_verify():
    """3.7.2 / 3.7.4: no retained evidence maps to Unable to verify with
    the SRS's exact required explanation text."""

    result = analyze_claim(
        "Did I eat bacon today?",
        []
    )

    assert result["verdict"] == "Unable to verify"
    assert result["confidence"] == 0
    assert result["summary"] == "No evidence was found for this claim."
    assert result["explanation"] == "Not enough relevant evidence was found."


def test_normalize_verdict_supported_is_unchanged():
    assert normalize_verdict("Supported") == "Supported"


def test_normalize_verdict_misleading_becomes_contradicted():
    assert normalize_verdict("Misleading") == "Contradicted"


def test_normalize_verdict_unsupported_becomes_contradicted():
    assert normalize_verdict("Unsupported") == "Contradicted"


def test_normalize_verdict_uncertain_becomes_unable_to_verify():
    assert normalize_verdict("Uncertain") == "Unable to verify"


def test_normalize_verdict_unknown_value_becomes_unable_to_verify():
    assert normalize_verdict("Something else") == "Unable to verify"