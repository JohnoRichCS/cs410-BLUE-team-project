import os
import re
from html import unescape
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


load_dotenv()


FACT_CHECK_API_URL = (
    "https://factchecktools.googleapis.com/v1alpha1/claims:search"
)

BRAVE_SEARCH_API_URL = (
    "https://api.search.brave.com/res/v1/web/search"
)


# TRUSTED SOURCE ALLOWLIST

TRUSTED_DOMAINS = {

    # WIRE SERVICES / INTERNATIONAL NEWS

    "reuters.com",
    "apnews.com",
    "afp.com",
    "bbc.com",
    "bbc.co.uk",
    "npr.org",
    "pbs.org",
    "aljazeera.com",
    "dw.com",
    "france24.com",
    "cbc.ca",
    "abc.net.au",

    # MAJOR U.S. NEWS ORGANIZATIONS

    "nytimes.com",
    "washingtonpost.com",
    "usatoday.com",
    "wsj.com",
    "latimes.com",
    "chicagotribune.com",
    "bostonglobe.com",

    "cnn.com",
    "nbcnews.com",
    "cbsnews.com",
    "abcnews.go.com",
    "foxnews.com",

    "politico.com",
    "thehill.com",
    "axios.com",

    # FACT-CHECKING ORGANIZATIONS

    "factcheck.org",
    "politifact.com",
    "snopes.com",
    "fullfact.org",
    "leadstories.com",
    "sciencefeedback.co",
    "healthfeedback.org",
    "checkyourfact.com",
    "aap.com.au",

    # SCIENCE JOURNALS / PUBLICATIONS

    "nature.com",
    "science.org",
    "sciencemag.org",
    "scientificamerican.com",
    "newscientist.com",
    "nationalgeographic.com",

    "pnas.org",
    "cell.com",
    "thelancet.com",
    "nejm.org",
    "bmj.com",
    "jamanetwork.com",

    # SPACE / EARTH / WEATHER / CLIMATE

    "nasa.gov",
    "noaa.gov",
    "usgs.gov",
    "weather.gov",
    "climate.gov",
    "nps.gov",

    "ucar.edu",
    "ucar.org",

    # HEALTH / MEDICINE

    "cdc.gov",
    "nih.gov",
    "fda.gov",
    "hhs.gov",
    "medlineplus.gov",

    "who.int",

    "mayoclinic.org",
    "clevelandclinic.org",
    "hopkinsmedicine.org",
    "health.harvard.edu",

    # U.S. GOVERNMENT / PUBLIC DATA

    "usa.gov",
    "whitehouse.gov",
    "congress.gov",
    "senate.gov",
    "house.gov",

    "supremecourt.gov",
    "uscourts.gov",

    "justice.gov",
    "fbi.gov",
    "state.gov",
    "defense.gov",
    "dhs.gov",

    "census.gov",
    "bls.gov",
    "bea.gov",

    "treasury.gov",
    "federalreserve.gov",

    "irs.gov",
    "ssa.gov",

    "energy.gov",
    "epa.gov",
    "transportation.gov",
    "dot.gov",

    "education.gov",
    "ed.gov",

    "commerce.gov",
    "agriculture.gov",
    "usda.gov",

    "sec.gov",
    "ftc.gov",
    "fcc.gov",
    "cisa.gov",

    # INTERNATIONAL / MULTINATIONAL ORGANIZATIONS

    "un.org",
    "unesco.org",
    "unicef.org",

    "worldbank.org",
    "imf.org",
    "oecd.org",

    "europa.eu",
    "ec.europa.eu",

    "gov.uk",
    "parliament.uk",

    "canada.ca",
    "statcan.gc.ca",

    "australia.gov.au",
    "abs.gov.au",

    # ECONOMICS / FINANCIAL DATA

    "fred.stlouisfed.org",
    "stlouisfed.org",

    # LAW / LEGAL INFORMATION

    "law.cornell.edu",

    # UNIVERSITY / ACADEMIC SOURCES

    "harvard.edu",
    "mit.edu",
    "stanford.edu",
    "yale.edu",
    "princeton.edu",

    "berkeley.edu",
    "ucla.edu",
    "columbia.edu",
    "cornell.edu",

    "upenn.edu",
    "duke.edu",
    "northwestern.edu",

    "umich.edu",
    "utexas.edu",
    "gatech.edu",

    "virginia.edu",
    "vt.edu",
    "wm.edu",
    "odu.edu",

    # TECHNOLOGY / CYBERSECURITY

    "nist.gov",
    "microsoft.com",
    "apple.com",
    "google.com",
    "cloud.google.com",
    "aws.amazon.com",
    "mozilla.org",

    # REFERENCE / GENERAL KNOWLEDGE

    "britannica.com",
    "smithsonianmag.com",
    "si.edu",

    # PROFESSIONAL / TECHNICAL ORGANIZATIONS

    "ieee.org",
    "acm.org",

    # SPORTS / OFFICIAL LEAGUE DATA

    "nba.com",
    "nfl.com",
    "mlb.com",
    "nhl.com",
    "ncaa.com",

    # ELECTION / CIVIC INFORMATION

    "fec.gov",
    "eac.gov",
}


