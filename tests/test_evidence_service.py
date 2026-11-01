import requests

from services.evidence_service import (
    find_evidence,
    find_fact_check_evidence,
    find_web_evidence,
    get_domain,
    is_trusted_domain,
    normalize_brave_results,
    normalize_fact_checks,
    remove_duplicate_evidence,
)


class FakeResponse:
    """Minimal stand-in for requests.Response used by the tests below."""

    def __init__(self, json_data):
        self._json_data = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


def raise_request_exception(*args, **kwargs):
    raise requests.RequestException("simulated network failure")


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


# 4.4 / 3.4.4: distinguishing a genuine source failure from a source
# that was simply never configured or that legitimately found nothing.


def test_fact_check_returns_not_failed_when_key_missing(monkeypatch):
    monkeypatch.delenv("GOOGLE_FACT_CHECK_API_KEY", raising=False)

    evidence, failed = find_fact_check_evidence("Any claim")

    assert evidence == []
    assert failed is False


def test_fact_check_returns_failed_on_request_exception(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACT_CHECK_API_KEY", "fake-key")
    monkeypatch.setattr(
        "services.evidence_service.requests.get",
        raise_request_exception
    )

    evidence, failed = find_fact_check_evidence("Any claim")

    assert evidence == []
    assert failed is True


def test_fact_check_returns_not_failed_on_success_with_no_results(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACT_CHECK_API_KEY", "fake-key")
    monkeypatch.setattr(
        "services.evidence_service.requests.get",
        lambda *a, **k: FakeResponse({"claims": []})
    )

    evidence, failed = find_fact_check_evidence("Any claim")

    assert evidence == []
    assert failed is False


def test_web_evidence_returns_failed_on_request_exception(monkeypatch):
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "fake-key")
    monkeypatch.setattr(
        "services.evidence_service.requests.get",
        raise_request_exception
    )

    evidence, failed = find_web_evidence("Any claim")

    assert evidence == []
    assert failed is True


def test_find_evidence_returns_none_when_both_sources_fail(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACT_CHECK_API_KEY", "fake-key")
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "fake-key")
    monkeypatch.setattr(
        "services.evidence_service.requests.get",
        raise_request_exception
    )

    assert find_evidence("Any claim with enough length") is None


def test_find_evidence_returns_empty_list_when_one_source_fails(monkeypatch):
    """One source fails, the other succeeds but finds nothing: this is
    NOT total failure, so an empty list (not None) is returned."""

    monkeypatch.setenv("GOOGLE_FACT_CHECK_API_KEY", "fake-key")
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "fake-key")

    def fake_get(url, *args, **kwargs):
        if url == "https://factchecktools.googleapis.com/v1alpha1/claims:search":
            raise requests.RequestException("simulated network failure")
        return FakeResponse({"web": {"results": []}})

    monkeypatch.setattr(
        "services.evidence_service.requests.get",
        fake_get
    )

    assert find_evidence("Any claim with enough length") == []


def test_find_evidence_returns_empty_list_when_no_keys_configured(monkeypatch):
    """Sources that are simply unconfigured are not a failure."""

    monkeypatch.delenv("GOOGLE_FACT_CHECK_API_KEY", raising=False)
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

    assert find_evidence("Any claim with enough length") == []