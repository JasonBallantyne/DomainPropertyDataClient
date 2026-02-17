# Simple data models used to store the results we scrape from Domain

from dataclasses import dataclass
from typing import Optional


# This represents one row from the suburb Market Trends table
@dataclass
class MarketTrend:
    bedrooms: Optional[int]
    property_type: str
    median_price: Optional[str]
    avg_days_on_market: Optional[int]
    clearance_rate: Optional[float]
    sold_this_year: Optional[int]


# This represents a recently sold property from a street page
@dataclass
class SoldProperty:
    address: str
    url: str
    sold_date: Optional[str]
    beds: Optional[int]
    baths: Optional[int]
    parking: Optional[int]
    price: Optional[str]