# ISSUE #12:
# TOPIC-AWARE SOURCE RANKING

TOPIC_TRUSTED_DOMAINS = {
    "financial_aid": {
        "studentaid.gov",
        "odu.edu",
    }
}


# ISSUE #13:
# EVIDENCE RELEVANCE SCORING

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "one",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "will",
    "with",
}


MIN_RELEVANCE = 0.20
MAX_EVIDENCE_ITEMS = 5


def find_evidence(claim):
    """
    Retrieve evidence for a submitted claim.

    Search order:

    1. Google Fact Check Tools API
    2. Brave Search API fallback

    Returns:
        list[dict]:
            Evidence was retrieved successfully.

        []:
            Retrieval worked but no evidence was found,
            or no external API is configured.

        None:
            Every configured evidence source failed.
    """

    if not claim or not claim.strip():
        return []

    claim = claim.strip()

    fact_check_results, fact_check_failed = (
        find_fact_check_evidence(claim)
    )

    if fact_check_results:
        return remove_duplicate_evidence(
            fact_check_results
        )

    web_results, web_failed = (
        find_web_evidence(claim)
    )

    if web_results:
        return remove_duplicate_evidence(
            web_results
        )

    # Issue #20 / requirement 3.4.4:
    # Only return None when all configured evidence
    # sources actually failed.
    if fact_check_failed and web_failed:
        return None

    return []


def find_fact_check_evidence(claim):
    """
    Search Google's Fact Check Tools API.

    Returns:
        tuple:
            (evidence_items, failed)

    failed is True only when the configured service
    was attempted and failed.
    """

    api_key = os.getenv(
        "GOOGLE_FACT_CHECK_API_KEY"
    )

    if not api_key:
        print(
            "Google Fact Check API key is not configured."
        )

        return [], False

    params = {
        "query": claim,
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

        return (
            normalize_fact_checks(data),
            False
        )

    except requests.RequestException as error:
        print(
            f"Google Fact Check API error: {error}"
        )

        return [], True

    except ValueError as error:
        print(
            f"Google Fact Check parsing error: {error}"
        )

        return [], True


def find_web_evidence(claim):
    """
    Search Brave Search when Google Fact Check does not
    return evidence.

    Returns:
        tuple:
            (evidence_items, failed)

    failed is True only when the configured service
    was attempted and failed.
    """

    api_key = os.getenv(
        "BRAVE_SEARCH_API_KEY"
    )

    if not api_key:
        print(
            "Brave Search API key is not configured."
        )

        return [], False

    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key
    }

    params = {
        "q": claim,
        "count": 20,
        "search_lang": "en"
    }

    try:
        response = requests.get(
            BRAVE_SEARCH_API_URL,
            headers=headers,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return (
            normalize_brave_results(data),
            False
        )

    except requests.RequestException as error:
        print(
            f"Brave Search API error: {error}"
        )

        return [], True

    except ValueError as error:
        print(
            f"Brave Search parsing error: {error}"
        )

        return [], True


def clean_snippet(text):
    """
    Convert HTML-heavy search snippets into readable
    plain text.

    Examples:

    <strong>financial aid</strong>
    becomes:
    financial aid

    &quot;example&quot;
    becomes:
    "example"
    """

    if not text:
        return ""

    # Decode HTML entities:
    # &quot; -> "
    # &#x27; -> '
    # &amp; -> &
    text = unescape(
        str(text)
    )

    # Remove HTML tags:
    # <strong>
    # </strong>
    # <em>
    text = re.sub(
        r"<[^>]+>",
        "",
        text
    )

    # Collapse repeated spaces/newlines.
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def normalize_fact_checks(data):
    """
    Convert Google's Fact Check response into Faict's
    standard evidence structure.
    """

    evidence = []

    claims = data.get(
        "claims",
        []
    )

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
                "title": clean_snippet(title),
                "url": url,
                "snippet": clean_snippet(snippet)
            })

    return evidence


def normalize_brave_results(data):
    """
    Convert Brave Search results into Faict's standard
    evidence structure.

    Only trusted domains are accepted.

    All trusted candidates are retained so relevance
    scoring and topic-aware ranking can be applied later.
    """

    evidence = []

    web_results = (
        data.get("web", {})
        .get("results", [])
    )

    for result in web_results:

        url = result.get(
            "url",
            ""
        )

        if not url:
            continue

        domain = get_domain(
            url
        )

        if not is_trusted_domain(
            domain
        ):
            continue

        title = clean_snippet(
            result.get(
                "title",
                "Web source"
            )
        )

        description = clean_snippet(
            result.get(
                "description",
                "No description available."
            )
        )

        evidence.append({
            "publisher": domain,
            "title": title,
            "url": url,
            "snippet": description
        })

    return evidence


