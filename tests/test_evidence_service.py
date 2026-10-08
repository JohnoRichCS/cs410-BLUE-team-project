from services.evidence_service import (
    get_domain,
    is_trusted_domain,
    normalize_brave_results,
    normalize_fact_checks,
    remove_duplicate_evidence,
)


def test_normalize_fact_checks():
    fake_response = {
        "claims": [
            {
                "text": "The Earth is flat.",
                "claimReview": [
                    {
                        "publisher": {
                            "name": "Example Fact Checker"
                        },
                        "url": "https://example.com/fact-check",
                        "title": "Earth is not flat",
                        "reviewDate": "2026-01-01T00:00:00Z",
                        "textualRating": "False"
                    }
                ]
            }
        ]
    }

    evidence = normalize_fact_checks(fake_response)

    assert len(evidence) == 1
    assert evidence[0]["publisher"] == "Example Fact Checker"
    assert evidence[0]["title"] == "Earth is not flat"
    assert evidence[0]["url"] == "https://example.com/fact-check"
    assert "False" in evidence[0]["snippet"]


def test_empty_fact_check_response():
    evidence = normalize_fact_checks({})

    assert evidence == []


def test_claim_without_reviews():
    fake_response = {
        "claims": [
            {
                "text": "Some claim"
            }
        ]
    }

    evidence = normalize_fact_checks(fake_response)

    assert evidence == []


def test_get_domain():
    domain = get_domain(
        "https://www.nasa.gov/example"
    )

    assert domain == "nasa.gov"


def test_trusted_exact_domain():
    assert is_trusted_domain(
        "reuters.com"
    )


def test_trusted_subdomain():
    assert is_trusted_domain(
        "news.reuters.com"
    )


def test_gov_domain_is_trusted():
    assert is_trusted_domain(
        "example.gov"
    )


def test_edu_domain_is_trusted():
    assert is_trusted_domain(
        "odu.edu"
    )


def test_military_domain_is_trusted():
    assert is_trusted_domain(
        "army.mil"
    )


def test_untrusted_domain_is_rejected():
    assert not is_trusted_domain(
        "randomsite.example"
    )


def test_normalize_brave_results_filters_sources():
    fake_response = {
        "web": {
            "results": [
                {
                    "title": "NASA explanation",
                    "url": "https://www.nasa.gov/example",
                    "description": "Scientific explanation."
                },
                {
                    "title": "Random Blog",
                    "url": "https://randomblog.example/article",
                    "description": "Untrusted source."
                },
                {
                    "title": "Reuters report",
                    "url": "https://www.reuters.com/example",
                    "description": "Reuters reporting."
                }
            ]
        }
    }

    evidence = normalize_brave_results(
        fake_response
    )

    assert len(evidence) == 2

    urls = [
        item["url"]
        for item in evidence
    ]

    assert "https://www.nasa.gov/example" in urls
    assert "https://www.reuters.com/example" in urls
    assert (
        "https://randomblog.example/article"
        not in urls
    )


def test_duplicate_sources_are_removed():
    evidence = [
        {
            "publisher": "NASA",
            "title": "Example",
            "url": "https://nasa.gov/example",
            "snippet": "Example evidence."
        },
        {
            "publisher": "NASA",
            "title": "Same Example",
            "url": "https://nasa.gov/example",
            "snippet": "Duplicate evidence."
        }
    ]

    result = remove_duplicate_evidence(
        evidence
    )

    assert len(result) == 1