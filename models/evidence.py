from models import db


class Evidence(db.Model):
    """
    Stores one retained evidence source for a completed verification.

    Linked to its parent Submission so a saved verification's
    full evidence set can be reconstructed later.

    The relevance field stores the score assigned by the
    evidence relevance-scoring pipeline when available.
    """

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    submission_id = db.Column(
        db.Integer,
        db.ForeignKey("submission.id"),
        nullable=False
    )

    title = db.Column(
        db.Text,
        nullable=False
    )

    url = db.Column(
        db.Text,
        nullable=False
    )

    publisher = db.Column(
        db.Text,
        nullable=True
    )

    excerpt = db.Column(
        db.Text,
        nullable=True
    )

    relevance = db.Column(
        db.Float,
        nullable=True
    )

    submission = db.relationship(
        "Submission",
        backref=db.backref(
            "evidence_items",
            lazy=True
        )
    )

    def __repr__(self):
        return (
            f"<Evidence {self.id} "
            f"for Submission {self.submission_id}>"
        )