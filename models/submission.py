from datetime import datetime
from models import db


class Submission(db.Model):
    """
    Temporary prototype model.

    Currently stores the submitted claim and its analysis
    in one table.

    TODO DATABASE:

    """

    id = db.Column(db.Integer, primary_key=True)

    claim = db.Column(
        db.Text,
        nullable=False
    )

    # Populated once claim classification (issue #10) is merged into
    # main; until then this defaults to "Unclassified" rather than
    # depending on the unmerged feature/claim-classification branch.
    topic = db.Column(
        db.String(100),
        nullable=False,
        default="Unclassified"
    )

    verdict = db.Column(
        db.String(50),
        nullable=False
    )

    confidence = db.Column(
        db.Integer,
        nullable=False
    )

    summary = db.Column(
        db.Text,
        nullable=False
    )

    explanation = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Submission {self.id}>"