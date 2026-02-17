# Main client used to pull data from the Domain website
# Handles suburb trends + sold properties on a street

import re
import requests
from bs4 import BeautifulSoup

from domain_client.models import MarketTrend, SoldProperty


class DomainClient:
    BASE_URL = "https://www.domain.com.au"

    def __init__(self, debug: bool = False):
        # Use a session so we don't create a new connection every time
        self.debug = debug
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-AU,en;q=0.9",
        })

    # -----------------------------
    # SUBURB MARKET TRENDS
    # -----------------------------
    def get_market_trends(self, suburb_slug: str):
        # Build suburb profile URL
        url = f"{self.BASE_URL}/suburb-profile/{suburb_slug}"
        response = self.session.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text("\n")

        # Regex to match the rows in the market trends section
        pattern = re.compile(
            r'(\d+)\s+(House|Unit|Apartment|Townhouse)\s+(\$\S+|---)\s+(\d+)?\s*days?\s*(\d+)?%\s*(\d+)',
            re.I
        )

        trends = []

        for match in pattern.findall(text):
            beds = int(match[0])
            prop = match[1].title()
            price = None if match[2] == "---" else match[2]
            days = int(match[3]) if match[3] else None
            clearance = float(match[4]) / 100 if match[4] else None
            sold = int(match[5]) if match[5] else None

            trends.append(
                MarketTrend(
                    bedrooms=beds,
                    property_type=prop,
                    median_price=price,
                    avg_days_on_market=days,
                    clearance_rate=clearance,
                    sold_this_year=sold
                )
            )

        return trends

    # -----------------------------
    # STREET SOLD PROPERTIES
    # -----------------------------
    def get_recent_sold(
        self,
        street_slug: str,
        limit: int = 20,
        page_no: int = 1,
        page_size: int = 10,
        fetch_details: bool = False
    ):
        # This URL filters the street page to only sold properties
        url = (
            f"{self.BASE_URL}/street-profile/{street_slug}"
            f"?filtertype=sold&pagesize={page_size}&pageno={page_no}"
        )

        response = self.session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        results = []

        # Listing links normally end with a long number (property id)
        listing_link_re = re.compile(r"^https?://www\.domain\.com\.au/.+-\d{8,}$", re.I)

        seen_urls = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not listing_link_re.match(href):
                continue
            if href in seen_urls:
                continue
            seen_urls.add(href)

            # Sometimes the visible title is missing the street name
            title = a.get_text(" ", strip=True)
            href_addr = self._address_from_href(href)

            if not title:
                address = href_addr
            else:
                street_tokens = ["esplanade", "street", "st", "road", "rd",
                                 "avenue", "ave", "drive", "dr", "circuit",
                                 "crescent", "lane", "place", "parade",
                                 "terrace", "court"]

                href_has_street = any(tok in href_addr.lower() for tok in street_tokens)
                title_has_street = any(tok in title.lower() for tok in street_tokens)

                # Prefer slug-derived address if title looks incomplete
                address = href_addr if (href_has_street and not title_has_street) else title

            card_text = self._get_card_text(a)

            beds = self._extract_int(card_text, "Bed")
            baths = self._extract_int(card_text, "Bath")
            park = self._extract_int(card_text, "Parking")

            sold_date = self._extract_sold_date(card_text)
            price = self._extract_price(card_text)

            # If needed, try to get missing info from the listing page
            if fetch_details and (sold_date is None or price is None):
                d_date, d_price = self._fetch_listing_sold_details(href)
                sold_date = sold_date or d_date
                price = price or d_price

            if beds is None and baths is None and park is None and sold_date is None and price is None:
                continue

            results.append(
                SoldProperty(
                    address=address,
                    url=href,
                    sold_date=sold_date,
                    beds=beds,
                    baths=baths,
                    parking=park,
                    price=price
                )
            )

            if len(results) >= limit:
                break

        return results

    # Move up the HTML to find the section with beds/baths/price
    def _get_card_text(self, anchor_tag):
        card = anchor_tag
        for _ in range(10):
            if card.parent is None:
                break
            card = card.parent
            txt = card.get_text("\n", strip=True)
            if ("Bed" in txt) or ("Sold" in txt) or ("$" in txt):
                return txt
        return ""

    def _extract_int(self, text: str, label: str):
        match = re.search(rf"(\d+)\s*{label}s?\b", text, re.I)
        return int(match.group(1)) if match else None

    def _extract_price(self, text: str):
        t = " ".join(text.split())
        m = re.search(r"\bSold\b\s*(\$\s?\d[\d,]*(?:\.\d+)?\s*[mk]?)", t, re.I)
        if m:
            return m.group(1).replace(" ", "")
        m = re.search(r"(\$\s?\d[\d,]*(?:\.\d+)?\s*[mk]?)", t, re.I)
        if m:
            return m.group(1).replace(" ", "")
        if "N/A" in t:
            return "N/A"
        return None

    def _extract_sold_date(self, text: str):
        t = " ".join(text.split())
        m = re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\b", t)
        if m:
            return m.group(0)
        m = re.search(r"\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", t)
        if m:
            return m.group(0)
        m = re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b", t)
        if m:
            return m.group(0)
        return None

    # Try pull extra details from the listing page
    def _fetch_listing_sold_details(self, listing_url: str):
        try:
            resp = self.session.get(listing_url, timeout=20)
            if resp.status_code != 200:
                return None, None
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text("\n", strip=True)
        except Exception:
            return None, None

        t = " ".join(text.split())

        price = None
        m = re.search(r"\bSold\b.*?(\$\s?\d[\d,]*(?:\.\d+)?\s*[mk]?)", t, re.I)
        if m:
            price = m.group(1).replace(" ", "")

        sold_date = None
        m = re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\b", t)
        if m:
            sold_date = m.group(0)

        return sold_date, price

    # Build a readable address from the listing URL
    def _address_from_href(self, href: str):
        path = href.rstrip("/").split("/")[-1]
        path = re.sub(r"-\d{8,}$", "", path)
        return path.replace("-", " ").strip()
