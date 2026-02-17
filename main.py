# Simple example of using the client to pull suburb + street data

import json
from dataclasses import asdict
from domain_client.client import DomainClient

client = DomainClient(debug=False)

trends = client.get_market_trends("mooloolaba-qld-4557")
sold = client.get_recent_sold(
    "mooloolaba-esplanade-mooloolaba-qld-4557",
    limit=10,
    fetch_details=False
)

print(json.dumps(
    {
        "market_trends": [asdict(t) for t in trends],
        "sold_properties": [asdict(s) for s in sold],
    },
    indent=2
))
