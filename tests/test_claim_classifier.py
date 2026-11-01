from services.claim_classifier import (
    classify_claim,
    validate_classification,
    default_classification
)


# ISSUE #10: CLAIM CLASSIFICATION

def test_valid_classification():
    result = validate_classification({
        "category": "Astronomy",
        "claim_type": "Factual",
        "is_conditional": False,
        "conditions": [],
        "missing_context": []
    })

    assert result["category"] == "Astronomy"
    assert result["claim_type"] == "Factual"
    assert result["is_conditional"] is False


def test_health_classification():
    result = validate_classification({
        "category": "Health",
        "claim_type": "Causal",
        "is_conditional": False,
        "conditions": [],
        "missing_context": []
    })

    assert result["category"] == "Health"
    assert result["claim_type"] == "Causal"


def test_invalid_claim_type():
    result = validate_classification({
        "category": "Technology",
        "claim_type": "Invalid Type",
        "is_conditional": False,
        "conditions": [],
        "missing_context": []
    })

    assert result["claim_type"] == "Other"


# ISSUE #11: CONDITIONAL-CLAIM DETECTION

def test_conditional_claim():
    result = validate_classification({
        "category": "Education",
        "claim_type": "Conditional",
        "is_conditional": True,
        "conditions": [
            "Student withdraws from college"
        ],
        "missing_context": [
            "Type of financial aid"
        ]
    })

    assert result["is_conditional"] is True
    assert len(result["conditions"]) == 1
    assert len(result["missing_context"]) == 1


def test_nonconditional_claim():
    result = validate_classification({
        "category": "Science",
        "claim_type": "Factual",
        "is_conditional": False,
        "conditions": [],
        "missing_context": []
    })

    assert result["is_conditional"] is False


# ERROR HANDLING

def test_empty_claim():
    result = classify_claim("")

    assert result["category"] == "Unknown"
    assert result["is_conditional"] is False


def test_invalid_response():
    result = validate_classification(None)

    assert result["category"] == "Unknown"


def test_default_classification():
    result = default_classification()

    assert result["category"] == "Unknown"
    assert result["conditions"] == []
    assert result["missing_context"] == []