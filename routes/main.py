from flask import Blueprint, abort, render_template, request

from models import db
from models.submission import Submission
from models.evidence import Evidence
from services.ai_service import analyze_claim
from services.evidence_service import (
    find_evidence,
    process_evidence,
)
from services.claim_classifier import classify_claim


main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("index.html")


CLAIM_MIN_LENGTH = 10
CLAIM_MAX_LENGTH = 500


@main.route("/analyze", methods=["POST"])
def analyze():
    claim = request.form["claim"].strip()

    # 3.1.2 / 3.1.3: reject an empty or out-of-range claim before starting
    # the verification workflow.
    if not (CLAIM_MIN_LENGTH <= len(claim) <= CLAIM_MAX_LENGTH):
        return render_template(
            "index.html",
            error="Enter a claim between 10 and 500 characters."
        )

    # Issues #10 and #11: Classify the submitted claim
    classification = classify_claim(claim)

    # Retrieve evidence using the existing Google Fact Check
    # and Brave Search workflow.
    sources = find_evidence(claim)

    # Issues #12 and #13:
    # Apply topic-aware source ranking and relevance scoring.
    sources = process_evidence(
        claim,
        classification.get(
            "category",
            "Unknown"
        ),
        sources
    )

    result = analyze_claim(
        claim=claim,
        evidence=sources
    )

    submission = Submission(
        claim=claim,
        verdict=result["verdict"],
        confidence=result["confidence"],
        summary=result["summary"],
        explanation=result["explanation"]
    )

    db.session.add(submission)
    db.session.flush()  # assigns submission.id before Evidence rows reference it

    # Issue #14: persist each retained evidence item against this
    # verification so it can be reconstructed later (see /submissions/<id>).
    for source in sources:
        db.session.add(Evidence(
            submission_id=submission.id,
            title=source.get("title", "Untitled source"),
            url=source.get("url", ""),
            publisher=source.get("publisher"),
            excerpt=source.get("snippet")
        ))

    db.session.commit()

    return render_template(
        "results.html",
        claim=claim,
        result=result,
        sources=sources,
        classification=classification
    )


@main.route("/history")
def history():
    saved_submissions = (
        Submission.query
        .order_by(Submission.created_at.desc())
        .all()
    )

    return render_template(
        "history.html",
        submissions=saved_submissions
    )


@main.route("/submissions/<int:submission_id>")
def submission_detail(submission_id):
    submission = db.session.get(Submission, submission_id)

    if submission is None:
        abort(404)

    return render_template(
        "detail.html",
        submission=submission,
        evidence_items=submission.evidence_items
    )


@main.route("/submissions")
def submissions():
    saved_submissions = Submission.query.all()

    return {
        "submissions": [
            {
                "id": item.id,
                "claim": item.claim,
                "verdict": item.verdict,
                "confidence": item.confidence,
                "summary": item.summary,
                "explanation": item.explanation
            }
            for item in saved_submissions
        ]
    }