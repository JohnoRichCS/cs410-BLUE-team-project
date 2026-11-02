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


CLAIM_MIN_LENGTH = 10
CLAIM_MAX_LENGTH = 500

EVIDENCE_UNAVAILABLE_MESSAGE = (
    "Evidence sources are temporarily unavailable."
)


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/analyze", methods=["POST"])
def analyze():
    claim = request.form["claim"].strip()

    # 3.1.2 / 3.1.3:
    # Reject an empty or out-of-range claim before
    # starting the verification workflow.
    if not (
        CLAIM_MIN_LENGTH
        <= len(claim)
        <= CLAIM_MAX_LENGTH
    ):
        return render_template(
            "index.html",
            error="Enter a claim between 10 and 500 characters."
        )

    # Issues #10 and #11:
    # Classify the submitted claim.
    classification = classify_claim(
        claim
    )

    # Issue #20 / requirement 3.4.4:
    # Retrieve evidence and distinguish total retrieval
    # failure from a legitimate search with no results.
    raw_sources = find_evidence(
        claim
    )

    sources_unavailable = (
        raw_sources is None
    )

    if sources_unavailable:
        sources = []

        result = {
            "verdict": "Unable to verify",
            "confidence": 0,
            "summary": "Evidence retrieval failed.",
            "explanation": EVIDENCE_UNAVAILABLE_MESSAGE
        }

    else:
        sources = raw_sources

        # Issues #12 and #13:
        # Apply topic-aware source ranking and relevance
        # scoring only when evidence retrieval succeeded.
        sources = process_evidence(
            claim,
            classification.get(
                "category",
                "Unknown"
            ),
            sources
        )

        # Generate the fact-check result using the
        # processed evidence.
        result = analyze_claim(
            claim=claim,
            evidence=sources
        )

    # Issue #14:
    # Save the completed verification, including the
    # classifier topic.
    submission = Submission(
        claim=claim,
        verdict=result["verdict"],
        confidence=result["confidence"],
        summary=result["summary"],
        explanation=result["explanation"],
        topic=classification.get(
            "category",
            "Unclassified"
        )
    )

    db.session.add(
        submission
    )

    # Assign submission.id before Evidence rows
    # reference it.
    db.session.flush()

    # Issue #14:
    # Persist each retained and processed evidence item.
    for source in sources:
        db.session.add(
            Evidence(
                submission_id=submission.id,
                title=source.get(
                    "title",
                    "Untitled source"
                ),
                url=source.get(
                    "url",
                    ""
                ),
                publisher=source.get(
                    "publisher"
                ),
                excerpt=source.get(
                    "snippet"
                ),
                relevance=source.get(
                    "relevance_score"
                )
            )
        )

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
        .order_by(
            Submission.created_at.desc()
        )
        .all()
    )

    return render_template(
        "history.html",
        submissions=saved_submissions
    )


@main.route("/submissions/<int:submission_id>")
def submission_detail(submission_id):
    submission = db.session.get(
        Submission,
        submission_id
    )

    if submission is None:
        abort(404)

    return render_template(
        "detail.html",
        submission=submission,
        evidence_items=submission.evidence_items
    )


@main.route("/submissions")
def submissions():
    saved_submissions = (
        Submission.query.all()
    )

    return {
        "submissions": [
            {
                "id": item.id,
                "claim": item.claim,
                "verdict": item.verdict,
                "confidence": item.confidence,
                "summary": item.summary,
                "explanation": item.explanation,
                "topic": item.topic
            }
            for item in saved_submissions
        ]
    }