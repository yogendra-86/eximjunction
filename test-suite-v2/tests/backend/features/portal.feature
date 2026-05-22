# features/portal.feature
Feature: Trade Data Portal
  As a business user
  I want to search and download trade data through a web interface
  So that I can make informed import-export decisions without coding

  Background:
    Given the API is running at base URL
    And I am logged in as a registered customer

  # ── Search ────────────────────────────────────────────────────────────────────

  @smoke @portal
  Scenario: Portal search returns results for valid HS code
    When I search the portal for HS code "090111" export flow
    Then the response status should be 200
    And the results list should not be empty
    And each result should have hs_code and value_usd and year
    And the plan should be "Free"
    And can_export should be false

  @portal
  Scenario: Free tier portal search is limited to 10 records
    When I search the portal for HS code "851712" export flow
    Then the response status should be 200
    And the results count should be at most 10
    And has_more may be true
    And tier_limit should be 10

  @portal
  Scenario: Portal search by keyword works
    When I search the portal with keyword "coffee" export flow
    Then the response status should be 200
    And the results list should not be empty

  @portal
  Scenario: Portal search with reporter filter works
    When I search the portal for HS "090111" reporter "IN" export flow
    Then the response status should be 200
    And all results reporter_iso should be "IN"

  @portal
  Scenario: Portal search with year range filter works
    When I search the portal for HS "090111" from 2022 to 2024
    Then all result years should be between 2022 and 2024

  @portal
  Scenario: Portal search without authentication is rejected
    When I search the portal without a token
    Then the response status should be 401

  # ── Export ────────────────────────────────────────────────────────────────────

  @portal
  Scenario: Free tier cannot export CSV
    Given I am on the free portal tier
    When I request a CSV export for HS "090111"
    Then the response status should be 403
    And the error should mention "Starter plan"

  @portal
  Scenario: Portal data status endpoint is public
    When I get the portal data status
    Then the response status should be 200
    And total_trade_flow_records should be present
    And hs_codes_covered should be present

  # ── Product Summary ───────────────────────────────────────────────────────────

  @smoke @portal
  Scenario: Product summary returns top exporters and trend data
    When I get the portal product summary for HS "090111" year 2024
    Then the response status should be 200
    And the hs_code should be "090111"
    And top_exporters should not be empty
    And each exporter should have iso and name and value_usd

  @portal
  Scenario: Product summary for non-existent HS code returns 404
    When I get the portal product summary for HS "999999" year 2024
    Then the response status should be 404

  # ── EXIM Services ────────────────────────────────────────────────────────────

  @smoke @portal
  Scenario: Service catalogue is publicly accessible
    When I get the EXIM service catalogue
    Then the response status should be 200
    And the catalogue should contain service "iec"
    And the catalogue should contain service "rcmc"
    And the catalogue should contain service "ad_code"
    And the catalogue should contain service "bundle"
    And the catalogue should contain service "retainer"
    And the IEC service price should be 299900

  @portal
  Scenario: Customer can submit an IEC service request
    When I submit an IEC service request with valid details
    Then the response status should be 201
    And the service_type should be "iec"
    And the status should be "submitted"
    And a reference ID should be returned

  @portal
  Scenario: Service request with invalid service type is rejected
    When I submit a service request with type "invalid_service"
    Then the response status should be 400

  @portal
  Scenario: Customer can view their own service requests
    Given I have submitted a service request
    When I get my service requests
    Then the response status should be 200
    And my submitted request should be in the list

  @portal
  Scenario: Service requests require authentication
    When I submit a service request without a token
    Then the response status should be 401

  # ── Portal Plans ─────────────────────────────────────────────────────────────

  @smoke @portal
  Scenario: Portal plans are publicly accessible and correctly priced
    When I get the portal plans
    Then the free plan records_per_search should be 10
    And the starter plan records_per_search should be 500
    And the pro plan records_per_search should be null
    And the starter plan can_export_csv should be true
    And the free plan can_export_csv should be false
    And the pro plan can_use_api should be true
