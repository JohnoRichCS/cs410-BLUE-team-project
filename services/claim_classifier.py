import json
import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def default_classification():
    """Return a safe fallback if classification fails."""

    return {
        "category": "Unknown",
        "claim_type": "Unknown",
        "is_conditional": False,
        "conditions": [],
        "missing_context": []
    }


def classify_claim(claim):
    """
    Classify any factual claim using AI.

    Identifies:
    - Topic/category
    - Claim type
    - Whether the claim is conditional
    - Relevant conditions
    - Potential missing context
    """

    if not isinstance(claim, str) or not claim.strip():
        return default_classification()

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-6-luna")

    if not api_key:
        return default_classification()

    client = OpenAI(api_key=api_key)

    instructions = """
You are the claim classification component of FAÍCT,
a general-purpose fact-checking application.

Your job is to classify claims about ANY topic.

Do not restrict categories to education or financial aid.

Determine the most appropriate, concise topic category
based on the submitted claim.

Examples of possible categories:
Science, Health, Technology, Education, Finance,
Politics, History, Sports, Entertainment, Environment,
Business, Law, or any other relevant topic.

You may create new category names when appropriate.

Identify the type of claim, such as:
- Factual
- Statistical
- Causal
- Comparative
- Predictive
- Conditional
- Opinion
- Other

Determine whether the claim depends on an explicit
or clearly implied condition.

Identify conditions mentioned in the claim.

Identify important missing context that may be
necessary to verify the claim accurately.

Do not determine whether the claim is true or false.

Do not invent facts, evidence, or sources.

Return ONLY valid JSON in this exact structure:

{
    "category": "Topic category",
    "claim_type": "Factual",
    "is_conditional": false,
    "conditions": [],
    "missing_context": []
}
"""

    try:
        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=claim
        )

        result = json.loads(response.output_text.strip())

        return validate_classification(result)

    except Exception as error:
        print(f"Claim classification error: {error}")
        return default_classification()


def validate_classification(result):
    """Validate and normalize the AI classification."""

    if not isinstance(result, dict):
        return default_classification()

    valid_types = {
        "Factual",
        "Statistical",
        "Causal",
        "Comparative",
        "Predictive",
        "Conditional",
        "Opinion",
        "Other"
    }

    claim_type = result.get("claim_type", "Other")

    if claim_type not in valid_types:
        claim_type = "Other"

    category = result.get("category", "Unknown")

    if not isinstance(category, str) or not category.strip():
        category = "Unknown"

    is_conditional = result.get("is_conditional", False)

    if not isinstance(is_conditional, bool):
        is_conditional = False

    conditions = result.get("conditions", [])

    if not isinstance(conditions, list):
        conditions = []

    missing_context = result.get("missing_context", [])

    if not isinstance(missing_context, list):
        missing_context = []

    return {
        "category": category.strip(),
        "claim_type": claim_type,
        "is_conditional": is_conditional,
        "conditions": [
            str(item) for item in conditions
        ],
        "missing_context": [
            str(item) for item in missing_context
        ]
    }