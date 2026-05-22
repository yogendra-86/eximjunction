"""End-to-end API tests covering each endpoint."""

PREFIX = "/api/v1"


# --- health & root ---

def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Trade Data API"
    assert body["api_prefix"] == PREFIX


def test_health(client):
    r = client.get(f"{PREFIX}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["db_ok"] is True


# --- countries ---

def test_list_countries(client):
    r = client.get(f"{PREFIX}/countries")
    assert r.status_code == 200
    countries = r.json()
    assert len(countries) >= 30
    iso_codes = {c["iso_alpha2"] for c in countries}
    assert {"IN", "US", "CN", "DE"}.issubset(iso_codes)


def test_get_country_by_iso2(client):
    r = client.get(f"{PREFIX}/countries/IN")
    assert r.status_code == 200
    assert r.json()["name"] == "India"
    assert r.json()["iso_alpha3"] == "IND"


def test_get_country_by_iso3(client):
    r = client.get(f"{PREFIX}/countries/USA")
    assert r.status_code == 200
    assert r.json()["iso_alpha2"] == "US"


def test_country_not_found(client):
    r = client.get(f"{PREFIX}/countries/XX")
    assert r.status_code == 404


# --- product search ---

def test_product_search_keyword(client):
    r = client.get(f"{PREFIX}/products/search", params={"q": "coffee"})
    assert r.status_code == 200
    results = r.json()
    assert len(results) > 0
    # at least one result should mention coffee
    assert any("coffee" in p["description"].lower() for p in results)


def test_product_search_numeric(client):
    r = client.get(f"{PREFIX}/products/search", params={"q": "0901"})
    assert r.status_code == 200
    results = r.json()
    assert len(results) > 0
    # all matches should start with 0901
    assert all(p["code"].startswith("0901") for p in results)


def test_product_search_with_level_filter(client):
    r = client.get(f"{PREFIX}/products/search", params={"q": "0", "level": 2})
    assert r.status_code == 200
    results = r.json()
    assert all(p["level"] == 2 for p in results)


def test_product_detail_with_hierarchy(client):
    r = client.get(f"{PREFIX}/products/090111")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == "090111"
    assert body["level"] == 6
    # ancestors should be 0901 (heading) and 09 (chapter), in order
    assert [a["code"] for a in body["ancestors"]] == ["09", "0901"]


def test_product_detail_chapter_has_children(client):
    r = client.get(f"{PREFIX}/products/09")
    assert r.status_code == 200
    body = r.json()
    assert len(body["children"]) > 0
    assert all(c["parent_code"] == "09" for c in body["children"])


def test_product_not_found(client):
    r = client.get(f"{PREFIX}/products/999999")
    assert r.status_code == 404


# --- top trading partners ---

def test_top_partners_for_reporter(client):
    r = client.get(
        f"{PREFIX}/products/090111/top-partners",
        params={"reporter": "IN", "flow": "export", "year": 2024, "limit": 5},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["hs_code"] == "090111"
    assert body["reporter"]["iso_alpha2"] == "IN"
    assert len(body["partners"]) <= 5
    assert len(body["partners"]) > 0
    # ranks should be sequential and values should be descending
    ranks = [p["rank"] for p in body["partners"]]
    values = [p["value_usd"] for p in body["partners"]]
    assert ranks == list(range(1, len(ranks) + 1))
    assert values == sorted(values, reverse=True)
    # for IN coffee export, US should be the top partner
    assert body["partners"][0]["country"]["iso_alpha2"] == "US"


def test_top_partners_global(client):
    """Without reporter param, returns top reporters globally for the product."""
    r = client.get(
        f"{PREFIX}/products/270900/top-partners",
        params={"flow": "export", "year": 2024},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["reporter"] is None
    # crude oil's top exporter in our seed data should be SA
    assert body["partners"][0]["country"]["iso_alpha2"] == "SA"


def test_top_partners_invalid_flow(client):
    r = client.get(
        f"{PREFIX}/products/090111/top-partners",
        params={"flow": "invalid"},
    )
    assert r.status_code == 422


# --- trade flow trends ---

def test_trade_flow_trend(client):
    r = client.get(
        f"{PREFIX}/trade-flows",
        params={
            "reporter": "IN", "partner": "US", "hs_code": "090111",
            "flow": "export", "year_from": 2019, "year_to": 2024,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["reporter"]["iso_alpha2"] == "IN"
    assert body["partner"]["iso_alpha2"] == "US"
    assert len(body["points"]) == 6  # 2019..2024
    assert body["points"][0]["year"] == 2019
    assert body["points"][-1]["year"] == 2024
    assert body["total_value_usd"] > 0
    assert body["growth_rate_pct"] is not None


def test_trade_flow_trend_invalid_year_range(client):
    r = client.get(
        f"{PREFIX}/trade-flows",
        params={
            "reporter": "IN", "partner": "US", "hs_code": "090111",
            "year_from": 2024, "year_to": 2019,
        },
    )
    assert r.status_code == 400


def test_trade_flow_trend_unknown_country(client):
    r = client.get(
        f"{PREFIX}/trade-flows",
        params={"reporter": "ZZ", "partner": "US", "hs_code": "090111"},
    )
    assert r.status_code == 404


# --- tariffs ---

def test_tariffs_mfn(client):
    """When partner is omitted, returns MFN rate (and any partner-specific rates)."""
    r = client.get(
        f"{PREFIX}/tariffs",
        params={"reporter": "US", "hs_code": "610910", "year": 2024},
    )
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 1
    # MFN rate for cotton T-shirts in US is 16.5
    mfn = next(t for t in rows if t["rate_type"] == "MFN")
    assert mfn["ad_valorem_rate"] == 16.5


def test_tariffs_with_partner(client):
    """USMCA preferential rate should appear alongside MFN."""
    r = client.get(
        f"{PREFIX}/tariffs",
        params={"reporter": "US", "partner": "MX", "hs_code": "870323", "year": 2024},
    )
    assert r.status_code == 200
    rows = r.json()
    rate_types = {t["rate_type"] for t in rows}
    assert "preferential" in rate_types
    pref = next(t for t in rows if t["rate_type"] == "preferential")
    assert pref["agreement"] == "USMCA"
    assert pref["ad_valorem_rate"] == 0.0


def test_tariffs_no_data_returns_empty(client):
    """Querying for a product/country with no tariff rows should return [], not 404."""
    r = client.get(
        f"{PREFIX}/tariffs",
        params={"reporter": "IN", "hs_code": "090411", "year": 2024},
    )
    assert r.status_code == 200
    assert r.json() == []


# --- compliance ---

def test_compliance_general_corridor(client):
    """Without HS code, only general/corridor docs returned."""
    r = client.get(
        f"{PREFIX}/compliance",
        params={"reporter": "IN", "partner": "US"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["corridor"] == "IN -> US"
    names = [d["document_name"] for d in body["documents"]]
    # general docs should appear
    assert "Commercial Invoice" in names
    assert "Packing List" in names
    # IN-specific docs should appear (since reporter=IN)
    assert "Importer-Exporter Code (IEC)" in names
    # US-specific import doc
    assert "Importer Security Filing (10+2)" in names


def test_compliance_with_hs_code_includes_product_docs(client):
    """With HS code 090111, phytosanitary cert should be included."""
    r = client.get(
        f"{PREFIX}/compliance",
        params={"reporter": "IN", "partner": "US", "hs_code": "090111"},
    )
    assert r.status_code == 200
    body = r.json()
    names = [d["document_name"] for d in body["documents"]]
    assert "Phytosanitary Certificate" in names


def test_compliance_diamond_kimberley(client):
    """Diamonds require Kimberley Process certification."""
    r = client.get(
        f"{PREFIX}/compliance",
        params={"reporter": "IN", "partner": "BE", "hs_code": "710231"},
    )
    assert r.status_code == 200
    names = [d["document_name"] for d in r.json()["documents"]]
    assert "Kimberley Process Certificate" in names


def test_compliance_pharma_to_us_includes_fda(client):
    """Exporting pharma to US should include FDA prior notice."""
    r = client.get(
        f"{PREFIX}/compliance",
        params={"reporter": "IN", "partner": "US", "hs_code": "300490"},
    )
    assert r.status_code == 200
    names = [d["document_name"] for d in r.json()["documents"]]
    assert any("FDA" in n for n in names)
