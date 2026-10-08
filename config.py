import os

from dotenv import load_dotenv


load_dotenv()


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = (
        os.getenv("SECRET_KEY")
        or "dev-secret-key"
    )

    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DATABASE_URL")
        or "sqlite:///" + os.path.join(
            BASE_DIR,
            "faict.db"
        )
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    OPENAI_API_KEY = os.getenv(
        "OPENAI_API_KEY"
    )

    OPENAI_MODEL = os.getenv(
        "OPENAI_MODEL"
    )

    GOOGLE_FACT_CHECK_API_KEY = os.getenv(
        "GOOGLE_FACT_CHECK_API_KEY"
    )