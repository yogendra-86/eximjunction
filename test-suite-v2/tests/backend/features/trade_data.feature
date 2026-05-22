# features/trade_data.feature
Feature: Trade Data API Endpoints
  As a developer with an API key
  I want to query global trade data
  So that I can build trade intelligence into my application

  Background:
    Given the API is running at base URL
    And I have a valid API key

  # Ã¢â€â‚¬Ã¢â€â‚¬ HS Code Search Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

  @smoke @trade
  Scenario: Search HS codes by keyword returns results
    When I search for products with keyword "coffee"
    Then the response status should be 200
    And the results should contain at least 1 item
    And all results should mention "coffee" in description

  @trade
  Scenario: Numeric HS code search returns prefix matches
    When I search for products with keyword "0901"
    Then the response status should be 200
    And all result codes should start with "0901"

  @trade
  Scenario Outline: Level filter returns correct hierarchy depth
    When I search for products with keyword "coffee" and level "<level>"
    Then all results should have level <expected_level>

    Examples:
      | level | expected_level |
      | 2     | 2              |
      | 4     | 4              |
      | 6     | 6              |

  @trade
  Scenario: Search with no matches returns empty list not error
    When I search for products with keyword "xyznonexistentproduct123"
    Then the response status should be 200
    And the result list should be empty

  @trade @security
  Scenario: Search without API key is rejected
    When I search for products without an API key
    Then the response status should be 401

  @trade @security
  Scenario: Search with invalid API key is rejected
    When I search with API key "tdk_completely_fake_invalid_key"
    Then the response status should be 401

  # Ã¢â€â‚¬Ã¢â€â‚¬ Product Detail Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

  @smoke @trade
  Scenario: HS code detail returns correct hierarchy
    When I get details for HS code "090111"
    Then the response status should be 200
    And the code should be "090111"
    And the level should be 6
    And there should be 2 ancestors
    And the first ancestor code should be "09"
    And the second ancestor code should be "0901"

  @trade
  Scenario: Chapter level HS code has children and no ancestors
    When I get details for HS code "09"
    Then the response status should be 200
    And the ancestors list should be empty
    And there should be at least 1 child

  @trade
  Scenario: Non-existent HS code returns 404
    When I get details for HS code "999999"
    Then the response status should be 404

  # Ã¢â€â‚¬Ã¢â€â‚¬ Top Trading Partners Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

  @smoke @trade
  Scenario: Top export partners for India coffee are ranked correctly
    When I get top partners for HS "090111" with reporter "IN" flow "export" year 2024
    Then the response status should be 200
    And the reporter country should be "IN"
    And partners should be ranked sequentially starting from 1
    And partners should be sorted by value_usd descending
    And the first partner should be "US"

  @trade
  Scenario: Global top exporters returns results without reporter
    When I get top partners for HS "270900" flow "export" year 2024 without reporter
    Then the response status should be 200
    And the reporter field should be null
    And there should be at least 1 partner

  @trade
  Scenario: Top partners with limit parameter respects the limit
    When I get top partners for HS "090111" flow "export" year 2024 with limit 3
    Then the number of partners should be at most 3

  @trade
  Scenario: Invalid flow value is rejected
    When I get top partners with flow "sideways"
    Then the response status should be 422

  # Ã¢â€â‚¬Ã¢â€â‚¬ Trade Flow Trends Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

  @smoke @trade
  Scenario: Trade flow trend returns 6 data points for 2019-2024
    When I get trade flows for IN to US for HS "090111" export 2019 to 2024
    Then the response status should be 200
    And there should be exactly 6 data points
    And the first point year should be 2019
    And the last point year should be 2024
    And total_value_usd should be greater than 0
    And growth_rate_pct should not be null

  @trade
  Scenario: year_from greater than year_to returns 400
    When I get trade flows with year_from 2024 and year_to 2019
    Then the response status should be 400

  @trade
  Scenario: Invalid reporter country returns 404
    When I get trade flows with reporter "ZZ" partner "US" hs "090111"
    Then the response status should be 404

  @trade
  Scenario: Future year range returns empty points list
    When I get trade flows for IN to US for HS "090111" export 2029 to 2030
    Then the response status should be 200
    And the points list should be empty

  # Ã¢â€â‚¬Ã¢â€â‚¬ Tariffs Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

  @smoke @trade
  Scenario: US MFN tariff on cotton T-shirts is 16.5 percent
    When I get tariffs for reporter "US" hs "610910" year 2024
    Then the response status should be 200
    And there should be at least 1 tariff result
    And the MFN rate should be 16.5

  @trade
  Scenario: USMCA preferential rate for US-Mexico cars is zero
    When I get tariffs for reporter "US" partner "MX" hs "870323" year 2024
    Then the response status should be 200
    And a preferential rate type should exist
    And the preferential rate should be 0.0
    And the agreement should be "USMCA"

  @trade
  Scenario: No tariff data returns empty list not error
    When I get tariffs for reporter "IN" hs "090411" year 2024
    Then the response status should be 200
    And the result list should be empty

  # Ã¢â€â‚¬Ã¢â€â‚¬ Compliance Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

  @smoke @trade
  Scenario: India to US general compliance returns core documents
    When I get compliance for reporter "IN" partner "US"
    Then the response status should be 200
    And the corridor should be "IN -> US"
    And "Commercial Invoice" should be in the documents
    And "Packing List" should be in the documents
    And "Importer-Exporter Code (IEC)" should be in the documents

  @trade
  Scenario: Pharma exports to US include FDA requirement
    When I get compliance for reporter "IN" partner "US" hs "300490"
    Then at least one document name should contain "FDA"

  @trade
  Scenario: Diamond exports include Kimberley Process certificate
    When I get compliance for reporter "IN" partner "BE" hs "710231"
    Then "Kimberley Process Certificate" should be in the documents

  @trade
  Scenario: Mandatory documents appear before optional ones
    When I get compliance for reporter "IN" partner "US"
    Then all mandatory documents should appear before optional ones

  @trade
  Scenario: Invalid reporter country returns 404
    When I get compliance for reporter "XX" partner "US"
    Then the response status should be 404

  # Ã¢â€â‚¬Ã¢â€â‚¬ Countries Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

  @smoke @trade
  Scenario: Countries list returns all supported countries
    When I get the countries list
    Then the response status should be 200
    And there should be at least 32 countries
    And "IN" should be in the country list
    And "US" should be in the country list

  @trade
  Scenario: Country lookup by ISO alpha-2 returns correct country
    When I look up country "IN"
    Then the name should be "India"
    And the iso_alpha3 should be "IND"
    And the m49_code should be 356

  @trade
  Scenario: Country lookup by ISO alpha-3 works
    When I look up country "USA"
    Then the iso_alpha2 should be "US"

  @trade
  Scenario: Invalid country code returns 404
    When I look up country "XX"
    Then the response status should be 404
