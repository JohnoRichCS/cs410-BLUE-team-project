import os

import requests
from dotenv import load_dotenv


load_dotenv()


FACT_CHECK_API_URL = (
    "https://factchecktools.googleapis.com/v1alpha1/claims:search"
)


def find_evidence(claim):
    """
    Search Google's Fact Check Tools API for fact-check reviews
    related to the submitted claim.

    Returns a normalized list of evidence dictionaries.
    """

    if not claim or not claim.strip():
        return []

    api_key = os.getenv("GOOGLE_FACT_CHECK_API_KEY")

    if not api_key:
        print("Google Fact Check API key is not configured.")
        return []

    params = {
        "query": claim.strip(),
        "languageCode": "en",
        "pageSize": 5,
        "key": api_key
    }

    try:
        response = requests.get(
            FACT_CHECK_API_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return normalize_fact_checks(data)

    except requests.RequestException as error:
        print(f"Google Fact Check API error: {error}")
        return []

    except ValueError as error:
        print(f"Google Fact Check parsing error: {error}")
        return []


def normalize_fact_checks(data):
    """
    Convert Google's Fact Check API response into the
    evidence format expected by Faict.
    """

    evidence = []

    claims = data.get("claims", [])

    for claim in claims:
        claim_text = claim.get(
            "text",
            "Unknown claim"
        )

        reviews = claim.get(
            "claimReview",
            []
        )

        for review in reviews:
            publisher_data = review.get(
                "publisher",
                {}
            )

            publisher = publisher_data.get(
                "name",
                "Unknown Publisher"
            )

            title = review.get(
                "title",
                "Fact-check review"
            )

            url = review.get(
                "url",
                ""
            )

            rating = review.get(
                "textualRating",
                "No rating provided"
            )

            review_date = review.get(
                "reviewDate",
                "Unknown date"
            )

            snippet = (
                f'Fact-checked claim: "{claim_text}". '
                f"Rating: {rating}. "
                f"Review date: {review_date}."
            )

            evidence.append({
                "publisher": publisher,
                "title": title,
                "url": url,
                "snippet": snippet
            })

    return evidence