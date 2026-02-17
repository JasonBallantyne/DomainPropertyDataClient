# DomainPropertyDataClient

Python client for retrieving suburb market trends and recently sold property data from Domain suburb and street profile pages.

---

## Overview

This project implements a Python-based client for extracting property market data from the Domain website.

The client provides a structured interface for retrieving:

- Suburb-level market trend data
- Recently sold property data for specific streets

The extracted data can be used for downstream analytics, modelling, or property investment decision-making.

---

## Data Sources

This client extracts publicly available data from the following Domain pages:

Suburb Profile Page  
Example:  
https://www.domain.com.au/suburb-profile/mooloolaba-qld-4557

Street Profile Page  
Example:  
https://www.domain.com.au/street-profile/mooloolaba-esplanade-mooloolaba-qld-4557

---

## Features

- Retrieve suburb-level market trends
- Retrieve recently sold properties for a street
- Structured JSON-style output
- Basic handling of missing or malformed data
- Reusable client-style interface

---

## Project Structure

    .
    ├── main.py
    ├── domain_client.py
    ├── requirements.txt
    └── README.md

---

## Setup

Create virtual environment:

    python -m venv venv

Activate environment (Windows):

    venv\Scripts\activate

Install dependencies:

    pip install -r requirements.txt

---

## Usage

Run the client:

    python main.py

---

## Example Output

Market Trends:

    {
      "bedrooms": 3,
      "property_type": "House",
      "median_price": "$1.15m",
      "avg_days_on_market": 37,
      "clearance_rate": 0.64
    }

Recently Sold Property:

    {
      "address": "12 Example Street",
      "sale_price": "$1,200,000",
      "bedrooms": 4,
      "bathrooms": 2,
      "car_spaces": 2,
      "sale_date": "2025-11-14"
    }

---

## Notes

- Data is sourced via HTML parsing of Domain suburb and street profile pages
- Erroneous or incomplete records may be dropped where necessary
- Intended for analytical and modelling use cases
