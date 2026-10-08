import json
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def analyze_claim(claim, evidence):
    """
    Analyze a factual claim using retrieved evidence.

    Parameters:
        claim (str):
            User-submitted factual claim.

        evidence (list):
            Evidence dictionaries returned by find_evidence().

    Returns:
        dict:
            {
                "verdict": str,
                "confidence": int,
                "summary": str,
                "explanation": str
            }
    """

    # Reject empty claims
    if not claim or not claim.strip():
        return {
            "verdict": "Uncertain",
            "confidence": 0,
            "summary": "No claim was provided.",
            "explanation": "Faict cannot analyze an empty claim."
        }

    # If no evidence was found, do not call OpenAI.
    # Saves API usage and avoids giving confidence to a claim that has no supporting material.
    if not evidence:
        return {
            "verdict": "Uncertain",
            "confidence": 0,
            "summary": "No evidence was found for this claim.",
            "explanation": (
                "Faict could not find fact-check evidence related to the "
                "submitted claim, so the claim cannot be verified."
            )
        }

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-6-luna")

    if not api_key:
        return {
            "verdict": "Uncertain",
            "confidence": 0,
            "summary": "AI analysis is unavailable.",
            "explanation": "The OpenAI API key has not been configured."
        }

    client = OpenAI(api_key=api_key)

    evidence_text = format_evidence(evidence)

    instructions = """
You are the AI analysis component of Faict, an evidence-based
fact-checking application.

Analyze the submitted claim using ONLY the supplied evidence.

Do not invent facts, evidence, publishers, sources, citations, or URLs.

Choose exactly one verdict:

Supported:
The supplied evidence strongly supports the claim.

Misleading:
The claim contains some truth but omits important context,
exaggerates, or may lead the reader to an incorrect conclusion.

Unsupported:
The supplied evidence directly contradicts the claim.

Uncertain:
The supplied evidence is insufficient, unclear, conflicting,
irrelevant, or does not actually address the claim.

Confidence must be an integer from 0 to 100.

Confidence represents confidence in the verdict based on the supplied
evidence. It does NOT represent how likely the claim itself is to be true.

For an Uncertain verdict, confidence should generally remain below 70
because the available evidence is insufficient, unclear, or conflicting.

If the evidence is irrelevant or does not actually address the claim,
return Uncertain.

Return ONLY valid JSON in exactly this structure:

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
            "explanation": (
                "An error occurred while communicating with the OpenAI API."
            )
        }


def format_evidence(evidence):
    """
    Convert retrieved evidence into readable text for the AI model.
    """

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
    """
    Validate and normalize the structured AI response.
    """

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

    # Prevent confusing results such as "Uncertain - 99%".
    if verdict == "Uncertain":
        confidence = min(confidence, 69)

    return {
        "verdict": verdict,
        "confidence": confidence,
        "summary": str(
            result.get(
                "summary",
                "No summary was provided."
            )
        ),
        "explanation": str(
            result.get(
                "explanation",
                "No explanation was provided."
            )
        )
    }