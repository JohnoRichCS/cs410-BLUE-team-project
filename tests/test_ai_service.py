from services.ai_service import validate_result


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