def get_domain(url):
    """
    Extract and clean the domain from a URL.

    Example:

    https://www.nasa.gov/example

    becomes:

    nasa.gov
    """

    try:
        parsed = urlparse(
            url
        )

        domain = (
            parsed.netloc
            .lower()
            .strip()
        )

        if domain.startswith(
            "www."
        ):
            domain = domain[4:]

        return domain

    except ValueError:
        return ""


def is_trusted_domain(domain):
    """
    Determine whether a domain can be used as trusted
    evidence.

    Automatically accepts:

    - U.S. government domains
    - U.S. military domains
    - U.S. education domains

    Also accepts explicitly allowlisted domains.
    """

    if not domain:
        return False

    domain = (
        domain
        .lower()
        .strip()
    )

    if domain.endswith(
        ".gov"
    ):
        return True

    if domain.endswith(
        ".edu"
    ):
        return True

    if domain.endswith(
        ".mil"
    ):
        return True

    for trusted_domain in TRUSTED_DOMAINS:

        if domain == trusted_domain:
            return True

        if domain.endswith(
            "." + trusted_domain
        ):
            return True

    return False


def normalize_topic(category):
    """
    Convert classifier categories into stable internal
    topic names used by evidence ranking.

    Shaavon's classifier may use slightly different
    category wording for similar topics.
    """

    if not isinstance(
        category,
        str
    ):
        return "other"

    value = (
        category
        .lower()
        .strip()
    )

    if (
        "financial aid" in value
        or "student aid" in value
        or value == "education finance"
        or value == "education and finance"
        or value == "college finance"
    ):
        return "financial_aid"

    return value.replace(
        " ",
        "_"
    )


def is_topic_priority_source(
    url,
    topic
):
    """
    Return True when a source belongs to the configured
    primary/trusted source list for a topic.
    """

    domain = get_domain(
        url
    )

    trusted_domains = (
        TOPIC_TRUSTED_DOMAINS
        .get(
            topic,
            set()
        )
    )

    for trusted_domain in trusted_domains:

        if domain == trusted_domain:
            return True

        if domain.endswith(
            "." + trusted_domain
        ):
            return True

    return False


def extract_terms(text):
    """
    Return distinct non-stopword terms from text.
    """

    words = re.findall(
        r"[a-z0-9]+",
        (text or "").lower()
    )

    return {
        word
        for word in words
        if word not in STOPWORDS
    }


def calculate_relevance(
    claim,
    evidence
):
    """
    Calculate evidence relevance from 0.00 to 1.00.

    Relevance is the proportion of distinct non-stopword
    claim terms appearing in the evidence title/snippet.
    """

    claim_terms = extract_terms(
        claim
    )

    if not claim_terms:
        return 0.0

    evidence_text = " ".join([
        evidence.get(
            "title",
            ""
        ),
        evidence.get(
            "snippet",
            ""
        ),
    ])

    evidence_terms = extract_terms(
        evidence_text
    )

    matching_terms = (
        claim_terms
        .intersection(
            evidence_terms
        )
    )

    score = (
        len(matching_terms)
        / len(claim_terms)
    )

    return round(
        score,
        2
    )


def add_relevance_scores(
    claim,
    evidence_items
):
    """
    Add relevance scores and remove evidence below
    the configured minimum threshold.
    """

    scored_items = []

    for evidence in evidence_items:

        item = evidence.copy()

        item["relevance_score"] = (
            calculate_relevance(
                claim,
                item
            )
        )

        if (
            item["relevance_score"]
            >= MIN_RELEVANCE
        ):
            scored_items.append(
                item
            )

    return scored_items


def rank_evidence(
    evidence_items,
    topic
):
    """
    Rank evidence in two stages:

    1. Topic-priority sources first.
    2. Highest relevance first within each group.
    """

    def ranking_key(item):

        is_priority = (
            is_topic_priority_source(
                item.get(
                    "url",
                    ""
                ),
                topic
            )
        )

        relevance = item.get(
            "relevance_score",
            0.0
        )

        return (
            0 if is_priority else 1,
            -relevance
        )

    return sorted(
        evidence_items,
        key=ranking_key
    )


def process_evidence(
    claim,
    category,
    evidence_items
):
    """
    Apply topic normalization, relevance scoring,
    threshold filtering, and topic-aware ranking.

    Returns no more than MAX_EVIDENCE_ITEMS.
    """

    topic = normalize_topic(
        category
    )

    scored_items = (
        add_relevance_scores(
            claim,
            evidence_items
        )
    )

    ranked_items = (
        rank_evidence(
            scored_items,
            topic
        )
    )

    return ranked_items[
        :MAX_EVIDENCE_ITEMS
    ]


def remove_duplicate_evidence(
    evidence
):
    """
    Remove duplicate sources based on URL.
    """

    unique_evidence = []

    seen_urls = set()

    for source in evidence:

        url = (
            source
            .get(
                "url",
                ""
            )
            .strip()
        )

        if not url:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(
            url
        )

        unique_evidence.append(
            source
        )

    return unique_evidence