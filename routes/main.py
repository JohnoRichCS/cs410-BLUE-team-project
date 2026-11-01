from flask import Blueprint, render_template, request

from models import db
from models.submission import Submission
from services.ai_service import analyze_claim
from services.evidence_service import find_evidence


main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("index.html")


EVIDENCE_UNAVAILABLE_MESSAGE = "Evidence sources are temporarily unavailable."


@main.route("/analyze", methods=["POST"])
def analyze():
    claim = request.form["claim"]

    raw_sources = find_evidence(claim)

    # 4.4: find_evidence() returns None specifically when every attempted
    # evidence source failed (as opposed to succeeding and finding
    # nothing), so that case gets its own message rather than being
    # treated as "no evidence exists for this claim."
    sources_unavailable = raw_sources is None
    sources = raw_sources or []

    if sources_unavailable:
        result = {
            "verdict": "Uncertain",
            "confidence": 0,
            "summary": "Evidence retrieval failed.",
            "explanation": EVIDENCE_UNAVAILABLE_MESSAGE
        }
    else:
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
    db.session.commit()

    return render_template(
        "results.html",
        claim=claim,
        result=result,
        sources=sources
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