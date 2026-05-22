# features/landing.feature
Feature: Landing Page
  As a potential customer
  I want to understand what EximJunction offers
  So that I can decide whether to sign up

  @smoke @frontend
  Scenario: Landing page loads with hero section
    Given I open the landing page
    Then the page title should contain "EximJunction"
    And the hero heading should be visible
    And the navbar should show "Data Portal" link
    And the navbar should show "Pricing" link
    And the navbar should show "EXIM Services" link
    And the navbar should show "API Docs" link

  @frontend
  Scenario: Navigation to portal from navbar works
    Given I open the landing page
    When I click "Data Portal" in the navbar
    Then I should be on the portal search page

  @frontend
  Scenario: Navigation to pricing from navbar works
    Given I open the landing page
    When I click "Pricing" in the navbar
    Then I should be on the pricing page

  @frontend
  Scenario: Three product cards are visible on landing page
    Given I open the landing page
    Then I should see the "Trade Data Portal" product card
    And I should see the "EXIM Documentation" product card
    And I should see the "Trade Data API" product card

  @frontend
  Scenario: API Docs link opens backend docs
    Given I open the landing page
    When I click "API Docs" in the navbar
    Then a new tab should open with URL containing "8000/docs"

  @smoke @frontend
  Scenario: Interactive demo section is visible
    Given I open the landing page
    When I scroll to the demo section
    Then the demo section should be visible
    And 5 query buttons should be present
    And the result panel should show "Select a query"
