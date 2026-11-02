from models import db
from models.submission import Submission


def test_faict_skeleton_workflow(app, client, monkeypatch):
    """
    Tests the Faict application flow without making real API calls.

    Verifies that:
    1. The homepage loads.
    2. A claim can be submitted.
    3. Analysis results reach the results page.
    4. Evidence reaches the results page.
    5. The submission is saved to the database.
    """

    fake_sources = [
        {
            "publisher": "Test Source",
            "title": "Test Evidence",
            "url": "https://example.com",
            "snippet": "Test evidence for the submitted claim."
        }
    ]

    fake_result = {
        "verdict": "Uncertain",
        "confidence": 75,
        "summary": "Test analysis result.",
        "explanation": "This is a test explanation."
    }

    fake_classification = {
        "category": "Science",
        "claim_type": "Factual",
        "is_conditional": False,
        "conditions": [],
        "missing_context": []
    }

    # Replace external services during this test

    monkeypatch.setattr(
        "routes.main.classify_claim",
        lambda claim: fake_classification
    )

    monkeypatch.setattr(
        "routes.main.find_evidence",
        lambda claim: fake_sources
    )

    # Relevance and ranking are tested separately in
    # test_evidence_service.py. Keep this test focused on
    # the Flask application workflow.
    monkeypatch.setattr(
        "routes.main.process_evidence",
        lambda claim, category, evidence_items: evidence_items
    )

    monkeypatch.setattr(
        "routes.main.analyze_claim",
        lambda claim, evidence: fake_result
    )

    # 1. Homepage loads

    response = client.get("/")

    assert response.status_code == 200

    # 2. Submit a claim

    test_claim = "The Earth has two moons."

    response = client.post(
        "/analyze",
        data={
            "claim": test_claim
        }
    )

    assert response.status_code == 200

    # 3. Analysis reached the results page

    assert b"Uncertain" in response.data
    assert b"75%" in response.data
    assert b"Test analysis result." in response.data

    # 4. Evidence reached the results page

    assert b"Test Source" in response.data
    assert b"Test Evidence" in response.data

    # 5. Submission was saved to the database

    with app.app_context():
        saved_submission = Submission.query.first()

        assert saved_submission is not None
        assert saved_submission.claim == test_claim
        assert saved_submission.verdict == "Uncertain"
        assert saved_submission.confidence == 75