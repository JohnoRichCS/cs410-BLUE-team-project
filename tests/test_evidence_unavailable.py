from models.submission import Submission


UNAVAILABLE_MESSAGE = b"Evidence sources are temporarily unavailable."


def test_results_page_shows_unavailable_message(app, client, monkeypatch):
    """4.4: when find_evidence() signals total source failure (returns
    None), the results page shows the required message instead of a
    generic 'no evidence found' result."""

    monkeypatch.setattr(
        "routes.main.find_evidence",
        lambda claim: None
    )

    def fail_if_called(claim, evidence):
        raise AssertionError(
            "analyze_claim should not be called when evidence "
            "retrieval itself failed"
        )

    monkeypatch.setattr("routes.main.analyze_claim", fail_if_called)

    response = client.post(
        "/analyze",
        data={"claim": "The Earth has two moons."}
    )

    assert response.status_code == 200
    assert UNAVAILABLE_MESSAGE in response.data


def test_submission_saved_with_unavailable_explanation(app, client, monkeypatch):
    monkeypatch.setattr(
        "routes.main.find_evidence",
        lambda claim: None
    )

    monkeypatch.setattr(
        "routes.main.analyze_claim",
        lambda claim, evidence: (_ for _ in ()).throw(
            AssertionError("analyze_claim should not be called")
        )
    )

    client.post(
        "/analyze",
        data={"claim": "The Earth has two moons."}
    )

    with app.app_context():
        submission = Submission.query.first()

        assert submission is not None
        assert submission.explanation == (
            "Evidence sources are temporarily unavailable."
        )


def test_results_page_unaffected_when_sources_found(app, client, monkeypatch):
    """A normal, non-empty evidence list still flows through analyze_claim
    as before - the 4.4 short-circuit only applies to total failure."""

    fake_sources = [
        {
            "publisher": "Test Source",
            "title": "Test Evidence",
            "url": "https://example.com",
            "snippet": "Test evidence for the submitted claim."
        }
    ]

    fake_result = {
        "verdict": "Supported",
        "confidence": 90,
        "summary": "Test analysis result.",
        "explanation": "This is a test explanation."
    }

    monkeypatch.setattr(
        "routes.main.find_evidence",
        lambda claim: fake_sources
    )

    monkeypatch.setattr(
        "routes.main.analyze_claim",
        lambda claim, evidence: fake_result
    )

    response = client.post(
        "/analyze",
        data={"claim": "The Earth has two moons."}
    )

    assert response.status_code == 200
    assert UNAVAILABLE_MESSAGE not in response.data
    assert b"Test analysis result." in response.data


def test_results_page_unaffected_when_sources_empty_not_none(app, client, monkeypatch):
    """An empty list (sources searched, found nothing) still goes through
    analyze_claim as before - only None triggers the 4.4 message."""

    analyze_claim_calls = []

    def fake_analyze_claim(claim, evidence):
        analyze_claim_calls.append((claim, evidence))
        return {
            "verdict": "Uncertain",
            "confidence": 0,
            "summary": "No evidence was found for this claim.",
            "explanation": "No evidence was found."
        }

    monkeypatch.setattr(
        "routes.main.find_evidence",
        lambda claim: []
    )

    monkeypatch.setattr(
        "routes.main.analyze_claim",
        fake_analyze_claim
    )

    response = client.post(
        "/analyze",
        data={"claim": "The Earth has two moons."}
    )

    assert response.status_code == 200
    assert UNAVAILABLE_MESSAGE not in response.data
    assert len(analyze_claim_calls) == 1
