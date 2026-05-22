Feature: Trade Data Portal Search
  As a logged-in business user
  I want to search and view trade data
  So that I can make informed import-export decisions

  @smoke @frontend
  Scenario: Portal search page loads with all filters
    Given I am logged in as a customer
    When I open the portal search page
    Then the HS code input should be visible
    And the flow selector should be visible
    And the reporter selector should be visible
    And the year range selectors should be visible
    And 6 popular search buttons should be visible

  @smoke @frontend
  Scenario: Search by HS code returns results table
    Given I am logged in as a customer
    When I open the portal search page
    And I enter HS code "090111"
    And I click the search button
    Then I should be redirected to the results page
    And the results table should be visible

  @frontend
  Scenario: Services page shows all service cards
    Given I am logged in as a customer
    When I open the services page
    Then I should see 5 service cards
    And "IEC Registration" card should be visible
    And the IEC card should show "2,999"

  @smoke @frontend
  Scenario: Submitting a service request shows success message
    Given I am logged in as a customer
    When I open the services page
    And I click the IEC Registration request button
    And I fill in the service request form
    And I submit the service request
    Then a success message should be visible
    And the message should contain "submitted successfully"