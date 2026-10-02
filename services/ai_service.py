def analyze_claim(claim, evidence):
    """
    Analyze a factual claim using retrieved evidence.

    CURRENT STATUS:
    Placeholder implementation.

    TODO:
    - Connect to the OpenAI API.
    - Read OPENAI_API_KEY from the environment.
    - Send the claim and retrieved evidence to the model.
    - Request a structured response.
    - Validate the returned values.
    - Handle API/network errors.

    Parameters:
        claim (str):
            The factual claim submitted by the user.

        evidence (list):
            Evidence returned by evidence_service.find_evidence().

            Expected format:
            [
                {
                    "publisher": "Reuters",
                    "title": "Article title",
                    "url": "https://...",
                    "snippet": "Relevant evidence..."
                }
            ]

    Returns:
        dict:
            {
                "verdict": "Supported | Misleading | Unsupported | Uncertain",
                "confidence": 0-100,
                "summary": "Short result summary",
                "explanation": "Detailed explanation"
            }

    IMPORTANT:
    Keep this return structure the same, because Flask depends on it.
    """

    return {
        "verdict": "Uncertain",
        "confidence": 75,
        "summary": "Placeholder analysis result.",
        "explanation": (
            "Real OpenAI analysis service not"
            "implemented yet."
        )
    }