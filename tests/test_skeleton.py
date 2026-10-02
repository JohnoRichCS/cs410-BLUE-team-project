from models.submission import Submission


def test_faict_skeleton_workflow(app, client):
    """
    Tests the current Faíct skeleton from submission through storage.

    This verifies that:
    1. The homepage loads.
    2. A claim can be submitted.
    3. Placeholder analysis is displayed.
    4. Placeholder evidence is displayed.
    5. The submission is saved to the database.
    """

    # Homepage works
    response = client.get("/")

    assert response.status_code == 200


    # Claim submission
    test_claim = "The Earth has two moons."

    response = client.post(
        "/analyze",
        data={"claim": test_claim}
    )

    assert response.status_code == 200


    # Placeholder analysis reached the result page
    assert b"Uncertain" in response.data
    assert b"75%" in response.data


    # Placeholder evidence reached the result page
    assert b"Associated Press" in response.data
    assert b"Reuters" in response.data


    # Submission was saved
    with app.app_context():

        submission = Submission.query.first()

        assert submission is not None
        assert submission.claim == test_claim
        assert submission.verdict == "Uncertain"
        assert submission.confidence == 75