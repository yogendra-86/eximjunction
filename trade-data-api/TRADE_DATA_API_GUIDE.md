# Trade Data API — Complete User Guide & FAQ

**Version:** 0.3.0  
**Last Updated:** May 2026  
**Support:** [Yet to decide]
**API Base URL:** `[Yet to decide]` *(or `http://localhost:8000` for local dev)*

---

## Table of Contents

1. [What is Trade Data API?](#1-what-is-trade-data-api)
2. [Getting Started](#2-getting-started)
3. [Authentication & API Keys](#3-authentication--api-keys)
4. [Querying Trade Data](#4-querying-trade-data)
5. [Subscription & Billing](#5-subscription--billing)
6. [Rate Limits & Usage](#6-rate-limits--usage)
7. [Understanding the Data](#7-understanding-the-data)
8. [FAQ — Technical](#8-faq--technical)
9. [FAQ — Billing & Plans](#9-faq--billing--plans)
10. [FAQ — Data & Coverage](#10-faq--data--coverage)
11. [FAQ — For Businesses](#11-faq--for-businesses)
12. [Troubleshooting](#12-troubleshooting)
13. [Glossary](#13-glossary)

---

## 1. What is Trade Data API?

Trade Data API is a service that gives you **programmatic access to international import-export trade data**. Instead of manually searching through government databases or buying expensive reports, you can query exactly what you need — by product, country, year — and get clean structured data back in milliseconds.

### What kind of data can I get?

| Data Type | Example Query | Example Answer |
|---|---|---|
| **Product search** | "Find the HS code for mobile phones" | HS 851712 — Telephones for cellular networks |
| **Trade partners** | "Who does India export rice to?" | Saudi Arabia, UAE, US, UK, Bangladesh (ranked by value) |
| **Trade trends** | "How has India's pharma exports to US changed 2019–2024?" | Year-by-year values + CAGR % |
| **Tariff rates** | "What duty does the US charge on cotton T-shirts?" | 16.5% MFN, 0% under USMCA for Mexico |
| **Compliance docs** | "What certificates does India need to export food to Germany?" | Phytosanitary cert, FSSAI cert, REACH declaration, etc. |

### Who is this for?

- **Import/Export businesses** — verify trade routes, discover new markets, understand competitor volumes
- **Freight forwarders & logistics companies** — look up HS codes, compliance requirements, tariff costs
- **Trade consultants** — back up recommendations with data, build reports for clients
- **Customs agents** — quick lookup of tariff classifications and duty rates
- **Market researchers** — analyse trade flow trends across countries and product categories
- **Developers** — build trade-related applications on top of structured API data

---

## 2. Getting Started

### Step 1 — Open the API Documentation

The interactive API explorer lives at:

```
http://localhost:8000/docs
```

This is a Swagger UI — every endpoint is listed, you can click **Try it out** and test queries directly in the browser without writing any code.

### Step 2 — Create your free account

Go to `POST /api/v1/auth/signup` in the docs, click **Try it out**, and fill in:

```json
{
  "email": "you@yourcompany.com",
  "password": "YourStrongPassword123",
  "full_name": "Your Name",
  "company_name": "Your Company Pvt Ltd",
  "phone": "+91-9876543210"
}
```

Click **Execute**. You'll get back a `access_token` — this is your login token, valid for 8 hours.

What happens automatically when you sign up:
- Your account is created
- You are subscribed to the **Free plan** (50 API calls/day)
- Your first API key is created for you

### Step 3 — Get your API key

Go to `GET /api/v1/auth/keys`. You'll need to authorize first:

1. Click the **Authorize** button (top right of the Swagger page)
2. In the field that says **HTTPBearer**, paste your `access_token`
3. Click **Authorize** and **Close**

Now call `GET /api/v1/auth/keys`. You'll see your default key listed with its `key_prefix`. To get the full usable key, create a named one via `POST /api/v1/auth/keys`:

```json
{
  "name": "My production key"
}
```

The response includes `plaintext_key` — a long string starting with `tdk_`. **Copy and save this immediately.** It is shown only once and cannot be retrieved again.

### Step 4 — Make your first query

Use your API key in the `X-API-Key` header:

```bash
curl "http://localhost:8000/api/v1/products/search?q=rice" \
  -H "X-API-Key: tdk_YourKeyHere"
```

Or in Swagger, click **Authorize** again and fill in the `X-API-Key` field with your full key.

Then go to `GET /api/v1/products/search`, enter `q=rice`, and hit **Execute**. You'll see a list of rice-related HS codes.

---

## 3. Authentication & API Keys

The API has two types of credentials:

| Type | What it's for | How long it lasts |
|---|---|---|
| **JWT Token** | Managing your account (signup, billing, key management) | 8 hours |
| **API Key** | Calling trade data endpoints | Until revoked |

### Getting a JWT Token (login)

```
POST /api/v1/auth/login
Body: { "email": "you@company.com", "password": "YourPassword" }
Response: { "access_token": "eyJ...", "token_type": "bearer" }
```

Use the token in the `Authorization` header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Creating an API Key

Once logged in:

```
POST /api/v1/auth/keys
Header: Authorization: Bearer <your-jwt-token>
Body: { "name": "Label for this key" }
Response: { "plaintext_key": "tdk_...", "tier": "free", ... }
```

### Using your API Key

Pass it in the `X-API-Key` header on every data request:

```bash
curl "http://localhost:8000/api/v1/countries" \
  -H "X-API-Key: tdk_AbCdEfGhXyZ..."
```

Or as a query parameter (for browser testing):

```
http://localhost:8000/api/v1/countries?api_key=tdk_AbCdEfGhXyZ...
```

### Managing your API Keys

| Action | Endpoint | Auth needed |
|---|---|---|
| Create a key | `POST /api/v1/auth/keys` | JWT |
| List your keys | `GET /api/v1/auth/keys` | JWT |
| View usage for a key | `GET /api/v1/auth/keys/{id}/usage` | JWT |
| Revoke a key | `DELETE /api/v1/auth/keys/{id}` | JWT |

> **Security tip:** If you think your API key has been exposed or leaked, revoke it immediately via `DELETE /api/v1/auth/keys/{id}` and create a new one.

---

## 4. Querying Trade Data

All data endpoints require a valid `X-API-Key` header.

### 4.1 Search for HS Codes

HS (Harmonized System) codes are the international standard for classifying traded goods. They're 6 digits and organized hierarchically:

- **2 digits** = Chapter (e.g., `09` = Coffee, tea, spices)
- **4 digits** = Heading (e.g., `0901` = Coffee)
- **6 digits** = Subheading (e.g., `090111` = Coffee, not roasted, not decaffeinated)

**Search by keyword:**

```
GET /api/v1/products/search?q=coffee
GET /api/v1/products/search?q=mobile phone
GET /api/v1/products/search?q=crude oil
GET /api/v1/products/search?q=rice
```

**Search by partial code:**

```
GET /api/v1/products/search?q=0901
GET /api/v1/products/search?q=85
```

**Filter by level (chapter/heading/subheading):**

```
GET /api/v1/products/search?q=tea&level=6   (only 6-digit codes)
GET /api/v1/products/search?q=8&level=2     (only chapters starting with 8)
```

**Sample response:**

```json
[
  {
    "code": "090111",
    "level": 6,
    "parent_code": "0901",
    "description": "Coffee, not roasted, not decaffeinated",
    "short_name": "Coffee, not roasted, not decaf"
  }
]
```

---

### 4.2 Get HS Code Details with Hierarchy

```
GET /api/v1/products/{hs_code}
```

**Example:** `GET /api/v1/products/090111`

```json
{
  "code": "090111",
  "level": 6,
  "description": "Coffee, not roasted, not decaffeinated",
  "ancestors": [
    {"code": "09", "description": "Coffee, tea, mate and spices"},
    {"code": "0901", "description": "Coffee, whether or not roasted or decaffeinated"}
  ],
  "children": []
}
```

**Example:** `GET /api/v1/products/09` (chapter level — shows children)

```json
{
  "code": "09",
  "level": 2,
  "description": "Coffee, tea, mate and spices",
  "ancestors": [],
  "children": [
    {"code": "0901", "description": "Coffee, whether or not roasted..."},
    {"code": "0902", "description": "Tea, whether or not flavoured"},
    {"code": "0904", "description": "Pepper of the genus Piper..."}
  ]
}
```

---

### 4.3 Top Trading Partners

Find out who trades the most for a given product.

```
GET /api/v1/products/{hs_code}/top-partners
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `flow` | string | `export` | `export` or `import` |
| `year` | integer | `2024` | Year of data (1990–2030) |
| `reporter` | string | *(none)* | ISO alpha-2 country code. If given, shows partners of that country. If omitted, shows global rankings. |
| `limit` | integer | `10` | How many results (max 100) |

**Example 1:** Who does India export coffee to?

```
GET /api/v1/products/090111/top-partners?reporter=IN&flow=export&year=2024&limit=5
```

```json
{
  "hs_code": "090111",
  "flow_type": "export",
  "year": 2024,
  "reporter": {"iso_alpha2": "IN", "name": "India"},
  "partners": [
    {"rank": 1, "country": {"iso_alpha2": "US", "name": "United States"}, "value_usd": 1180000000},
    {"rank": 2, "country": {"iso_alpha2": "DE", "name": "Germany"}, "value_usd": 985000000},
    {"rank": 3, "country": {"iso_alpha2": "IT", "name": "Italy"}, "value_usd": 865000000},
    {"rank": 4, "country": {"iso_alpha2": "BE", "name": "Belgium"}, "value_usd": 633000000},
    {"rank": 5, "country": {"iso_alpha2": "RU", "name": "Russia"}, "value_usd": 519000000}
  ]
}
```

**Example 2:** Who are the world's top crude oil exporters? (no reporter)

```
GET /api/v1/products/270900/top-partners?flow=export&year=2024&limit=5
```

**Example 3:** Who imports the most mobile phones?

```
GET /api/v1/products/851712/top-partners?flow=import&year=2024
```

---

### 4.4 Trade Flow Trends

Get year-by-year trade data between two specific countries for a product.

```
GET /api/v1/trade-flows
```

**Parameters:**

| Parameter | Required | Description |
|---|---|---|
| `reporter` | ✅ | ISO alpha-2 of the reporting country |
| `partner` | ✅ | ISO alpha-2 of the partner country |
| `hs_code` | ✅ | HS code to query |
| `flow` | ❌ | `export` (default) or `import` |
| `year_from` | ❌ | Start year (default 2019) |
| `year_to` | ❌ | End year (default 2024) |

**Example:** India's pharma exports to the US, 2019–2024

```
GET /api/v1/trade-flows?reporter=IN&partner=US&hs_code=300490&flow=export&year_from=2019&year_to=2024
```

```json
{
  "reporter": {"iso_alpha2": "IN", "name": "India"},
  "partner": {"iso_alpha2": "US", "name": "United States"},
  "hs_code": "300490",
  "hs_description": "Medicaments, retail",
  "flow_type": "export",
  "points": [
    {"year": 2019, "value_usd": 14960000000},
    {"year": 2020, "value_usd": 12700000000},
    {"year": 2021, "value_usd": 16740000000},
    {"year": 2022, "value_usd": 19360000000},
    {"year": 2023, "value_usd": 18480000000},
    {"year": 2024, "value_usd": 17640000000}
  ],
  "total_value_usd": 99880000000,
  "growth_rate_pct": 3.3
}
```

`growth_rate_pct` is the **CAGR** (Compound Annual Growth Rate) over the queried period.

---

### 4.5 Tariff Rates

Find out what duty a country charges on imports of a specific product.

```
GET /api/v1/tariffs
```

**Parameters:**

| Parameter | Required | Description |
|---|---|---|
| `reporter` | ✅ | Country applying the tariff (importer), ISO alpha-2 |
| `hs_code` | ✅ | HS code of the product |
| `partner` | ❌ | Exporting country. If given, returns both MFN and any preferential rate for that partner |
| `year` | ❌ | Year (default 2024) |

**Example 1:** US tariff on cotton T-shirts (MFN — applies to all countries)

```
GET /api/v1/tariffs?reporter=US&hs_code=610910&year=2024
```

```json
[
  {
    "rate_type": "MFN",
    "ad_valorem_rate": 16.5,
    "notes": "Cotton T-shirts"
  }
]
```

**Example 2:** What does the US charge Mexico for cars? (includes USMCA preference)

```
GET /api/v1/tariffs?reporter=US&partner=MX&hs_code=870323&year=2024
```

```json
[
  {
    "rate_type": "preferential",
    "ad_valorem_rate": 0.0,
    "agreement": "USMCA",
    "notes": "Duty-free if regional value content rules met"
  },
  {
    "rate_type": "MFN",
    "ad_valorem_rate": 2.5
  }
]
```

Results are sorted lowest-rate first (most beneficial to the importer).

---

### 4.6 Compliance Documents

Find out what certificates and documents are required to ship a product between two countries.

```
GET /api/v1/compliance
```

**Parameters:**

| Parameter | Required | Description |
|---|---|---|
| `reporter` | ✅ | Exporting country, ISO alpha-2 |
| `partner` | ✅ | Importing country, ISO alpha-2 |
| `hs_code` | ❌ | If provided, includes product-specific requirements |

**Example 1:** General documents for any India → US export

```
GET /api/v1/compliance?reporter=IN&partner=US
```

Returns: Commercial Invoice, Packing List, Bill of Lading, IEC (India Exporter Code), Shipping Bill, Importer Security Filing (10+2)

**Example 2:** India → US pharmaceuticals

```
GET /api/v1/compliance?reporter=IN&partner=US&hs_code=300490
```

Returns everything above PLUS: Drug Manufacturing Licence (GMP), FDA Prior Notice & Drug Establishment Registration

**Example 3:** India → Belgium diamonds

```
GET /api/v1/compliance?reporter=IN&partner=BE&hs_code=710231
```

Returns general docs PLUS: Kimberley Process Certificate (mandatory for rough diamonds)

---

### 4.7 Countries Reference

```
GET /api/v1/countries            — list all 32+ supported countries
GET /api/v1/countries/IN         — lookup by ISO alpha-2
GET /api/v1/countries/IND        — lookup by ISO alpha-3
```

**Country codes quick reference:**

| Country | Alpha-2 | Country | Alpha-2 |
|---|---|---|---|
| India | `IN` | United States | `US` |
| China | `CN` | Germany | `DE` |
| United Kingdom | `GB` | Japan | `JP` |
| United Arab Emirates | `AE` | Saudi Arabia | `SA` |
| Bangladesh | `BD` | Vietnam | `VN` |
| Singapore | `SG` | South Korea | `KR` |

---

## 5. Subscription & Billing

### Plans

| Plan | Price | Daily Calls | Best For |
|---|---|---|---|
| **Free** | ₹0/month | 50 calls/day | Trial & evaluation |
| **Paid** | ₹1,999/month | 10,000 calls/day | Business use |
| **Paid Annual** | ₹19,990/year | 10,000 calls/day | Save 2 months |

View current plans programmatically (no login needed):

```
GET /api/v1/billing/plans
```

### Upgrading your plan

**Step 1:** Make sure you're logged in (have a valid JWT token)

**Step 2:** Start checkout

```
POST /api/v1/billing/checkout
Body: { "plan_code": "paid" }
```

Response includes a Razorpay order ID and amount.

**Step 3:** Complete payment via Razorpay checkout (UPI, Net Banking, Credit/Debit Card)

**Step 4:** Your subscription activates immediately. All your existing API keys are automatically upgraded to the new tier.

### Check your current subscription

```
GET /api/v1/billing/subscription
Header: Authorization: Bearer <your-jwt-token>
```

### Payment history

```
GET /api/v1/billing/payments
Header: Authorization: Bearer <your-jwt-token>
```

---

## 6. Rate Limits & Usage

### Daily limits

| Plan | Limit | Resets |
|---|---|---|
| Free | 50 requests/day | 00:00 UTC (5:30 AM IST) |
| Paid | 10,000 requests/day | 00:00 UTC (5:30 AM IST) |

Limits are per API key, per calendar day (UTC).

### What happens when you hit the limit?

You'll get an HTTP `429 Too Many Requests` response:

```json
{
  "detail": "Daily rate limit of 50 requests exceeded for tier 'free'. Resets at 00:00 UTC. Upgrade your plan at /pricing."
}
```

The `Retry-After: 3600` header tells you to wait (in seconds) before trying again.

### Check your usage

```
GET /api/v1/auth/keys/{key_id}/usage
Header: Authorization: Bearer <your-jwt-token>
```

Returns a 30-day breakdown of daily request counts.

### Tips to stay within limits

- On the free tier, **cache responses on your side** — trade data changes infrequently
- Batch your lookups — search for a chapter code (`09`) to get all subheadings in one call
- Use `limit` parameters to avoid pulling more data than you need

---

## 7. Understanding the Data

### What is an HS code?

The **Harmonized System** (HS) is an international standard developed by the World Customs Organization (WCO) to classify traded goods. 200+ countries use it for customs. Every product has a 6-digit HS code:

```
09           = Chapter: Coffee, tea, mate and spices
  0901       = Heading: Coffee (roasted/unroasted/decaf)
    090111   = Subheading: Coffee, not roasted, not decaffeinated
```

When you import or export, your shipment is classified under a specific HS code. This determines the duty rate, required documents, and how the trade is recorded in statistics.

### What does "value_usd" mean?

All trade values are in **USD** regardless of the currencies the countries actually traded in. This is how UN Comtrade standardizes data across countries. For an Indian company trading in INR, the conversion is based on average exchange rates for that year.

### What does "flow_type" mean?

- **`export`**: data reported by the exporting country (what they sent out)
- **`import`**: data reported by the importing country (what they received)

Both should theoretically be the same for a given trade pair, but due to reporting differences, CIF vs FOB valuation, and timing, the numbers often differ. Imports are typically higher because they include cost, insurance, and freight (CIF).

### What is CAGR?

**Compound Annual Growth Rate** — the steady growth rate that would take you from the starting value to the ending value over the number of years. It accounts for compounding, unlike a simple average.

For example: if India's exports to the US grew from ₹100Cr to ₹134Cr over 5 years, the CAGR is 6% per year.

### What is MFN rate?

**Most Favoured Nation** rate — the standard tariff a WTO member applies to all other WTO members unless a preferential agreement applies. If a country has an FTA (Free Trade Agreement) with another country, the preferential rate is usually lower than MFN.

### Why do some tariff results show "specific rate"?

Some products (especially agricultural commodities like rice in Japan) are taxed by weight or volume rather than a percentage of value. For example, Japan charges JPY 341 per kg on milled rice imports rather than a percentage.

---

## 8. FAQ — Technical

**Q: I get a 401 error saying "API key required." What am I doing wrong?**

You're missing the API key in your request. Make sure you're passing it in the `X-API-Key` header:

```bash
curl "http://localhost:8000/api/v1/products/search?q=rice" \
  -H "X-API-Key: tdk_YourFullKeyHere"
```

The key must be the full `plaintext_key` you received when you created it — the `key_prefix` shown in the listing (e.g., `tdk_AbCdEfGh`) is only a display label, not the full key.

---

**Q: I lost my API key. Can I recover it?**

No. For security reasons, the full key is shown only once at creation and stored as a hash in our database — not as the original key. If you've lost it, revoke the old key and create a new one:

```
DELETE /api/v1/auth/keys/{id}      — revoke old key
POST   /api/v1/auth/keys           — create new key
```

---

**Q: My JWT token expired. What do I do?**

Tokens expire after 8 hours. Simply log in again:

```
POST /api/v1/auth/login
Body: { "email": "you@company.com", "password": "YourPassword" }
```

---

**Q: Can I have multiple API keys?**

Yes. You can create as many keys as you want. This is useful if you're running multiple applications or want to track usage separately per project. Each key counts toward the same daily limit (limits are account-level, not key-level).

---

**Q: What programming languages can I use?**

Any language that can make HTTP requests. Here are quick examples:

**Python:**
```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/products/search",
    params={"q": "coffee"},
    headers={"X-API-Key": "tdk_YourKeyHere"}
)
data = response.json()
```

**JavaScript (Node.js):**
```javascript
const response = await fetch(
  "http://localhost:8000/api/v1/products/search?q=coffee",
  { headers: { "X-API-Key": "tdk_YourKeyHere" } }
);
const data = await response.json();
```

**PHP:**
```php
$ch = curl_init("http://localhost:8000/api/v1/products/search?q=coffee");
curl_setopt($ch, CURLOPT_HTTPHEADER, ["X-API-Key: tdk_YourKeyHere"]);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$data = json_decode(curl_exec($ch));
```

**Excel (Power Query):**
Go to **Data → Get Data → From Web**, enter the URL with `?api_key=tdk_YourKeyHere` appended. Power Query will parse the JSON automatically.

---

**Q: I get a 422 Unprocessable Entity error. What does that mean?**

A required parameter is missing or in the wrong format. Read the error response body — it tells you exactly which field failed:

```json
{
  "detail": [
    {
      "loc": ["query", "reporter"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

In this case, you forgot to include `reporter` in the query string.

---

**Q: How do I use the API in Postman?**

1. Create a new request
2. Set method to `GET`, URL to `http://localhost:8000/api/v1/products/search`
3. Under **Params**, add key `q` with value `coffee`
4. Under **Headers**, add key `X-API-Key` with value `tdk_YourKey`
5. Click **Send**

To avoid adding the header to every request, create a **Postman Collection** and set the header at the collection level.

---

**Q: Is there an SDK or client library?**

Not yet. The API follows standard REST conventions and returns JSON, so it works out of the box with any HTTP client library. An official Python SDK is planned for Phase 4.

---

**Q: Can I filter trade flow data by month instead of year?**

Currently only annual data is available. Monthly data support is on the roadmap.

---

**Q: Does the API support CORS (for calling from a browser)?**

Yes. CORS is enabled for all origins by default in development mode. For production, configure `CORS_ORIGINS` in `.env` to your specific frontend domain.

---

## 9. FAQ — Billing & Plans

**Q: Is the Free plan really free forever?**

Yes, completely free with no credit card required. You get 50 API calls per day, every day, as long as your account is active.

---

**Q: What counts as an "API call"?**

Each HTTP request to a data endpoint counts as one call. Requests to auth or billing endpoints (`/auth/*`, `/billing/*`) do not count toward your limit.

These count:
- `GET /api/v1/products/search?q=coffee`
- `GET /api/v1/trade-flows?reporter=IN&...`
- `GET /api/v1/tariffs?reporter=US&...`

These do NOT count:
- `GET /api/v1/billing/plans`
- `POST /api/v1/auth/login`
- `GET /api/v1/health`

---

**Q: When does the daily call limit reset?**

At **00:00 UTC every day**, which is **5:30 AM IST**. So if you exhaust your 50 free calls at 11 PM IST, they reset 6.5 hours later.

---

**Q: Can I upgrade mid-month? Will I be charged for the full month?**

Yes, you can upgrade at any time. You pay for the current month from the upgrade date and are billed monthly from that date onwards. No prorating — you pay ₹1,999 and get access for a full 30 days from the moment of payment.

---

**Q: What payment methods do you accept?**

All major Indian payment methods via Razorpay:
- UPI (Google Pay, PhonePe, Paytm, BHIM)
- Net Banking (all major Indian banks)
- Credit Cards (Visa, Mastercard, Amex, RuPay)
- Debit Cards
- EMI (on eligible cards)

---

**Q: Do you issue GST invoices?**

Yes. GST invoices are automatically generated for every payment. You can download them from your billing dashboard. Our GSTIN is provided on every invoice.

---

**Q: What happens to my API keys if I don't renew my subscription?**

If your paid subscription expires and you don't renew, your account automatically reverts to the Free tier (50 calls/day). Your API keys stay active but at the free tier limit. No data is deleted.

---

**Q: Can I cancel my subscription anytime?**

Yes, cancel anytime. You retain paid access until the end of your current billing period. No penalties, no questions asked.

---

**Q: I paid but my account still shows Free plan. What do I do?**

Wait 2–3 minutes — there's sometimes a small delay between payment capture and subscription activation. If it still shows Free after 5 minutes, contact us at support@tradedataapi.in with your payment receipt and we'll fix it manually within 2 hours.

---

**Q: Is there a team or multi-user plan?**

Not yet. Currently each account is single-user. A Team plan (shared key pool, central billing) is planned. If you need this urgently, email us and we'll work something out.

---

**Q: Do you offer discounts for startups or researchers?**

Yes. Email us at support@tradedataapi.in with a brief description of your project. We offer:
- 50% discount for registered Indian startups (DPIIT recognition required)
- 3-month free Paid plan for academic research institutions
- Custom pricing for NGOs

---

## 10. FAQ — Data & Coverage

**Q: Where does your data come from?**

Our data is sourced from:
- **UN Comtrade** — official global trade statistics, reported by governments
- **WITS (World Bank)** — tariff schedules
- **DGFT / ICEGATE** — India-specific export-import compliance rules
- **WTO Tariff Download Facility** — MFN and bound tariff rates

All sources are official government or intergovernmental datasets.

---

**Q: How current is the data?**

Trade statistics have an inherent lag due to how customs data is collected and reported:

| Data type | Typical lag |
|---|---|
| Annual trade flows | 12–18 months behind |
| Monthly trade flows | 2–3 months behind |
| Tariff rates | Updated annually (or when changed) |
| Compliance docs | Updated when regulations change |

This is the same lag that exists in ALL trade data services — Tradeline, ImportGenius, Zauba — because the underlying government data is not real-time. If you see "2024 data," it means data that governments reported for the year 2024, published in 2025.

---

**Q: How often is your database updated?**

Currently monthly. We pull the latest available data from Comtrade and update our database on the 1st of each month.

---

**Q: Does the API cover all countries in the world?**

Currently 32+ major trading nations are in the dataset, covering approximately 90% of global trade volume. We're expanding to full 200+ country coverage in the next update.

---

**Q: Does the API have shipment-level data (like Zauba)?**

No. We provide aggregated trade statistics (country-to-country flows), not individual shipment records. Shipment-level data (importer name, exporter name, quantity per shipment, port of entry) is a different product requiring different data sources and significantly higher licensing costs.

Shipment-level data for India (from bill-of-entry filings) is on the roadmap as a premium add-on.

---

**Q: Can I get data for a specific Indian port (e.g., JNPT, Mundra)?**

Not yet. Port-level breakdowns require ICEGATE data integration which is in development. Currently data is at the country level.

---

**Q: Is your data the same as what you'd find on the Comtrade website?**

The underlying numbers come from the same source, but we've cleaned, normalised, and structured it to be easier to query programmatically. The Comtrade website is designed for one-off human lookups; our API is designed for integration into applications and automated workflows.

---

**Q: Do you support HS 2022 codes?**

Yes. The database stores HS codes at the 2017 revision level (HS 2017), which is the most widely reported by countries. HS 2022 crosswalk mapping is on the roadmap.

---

**Q: Can I get tariff data for India's FTAs? (ASEAN-India, India-Japan CEPA, etc.)**

Yes, for the corridors and HS codes currently in the dataset. For example:
- India-Japan CEPA tariff rates are included for automotive products
- ASEAN-India FTA rates for mobile phones
- EU GSP rates for Bangladesh garments

Coverage of FTA preferential rates is expanding with each monthly update.

---

## 11. FAQ — For Businesses

**Q: We are a freight forwarding company. How does this help us?**

Several ways:

1. **HS code lookup** — when a client brings you a shipment, look up the right 6-digit HS code by product description. Correct classification avoids customs delays and penalties.

2. **Tariff pre-calculation** — before quoting a client, check the duty rate the destination country will apply. Give your clients accurate landed cost estimates.

3. **Compliance checklist** — for any India-to-X corridor, pull the list of required certificates so your clients don't get shipments held at customs for missing documents.

4. **Integrate into your TMS** — call our API from your Transport Management System to auto-populate HS code and tariff fields.

---

**Q: We are an export consultant. Can we use this for client reports?**

Yes. You can query trade data via our API and incorporate it into client reports, presentations, and market analysis documents. Attribution to the data source (UN Comtrade via Trade Data API) is appreciated but not required.

The Paid plan at ₹1,999/month gives you 10,000 calls/day — more than enough to build comprehensive reports for multiple clients.

---

**Q: We are a manufacturer looking for new export markets. How do I use this?**

1. Find your product's HS code using `GET /products/search?q=your-product`
2. See which countries import the most of that product: `GET /products/{hs_code}/top-partners?flow=import`
3. Check what tariff those countries charge on imports: `GET /tariffs?reporter=target_country&hs_code=...`
4. See if India has an FTA with that country (lower tariff = competitive advantage): include your `partner=IN` for preferential rates
5. Check compliance requirements: `GET /compliance?reporter=IN&partner=target_country&hs_code=...`

---

**Q: We want to integrate this into our ERP / accounting software. Is that possible?**

Yes. The API is a standard REST API that returns JSON — the same format that systems like SAP, Tally Prime, Zoho Books, and most ERPs can consume via their integration frameworks or custom connectors.

Contact us at support@tradedataapi.in and we can help with integration specifics for your system.

---

**Q: Can I use this data commercially — i.e., build a product on top of it?**

Yes, on the Paid plan. The underlying data from UN Comtrade is publicly available under a Creative Commons licence. Our API service, data cleaning, structuring, and hosting are what you're paying for.

If you're planning to build a product that resells or repackages our data as a core feature, contact us for a custom licensing arrangement.

---

**Q: Is the API stable enough for production use?**

The API is currently in **public beta**. The endpoints and response formats are stable (we follow semantic versioning and will not break the API without a migration period). We provide:

- 99% uptime target for the Paid plan
- Email notifications for planned maintenance
- API version in the URL (`/api/v1/`) so future versions don't break existing integrations

---

**Q: What is your data privacy policy? Do you store our queries?**

We log API key usage (request count per day, last used timestamp) for rate limiting and billing purposes. We do NOT log the specific parameters of your queries or the data you access. Your business intelligence (which markets you're researching, which products you're analysing) is private.

Full privacy policy: [tradedataapi.in/privacy](https://tradedataapi.in/privacy) *(link active after launch)*

---

## 12. Troubleshooting

### Error 401 — Unauthorized

| Symptom | Cause | Fix |
|---|---|---|
| "API key required" | No `X-API-Key` header | Add header `X-API-Key: tdk_...` |
| "Invalid or revoked API key" | Wrong key or revoked | Check key, create a new one if needed |
| "Admin bearer token required" | Missing JWT for admin endpoint | Login via `/auth/admin/login` |
| "Customer bearer token required" | Missing JWT for customer endpoint | Login via `/auth/login` |

### Error 403 — Forbidden

"Customer account is inactive" — your account has been suspended. Contact support.

### Error 404 — Not Found

| Symptom | Cause | Fix |
|---|---|---|
| "HS code '999999' not found" | Code doesn't exist in our DB | Search first to confirm the exact code |
| "Reporter 'XX' not found" | Invalid country code | Use ISO alpha-2 codes (e.g., `IN`, `US`, `DE`) |
| "Plan 'gold' not found" | Invalid plan code | Use `GET /billing/plans` to see valid codes |

### Error 422 — Validation Error

A required parameter is missing or in wrong format. Read the `detail` array in the response — it pinpoints which field and why it failed.

### Error 429 — Rate Limit Exceeded

You've used all your daily calls. Options:
- Wait until 5:30 AM IST for the reset
- Upgrade to Paid plan for 10,000 calls/day

### Error 500 — Server Error

Something unexpected broke on our side. Email support@tradedataapi.in with the endpoint, parameters, and timestamp. We typically fix production issues within 4 hours.

### Server not responding (during local development)

The uvicorn server isn't running. In PowerShell:

```powershell
cd D:\all_py\trade-data-api\trade-data-api
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Leave that window open.

---

## 13. Glossary

| Term | Definition |
|---|---|
| **API** | Application Programming Interface — a way for two software systems to communicate |
| **API Key** | A unique secret token (`tdk_...`) that identifies your application and authorizes data requests |
| **Bearer Token** | The JWT token used in the `Authorization: Bearer ...` header for account management |
| **CAGR** | Compound Annual Growth Rate — the annualized growth rate over a multi-year period |
| **CIF** | Cost, Insurance, Freight — import value that includes shipping and insurance costs |
| **Comtrade** | UN Comtrade — the official UN database of international trade statistics |
| **Compliance** | The set of regulations, certifications, and documents required to legally trade a product between two countries |
| **DGFT** | Directorate General of Foreign Trade — India's government body regulating import-export |
| **FOB** | Free On Board — export value excluding shipping and insurance costs |
| **FTA** | Free Trade Agreement — a treaty between countries that reduces or eliminates tariffs |
| **GSP** | Generalised System of Preferences — lower tariffs that developed countries give to developing nations |
| **HS Code** | Harmonized System code — the 6-digit international standard for classifying traded goods |
| **ICEGATE** | Indian Customs Electronic Gateway — India's customs IT portal |
| **IEC** | Importer Exporter Code — a 10-digit code every Indian entity needs to import or export |
| **ISO Alpha-2** | 2-letter country code standard (e.g., `IN` = India, `US` = United States) |
| **JWT** | JSON Web Token — an encrypted login token valid for 8 hours |
| **MFN** | Most Favoured Nation — the standard tariff rate a WTO member applies to all other WTO members |
| **Paise** | 1/100th of an Indian Rupee. Our API stores prices in paise (₹1,999 = 199,900 paise) |
| **Rate Limit** | The maximum number of API calls allowed per day for your subscription tier |
| **Reporter** | In trade statistics, the country that reported the data to Comtrade |
| **REST API** | Representational State Transfer — a standard architectural style for web APIs |
| **Tariff** | A tax or duty imposed by a government on imported goods |
| **WITS** | World Integrated Trade Solution — World Bank platform for trade and tariff data |
| **WTO** | World Trade Organization — the international body governing trade rules |

---

*Trade Data API is built and maintained in India 🇮🇳*  
*For support: support@tradedataapi.in*  
*Documentation: http://localhost:8000/docs (development) | https://api.tradedataapi.in/docs (production)*
