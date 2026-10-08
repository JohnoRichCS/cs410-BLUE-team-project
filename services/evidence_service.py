import os
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

# This list is used only for Brave Search fallback results.

# Google Fact Check results are already coming from Google's indexed fact checking ecosystem and are handled separately.

# Rejects random blogs, forums, social media posts, and other low quality sources.


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

    # SCIENCE JOURNALS / SCIENCE PUBLICATIONS

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

    # INTERNATIONAL GOVERNMENT / MULTINATIONAL ORGANIZATIONS

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

    "federalreserve.gov",
    "fred.stlouisfed.org",
    "stlouisfed.org",

    "bls.gov",
    "bea.gov",
    "census.gov",

    "worldbank.org",
    "imf.org",
    "oecd.org",

    # LAW / LEGAL INFORMATION

    "law.cornell.edu",
    "supremecourt.gov",
    "uscourts.gov",
    "justice.gov",
    "congress.gov",

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
    "cisa.gov",

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


def find_evidence(claim):
    """
    Retrieve evidence for a submitted claim.

    Search order:

    1. Google Fact Check Tools API
    2. Brave Search API fallback

    Google Fact Check is preferred because its results contain
    published fact-check reviews.

    Brave Search is used when no Google fact-check evidence is found.

    Returns:
        list[dict]

        Example:

        [
            {
                "publisher": "nasa.gov",
                "title": "Example article",
                "url": "https://...",
                "snippet": "Relevant evidence..."
            }
        ]
    """

    if not claim or not claim.strip():
        return []

    claim = claim.strip()

    # First choice: Google Fact Check

    fact_check_results = find_fact_check_evidence(claim)

    if fact_check_results:
        return remove_duplicate_evidence(
            fact_check_results
        )

    # Fallback: Brave Search

    web_results = find_web_evidence(claim)

    return remove_duplicate_evidence(
        web_results
    )


def find_fact_check_evidence(claim):
    """
    Search Google's Fact Check Tools API.

    Returns normalized evidence that can be passed directly
    into analyze_claim().
    """

    api_key = os.getenv(
        "GOOGLE_FACT_CHECK_API_KEY"
    )

    if not api_key:
        print(
            "Google Fact Check API key is not configured."
        )
        return []

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

        return normalize_fact_checks(
            data
        )

    except requests.RequestException as error:
        print(
            f"Google Fact Check API error: {error}"
        )

        return []

    except ValueError as error:
        print(
            f"Google Fact Check parsing error: {error}"
        )

        return []


def find_web_evidence(claim):
    """
    Search Brave Search when Google Fact Check does not
    return evidence.

    Only results from trusted sources are returned.
    """

    api_key = os.getenv(
        "BRAVE_SEARCH_API_KEY"
    )

    if not api_key:
        print(
            "Brave Search API key is not configured."
        )

        return []

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

        return normalize_brave_results(
            data
        )

    except requests.RequestException as error:
        print(
            f"Brave Search API error: {error}"
        )

        return []

    except ValueError as error:
        print(
            f"Brave Search parsing error: {error}"
        )

        return []


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
                "title": title,
                "url": url,
                "snippet": snippet
            })

    return evidence


def normalize_brave_results(data):
    """
    Convert Brave Search results into Faict's standard
    evidence structure.

    Only trusted domains are accepted.
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

        title = result.get(
            "title",
            "Web source"
        )

        description = result.get(
            "description",
            "No description available."
        )

        evidence.append({
            "publisher": domain,
            "title": title,
            "url": url,
            "snippet": description
        })

        # Keeps API usage and AI prompt size low
        if len(evidence) >= 5:
            break

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
    - accredited U.S. education domains

    Also accepts domains explicitly listed in
    TRUSTED_DOMAINS.
    """

    if not domain:
        return False

    domain = (
        domain
        .lower()
        .strip()
    )

    # Government

    if domain.endswith(
        ".gov"
    ):
        return True

    # Education

    if domain.endswith(
        ".edu"
    ):
        return True

    # Military

    if domain.endswith(
        ".mil"
    ):
        return True

    # Explicit allowlist

    for trusted_domain in TRUSTED_DOMAINS:

        if domain == trusted_domain:
            return True

        # Allows legitimate subdomains:
        #
        # climate.nasa.gov
        # health.harvard.edu
        # fred.stlouisfed.org
        #
        if domain.endswith(
            "." + trusted_domain
        ):
            return True

    return False


def remove_duplicate_evidence(evidence):
    """
    Remove duplicate sources based on their URL.

    Search APIs may occasionally return the same article
    more than once.
    """

    unique_evidence = []

    seen_urls = set()

    for source in evidence:

        url = (
            source
            .get("url", "")
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