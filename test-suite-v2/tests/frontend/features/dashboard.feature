Feature: Customer Dashboard
  As a logged-in customer
  I want to manage my API keys and subscription
  So that I can access the trade data API

  @smoke @frontend
  Scenario: Dashboard overview shows subscription status
    Given I am logged in as a customer
    When I open the dashboard
    Then the subscription plan should be visible
    And the daily usage stats should be visible
    And the usage chart should be visible
    And the sidebar should show all navigation items

  @frontend
  Scenario: API Keys page allows creating a new key
    Given I am logged in as a customer
    When I open the API Keys page
    And I create a key named "My Test Key"
    Then the new key should appear in the list
    And the key should start with "tdk_"
    And a copy warning should be shown

  @frontend
  Scenario: Billing page shows current plan
    Given I am logged in as a customer
    When I open the Billing page
    Then the current plan should show "Free"
    And the upgrade button should be visible

  @frontend
  Scenario: Dashboard sidebar Data Portal link works
    Given I am logged in as a customer
    When I open the dashboard
    And I click "Data Portal" in the sidebar
    Then I should be on the portal search page

  @frontend
  Scenario: Dashboard sidebar EXIM Docs link works
    Given I am logged in as a customer
    When I open the dashboard
    And I click "EXIM Docs" in the sidebar
    Then I should be on the services page