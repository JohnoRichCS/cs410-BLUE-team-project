from services.evidence_service import normalize_fact_checks


def test_normalize_fact_checks():
    fake_response = {
        "claims": [
            {
                "text": "The Earth is flat.",
                "claimReview": [
                    {
                        "publisher": {
                            "name": "Example Fact Checker"
                        },
                        "url": "https://example.com/fact-check",
                        "title": "Earth is not flat",
                        "reviewDate": "2026-01-01T00:00:00Z",
                        "textualRating": "False"
                    }
                ]
            }
        ]
    }

    evidence = normalize_fact_checks(fake_response)

    assert len(evidence) == 1
    assert evidence[0]["publisher"] == "Example Fact Checker"
    assert evidence[0]["title"] == "Earth is not flat"
    assert evidence[0]["url"] == "https://example.com/fact-check"
    assert "False" in evidence[0]["snippet"]


def test_empty_response():
    evidence = normalize_fact_checks({})

    assert evidence == []


def test_claim_without_reviews():
    fake_response = {
        "claims": [
            {
                "text": "Some claim"
            }
        ]
    }

    evidence = normalize_fact_checks(fake_response)

    assert evidence == []