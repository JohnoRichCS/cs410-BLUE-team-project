from models.submission import Submission
from models.evidence import Evidence


FAKE_SOURCES = [
    {
        "publisher": "Test Source",
        "title": "Test Evidence",
        "url": "https://example.com/one",
        "snippet": "Test evidence for the submitted claim.",
        "relevance_score": 0.80
    },
    {
        "publisher": "Second Source",
        "title": "Second Evidence",
        "url": "https://example.com/two",
        "snippet": "Second piece of evidence.",
        "relevance_score": 0.60
    }
]


FAKE_RESULT = {
    "verdict": "Uncertain",
    "confidence": 75,
    "summary": "Test analysis result.",
    "explanation": "This is a test explanation."
}


FAKE_CLASSIFICATION = {
    "category": "Science",
    "claim_type": "Factual",
    "is_conditional": False,
    "conditions": [],
    "missing_context": []
}


def submit_test_claim(
    client,
    monkeypatch,
    claim="The Earth has two moons."
):
    monkeypatch.setattr(
        "routes.main.classify_claim",
        lambda claim: FAKE_CLASSIFICATION
    )

    monkeypatch.setattr(
        "routes.main.find_evidence",
        lambda claim: FAKE_SOURCES
    )

    # Ranking and relevance behavior are tested separately
    # in test_evidence_service.py.
    #
    # This test verifies that already-processed evidence
    # is persisted correctly.
    monkeypatch.setattr(
        "routes.main.process_evidence",
        lambda claim, category, evidence_items: evidence_items
    )

    monkeypatch.setattr(
        "routes.main.analyze_claim",
        lambda claim, evidence: FAKE_RESULT
    )

    return client.post(
        "/analyze",
        data={
            "claim": claim
        }
    )


def test_evidence_items_are_persisted(
    app,
    client,
    monkeypatch
):
    """
    FR-05 / issue #14:
    each retained evidence item is saved to the database
    and linked to its parent Submission.
    """

    response = submit_test_claim(
        client,
        monkeypatch
    )

    assert response.status_code == 200

    with app.app_context():
        submission = Submission.query.first()

        assert submission is not None

        saved_evidence = Evidence.query.filter_by(
            submission_id=submission.id
        ).all()

        assert (
            len(saved_evidence)
            == len(FAKE_SOURCES)
        )

        urls = {
            item.url
            for item in saved_evidence
        }

        assert (
            "https://example.com/one"
            in urls
        )

        assert (
            "https://example.com/two"
            in urls
        )

        first = next(
            item
            for item in saved_evidence
            if item.url
            == "https://example.com/one"
        )

        assert (
            first.title
            == "Test Evidence"
        )

        assert (
            first.publisher
            == "Test Source"
        )

        assert (
            first.excerpt
            == "Test evidence for the submitted claim."
        )

        assert (
            first.relevance
            == 0.80
        )


def test_submission_saves_classifier_topic(
    app,
    client,
    monkeypatch
):
    """
    FR-05 / issue #14:
    a saved verification stores the category returned
    by claim classification.
    """

    submit_test_claim(
        client,
        monkeypatch
    )

    with app.app_context():
        submission = Submission.query.first()

        assert submission is not None
        assert submission.topic == "Science"


def test_detail_page_shows_claim_verdict_and_evidence(
    app,
    client,
    monkeypatch
):
    """
    FR-07 / issue #16:
    opening a saved verification's detail page shows
    the claim, verdict, and each linked evidence item.
    """

    submit_test_claim(
        client,
        monkeypatch
    )

    with app.app_context():
        submission = Submission.query.first()

        assert submission is not None

        submission_id = submission.id

    response = client.get(
        f"/submissions/{submission_id}"
    )

    assert response.status_code == 200

    assert (
        b"The Earth has two moons."
        in response.data
    )

    assert (
        b"Uncertain"
        in response.data
    )

    assert (
        b"Test Evidence"
        in response.data
    )

    assert (
        b"Second Evidence"
        in response.data
    )

    assert (
        b"https://example.com/one"
        in response.data
    )


def test_detail_page_links_from_history(
    app,
    client,
    monkeypatch
):
    """
    FR-07 / issue #16:
    a history item links to its own detail view.
    """

    submit_test_claim(
        client,
        monkeypatch
    )

    with app.app_context():
        submission = Submission.query.first()

        assert submission is not None

        submission_id = submission.id

    response = client.get(
        "/history"
    )

    assert response.status_code == 200

    assert (
        f"/submissions/{submission_id}".encode()
        in response.data
    )


def test_detail_page_404_for_unknown_submission(
    client
):
    response = client.get(
        "/submissions/999999"
    )

    assert response.status_code == 404