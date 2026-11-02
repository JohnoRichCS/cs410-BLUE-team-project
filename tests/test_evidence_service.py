import requests

from services.evidence_service import (
    TOPIC_TRUSTED_DOMAINS,
    add_relevance_scores,
    calculate_relevance,
    clean_snippet,
    find_evidence,
    find_fact_check_evidence,
    find_web_evidence,
    get_domain,
    is_topic_priority_source,
    is_trusted_domain,
    normalize_brave_results,
    normalize_fact_checks,
    normalize_topic,
    process_evidence,
    rank_evidence,
    remove_duplicate_evidence,
)


class FakeResponse:
    """
    Minimal stand-in for requests.Response.
    """

    def __init__(self, json_data):
        self._json_data = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


def raise_request_exception(
    *args,
    **kwargs
):
    raise requests.RequestException(
        "simulated network failure"
    )


def test_clean_snippet_removes_html():
    raw = (
        "<strong>You may repay aid</strong> "
        "&quot;depending on enrollment&quot;"
    )

    cleaned = clean_snippet(
        raw
    )

    assert cleaned == (
        'You may repay aid "depending on enrollment"'
    )


def test_clean_snippet_decodes_apostrophe():
    raw = (
        "didn&#x27;t complete "
        "<strong>60 percent</strong>"
    )

    cleaned = clean_snippet(
        raw
    )

    assert cleaned == (
        "didn't complete 60 percent"
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
                        "url": (
                            "https://example.com/fact-check"
                        ),
                        "title": "Earth is not flat",
                        "reviewDate": (
                            "2026-01-01T00:00:00Z"
                        ),
                        "textualRating": "False"
                    }
                ]
            }
        ]
    }

    evidence = normalize_fact_checks(
        fake_response
    )

    assert len(evidence) == 1

    assert (
        evidence[0]["publisher"]
        == "Example Fact Checker"
    )

    assert (
        evidence[0]["title"]
        == "Earth is not flat"
    )

    assert (
        evidence[0]["url"]
        == "https://example.com/fact-check"
    )

    assert (
        "False"
        in evidence[0]["snippet"]
    )


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

    evidence = normalize_fact_checks(
        fake_response
    )

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
                    "title": (
                        "<strong>NASA</strong> explanation"
                    ),
                    "url": (
                        "https://www.nasa.gov/example"
                    ),
                    "description": (
                        "Scientific "
                        "<strong>explanation</strong>."
                    )
                },
                {
                    "title": "Random Blog",
                    "url": (
                        "https://randomblog.example/article"
                    ),
                    "description": (
                        "Untrusted source."
                    )
                },
                {
                    "title": "Reuters report",
                    "url": (
                        "https://www.reuters.com/example"
                    ),
                    "description": (
                        "Reuters &quot;reporting&quot;."
                    )
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

    assert (
        "https://www.nasa.gov/example"
        in urls
    )

    assert (
        "https://www.reuters.com/example"
        in urls
    )

    assert (
        "https://randomblog.example/article"
        not in urls
    )

    nasa = next(
        item
        for item in evidence
        if "nasa.gov" in item["url"]
    )

    assert (
        nasa["title"]
        == "NASA explanation"
    )

    assert (
        nasa["snippet"]
        == "Scientific explanation."
    )

    reuters = next(
        item
        for item in evidence
        if "reuters.com" in item["url"]
    )

    assert (
        reuters["snippet"]
        == 'Reuters "reporting".'
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


# ISSUE #12:
# TOPIC-AWARE SOURCE RANKING


def test_financial_aid_topic_domains():
    domains = TOPIC_TRUSTED_DOMAINS[
        "financial_aid"
    ]

    assert "studentaid.gov" in domains
    assert "odu.edu" in domains


def test_education_finance_maps_to_financial_aid():
    assert (
        normalize_topic(
            "Education Finance"
        )
        == "financial_aid"
    )


def test_education_and_finance_maps_to_financial_aid():
    assert (
        normalize_topic(
            "Education and Finance"
        )
        == "financial_aid"
    )


def test_financial_aid_maps_to_financial_aid():
    assert (
        normalize_topic(
            "Financial Aid"
        )
        == "financial_aid"
    )


def test_topic_priority_source_exact_domain():
    assert is_topic_priority_source(
        "https://studentaid.gov/example",
        "financial_aid"
    )


def test_topic_priority_source_subdomain():
    assert is_topic_priority_source(
        "https://www.odu.edu/financial-aid",
        "financial_aid"
    )


def test_financial_aid_primary_sources_rank_first():
    items = [
        {
            "url": "https://www.uga.edu/article",
            "relevance_score": 0.95
        },
        {
            "url": "https://studentaid.gov/article",
            "relevance_score": 0.60
        },
        {
            "url": (
                "https://www.odu.edu/financial-aid"
            ),
            "relevance_score": 0.55
        },
    ]

    ranked = rank_evidence(
        items,
        "financial_aid"
    )

    assert (
        "studentaid.gov"
        in ranked[0]["url"]
    )

    assert (
        "odu.edu"
        in ranked[1]["url"]
    )

    assert (
        "uga.edu"
        in ranked[2]["url"]
    )


# ISSUE #13:
# EVIDENCE RELEVANCE SCORING


def test_relevance_score_exact_overlap():
    claim = (
        "alpha beta gamma delta epsilon"
    )

    evidence = {
        "title": "alpha beta",
        "snippet": "gamma delta"
    }

    assert (
        calculate_relevance(
            claim,
            evidence
        )
        == 0.80
    )


def test_relevance_score_zero_when_no_overlap():
    claim = (
        "alpha beta gamma"
    )

    evidence = {
        "title": "delta epsilon",
        "snippet": "zeta eta"
    }

    assert (
        calculate_relevance(
            claim,
            evidence
        )
        == 0.0
    )


def test_relevance_orders_within_same_group():
    items = [
        {
            "url": "https://example.com/a",
            "relevance_score": 0.40
        },
        {
            "url": "https://example.com/b",
            "relevance_score": 0.80
        }
    ]

    ranked = rank_evidence(
        items,
        "other"
    )

    assert (
        ranked[0]["relevance_score"]
        == 0.80
    )

    assert (
        ranked[1]["relevance_score"]
        == 0.40
    )


def test_relevance_threshold_removes_low_score():
    claim = (
        "alpha beta gamma delta epsilon"
    )

    items = [
        {
            "publisher": "Example",
            "title": "alpha",
            "snippet": "",
            "url": "https://example.com/a"
        },
        {
            "publisher": "Example",
            "title": "alpha beta",
            "snippet": "",
            "url": "https://example.com/b"
        }
    ]

    results = add_relevance_scores(
        claim,
        items
    )

    assert len(results) == 2

    assert (
        results[0]["relevance_score"]
        == 0.20
    )

    assert (
        results[1]["relevance_score"]
        == 0.40
    )


def test_relevance_below_threshold_is_removed():
    claim = (
        "alpha beta gamma delta epsilon zeta"
    )

    items = [
        {
            "publisher": "Example",
            "title": "alpha",
            "snippet": "",
            "url": "https://example.com/a"
        }
    ]

    results = add_relevance_scores(
        claim,
        items
    )

    assert results == []


def test_process_evidence_limits_results_to_five():
    claim = "financial aid withdrawal"

    evidence = []

    for index in range(10):
        evidence.append({
            "publisher": "Example",
            "title": (
                f"financial aid withdrawal {index}"
            ),
            "snippet": (
                "financial aid withdrawal"
            ),
            "url": (
                f"https://example.edu/{index}"
            )
        })

    results = process_evidence(
        claim,
        "Education Finance",
        evidence
    )

    assert len(results) == 5


# ISSUE #20:
# EVIDENCE RETRIEVAL FAILURE HANDLING


def test_fact_check_returns_not_failed_when_key_missing(
    monkeypatch
):
    monkeypatch.delenv(
        "GOOGLE_FACT_CHECK_API_KEY",
        raising=False
    )

    evidence, failed = (
        find_fact_check_evidence(
            "Any claim"
        )
    )

    assert evidence == []
    assert failed is False


def test_fact_check_returns_failed_on_request_exception(
    monkeypatch
):
    monkeypatch.setenv(
        "GOOGLE_FACT_CHECK_API_KEY",
        "fake-key"
    )

    monkeypatch.setattr(
        "services.evidence_service.requests.get",
        raise_request_exception
    )

    evidence, failed = (
        find_fact_check_evidence(
            "Any claim"
        )
    )

    assert evidence == []
    assert failed is True


def test_fact_check_returns_not_failed_on_success_with_no_results(
    monkeypatch
):
    monkeypatch.setenv(
        "GOOGLE_FACT_CHECK_API_KEY",
        "fake-key"
    )

    monkeypatch.setattr(
        "services.evidence_service.requests.get",
        lambda *a, **k: FakeResponse(
            {
                "claims": []
            }
        )
    )

    evidence, failed = (
        find_fact_check_evidence(
            "Any claim"
        )
    )

    assert evidence == []
    assert failed is False


def test_web_evidence_returns_failed_on_request_exception(
    monkeypatch
):
    monkeypatch.setenv(
        "BRAVE_SEARCH_API_KEY",
        "fake-key"
    )

    monkeypatch.setattr(
        "services.evidence_service.requests.get",
        raise_request_exception
    )

    evidence, failed = (
        find_web_evidence(
            "Any claim"
        )
    )

    assert evidence == []
    assert failed is True


def test_find_evidence_returns_none_when_both_sources_fail(
    monkeypatch
):
    monkeypatch.setenv(
        "GOOGLE_FACT_CHECK_API_KEY",
        "fake-key"
    )

    monkeypatch.setenv(
        "BRAVE_SEARCH_API_KEY",
        "fake-key"
    )

    monkeypatch.setattr(
        "services.evidence_service.requests.get",
        raise_request_exception
    )

    assert (
        find_evidence(
            "Any claim with enough length"
        )
        is None
    )


def test_find_evidence_returns_empty_list_when_one_source_fails(
    monkeypatch
):
    monkeypatch.setenv(
        "GOOGLE_FACT_CHECK_API_KEY",
        "fake-key"
    )

    monkeypatch.setenv(
        "BRAVE_SEARCH_API_KEY",
        "fake-key"
    )

    def fake_get(
        url,
        *args,
        **kwargs
    ):
        if (
            url
            == FACT_CHECK_API_URL
        ):
            raise requests.RequestException(
                "simulated network failure"
            )

        return FakeResponse({
            "web": {
                "results": []
            }
        })

    def fake_get(
        url,
        *args,
        **kwargs
    ):
        if url == (
            "https://factchecktools.googleapis.com/"
            "v1alpha1/claims:search"
        ):
            raise requests.RequestException(
                "simulated network failure"
            )

        return FakeResponse({
            "web": {
                "results": []
            }
        })

    monkeypatch.setattr(
        "services.evidence_service.requests.get",
        fake_get
    )

    assert (
        find_evidence(
            "Any claim with enough length"
        )
        == []
    )


def test_find_evidence_returns_empty_list_when_no_keys_configured(
    monkeypatch
):
    monkeypatch.delenv(
        "GOOGLE_FACT_CHECK_API_KEY",
        raising=False
    )

    monkeypatch.delenv(
        "BRAVE_SEARCH_API_KEY",
        raising=False
    )

    assert (
        find_evidence(
            "Any claim with enough length"
        )
        == []
    )