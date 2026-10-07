import json
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def analyze_claim(claim, evidence):
    """
    Analyze a factual claim using retrieved evidence.

    Returns:
        {
            "verdict": str,
            "confidence": int,
            "summary": str,
            "explanation": str
        }
    """

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-6-luna")

    if not api_key:
        return {
            "verdict": "Uncertain",
            "confidence": 0,
            "summary": "AI analysis is unavailable.",
            "explanation": "The OpenAI API key is not configured."
        }

    client = OpenAI(api_key=api_key)

    evidence_text = format_evidence(evidence)

    instructions = """
You are the AI analysis component of Faict, an evidence-based
fact-checking application.

Analyze the submitted claim using only the supplied evidence.

Do not invent sources, facts, publishers, URLs, or evidence.

Choose exactly one verdict:

Supported:
The supplied evidence strongly supports the claim.

Misleading:
The claim contains some truth but omits important context,
exaggerates, or may lead the reader to an incorrect conclusion.

Unsupported:
The supplied evidence contradicts the claim.

Uncertain:
The supplied evidence is insufficient, unclear, or conflicting.

Confidence must be an integer from 0 to 100 and should represent
how confident the analysis is based on the supplied evidence.

Return only valid JSON in this exact structure:

{
    "verdict": "Supported",
    "confidence": 90,
    "summary": "One short sentence summarizing the result.",
    "explanation": "A clear explanation based on the supplied evidence."
}
"""

    user_input = f"""
CLAIM:
{claim}

EVIDENCE:
{evidence_text}
"""

    try:
        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=user_input
        )

        raw_output = response.output_text.strip()
        result = json.loads(raw_output)

        return validate_result(result)

    except json.JSONDecodeError:
        return {
            "verdict": "Uncertain",
            "confidence": 0,
            "summary": "The AI returned an invalid response.",
            "explanation": "Faict could not interpret the AI analysis."
        }

    except Exception as error:
        print(f"OpenAI API error: {error}")

        return {
            "verdict": "Uncertain",
            "confidence": 0,
            "summary": "AI analysis could not be completed.",
            "explanation": "An error occurred while communicating with OpenAI."
        }


def format_evidence(evidence):
    if not evidence:
        return "No evidence was provided."

    formatted_sources = []

    for index, source in enumerate(evidence, start=1):
        formatted_sources.append(
            f"""
Source {index}
Publisher: {source.get("publisher", "Unknown")}
Title: {source.get("title", "Unknown")}
URL: {source.get("url", "Unknown")}
Evidence: {source.get("snippet", "No snippet available")}
"""
        )

    return "\n".join(formatted_sources)


def validate_result(result):
    valid_verdicts = {
        "Supported",
        "Misleading",
        "Unsupported",
        "Uncertain"
    }

    verdict = result.get("verdict", "Uncertain")

    if verdict not in valid_verdicts:
        verdict = "Uncertain"

    try:
        confidence = int(result.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0

    confidence = max(0, min(100, confidence))

    return {
        "verdict": verdict,
        "confidence": confidence,
        "summary": str(
            result.get("summary", "No summary provided.")
        ),
        "explanation": str(
            result.get("explanation", "No explanation provided.")
        )
    }