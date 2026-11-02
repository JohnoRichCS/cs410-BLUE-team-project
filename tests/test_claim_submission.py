from models.submission import Submission


FAKE_SOURCES = [
    {
        "publisher": "Test Source",
        "title": "Test Evidence",
        "url": "https://example.com",
        "snippet": "Test evidence for the submitted claim."
    }
]

FAKE_RESULT = {
    "verdict": "Supported",
    "confidence": 90,
    "summary": "Test analysis result.",
    "explanation": "This is a test explanation."
}

ERROR_MESSAGE = b"Enter a claim between 10 and 500 characters."


def stub_services(monkeypatch):
    monkeypatch.setattr(
        "routes.main.find_evidence",
        lambda claim: FAKE_SOURCES
    )

    monkeypatch.setattr(
        "routes.main.analyze_claim",
        lambda claim, evidence: FAKE_RESULT
    )


def test_claim_within_range_starts_workflow(app, client, monkeypatch):
    """3.1.2 / 3.1.4: a 10-500 char claim is accepted and analyzed."""

    stub_services(monkeypatch)

    response = client.post(
        "/analyze",
        data={"claim": "The Earth has two moons."}
    )

    assert response.status_code == 200
    assert ERROR_MESSAGE not in response.data

    with app.app_context():
        assert Submission.query.count() == 1


def test_exactly_ten_characters_is_accepted(app, client, monkeypatch):
    """3.1.2: a claim at the lower boundary (10 chars) is accepted."""

    stub_services(monkeypatch)

    response = client.post("/analyze", data={"claim": "1234567890"})

    assert response.status_code == 200
    assert ERROR_MESSAGE not in response.data

    with app.app_context():
        assert Submission.query.count() == 1


def test_exactly_five_hundred_characters_is_accepted(app, client, monkeypatch):
    """3.1.2: a claim at the upper boundary (500 chars) is accepted."""

    stub_services(monkeypatch)

    response = client.post("/analyze", data={"claim": "a" * 500})

    assert response.status_code == 200
    assert ERROR_MESSAGE not in response.data

    with app.app_context():
        assert Submission.query.count() == 1


def test_nine_characters_is_rejected(app, client, monkeypatch):
    """3.1.2 / 3.1.3: a 9-char claim is rejected before analysis starts."""

    stub_services(monkeypatch)

    response = client.post("/analyze", data={"claim": "123456789"})

    assert response.status_code == 200
    assert ERROR_MESSAGE in response.data

    with app.app_context():
        assert Submission.query.count() == 0


def test_five_hundred_and_one_characters_is_rejected(app, client, monkeypatch):
    """3.1.2 / 3.1.3: a 501-char claim is rejected before analysis starts."""

    stub_services(monkeypatch)

    response = client.post("/analyze", data={"claim": "a" * 501})

    assert response.status_code == 200
    assert ERROR_MESSAGE in response.data

    with app.app_context():
        assert Submission.query.count() == 0


def test_empty_claim_is_rejected(app, client, monkeypatch):
    """3.1.3: an empty claim is rejected and does not start verification."""

    stub_services(monkeypatch)

    response = client.post("/analyze", data={"claim": ""})

    assert response.status_code == 200
    assert ERROR_MESSAGE in response.data

    with app.app_context():
        assert Submission.query.count() == 0


def test_whitespace_only_claim_is_rejected(app, client, monkeypatch):
    """
    3.1.2: length is measured after leading/trailing whitespace is
    removed, so a claim that is only whitespace is rejected.
    """

    stub_services(monkeypatch)

    response = client.post("/analyze", data={"claim": "              "})

    assert response.status_code == 200
    assert ERROR_MESSAGE in response.data

    with app.app_context():
        assert Submission.query.count() == 0


def test_claim_is_stripped_before_saving(app, client, monkeypatch):
    """3.1.2: surrounding whitespace is removed from the stored claim."""

    stub_services(monkeypatch)

    client.post(
        "/analyze",
        data={"claim": "   The Earth has two moons.   "}
    )

    with app.app_context():
        submission = Submission.query.first()
        assert submission.claim == "The Earth has two moons."
