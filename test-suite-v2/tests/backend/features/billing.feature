# features/billing.feature
Feature: Billing and Subscription Management
  As a customer
  I want to manage my subscription and payments
  So that I can access the appropriate level of trade data

  Background:
    Given the API is running at base URL

  # ── Plans ─────────────────────────────────────────────────────────────────────

  @smoke @billing
  Scenario: Plans endpoint returns all active plans without authentication
    When I get the billing plans
    Then the response status should be 200
    And the plan list should contain "free"
    And the plan list should contain "paid"
    And the plan list should contain "paid_annual"
    And the free plan price should be 0
    And the paid plan price should be 199900
    And the annual plan price should be 1999000
    And the paid plan display should be "₹1,999/month"

  @billing
  Scenario: Free plan has correct daily request limit
    When I get the billing plans
    Then the free plan daily_request_limit should be 50

  @billing
  Scenario: Paid plan has correct daily request limit
    When I get the billing plans
    Then the paid plan daily_request_limit should be 10000

  # ── Subscription Auto-creation ───────────────────────────────────────────────

  @smoke @billing
  Scenario: New customer is automatically subscribed to free plan
    Given I register as a new customer
    When I check my subscription
    Then the response status should be 200
    And the subscription status should be "active"
    And the plan code should be "free"
    And current_period_end should be set

  # ── Checkout ─────────────────────────────────────────────────────────────────

  @smoke @billing
  Scenario: Paid plan checkout creates a Razorpay order in mock mode
    Given I am logged in as a registered customer
    When I initiate checkout for plan "paid"
    Then the response status should be 200
    And the order_id should start with "order_mock_"
    And the amount_paise should be 199900
    And the currency should be "INR"
    And mock_mode should be true
    And the customer email should be present in response

  @billing
  Scenario: Annual plan checkout has correct amount
    Given I am logged in as a registered customer
    When I initiate checkout for plan "paid_annual"
    Then the response status should be 200
    And the amount_paise should be 1999000

  @billing
  Scenario: Checkout for free plan is rejected
    Given I am logged in as a registered customer
    When I initiate checkout for plan "free"
    Then the response status should be 400

  @billing
  Scenario: Checkout for nonexistent plan is rejected
    Given I am logged in as a registered customer
    When I initiate checkout for plan "diamond_ultra"
    Then the response status should be 404

  @billing
  Scenario: Checkout without authentication is rejected
    When I initiate checkout for plan "paid" without a token
    Then the response status should be 401

  # ── Mock Payment Success ──────────────────────────────────────────────────────

  @smoke @billing
  Scenario: Successful mock payment activates subscription
    Given I am logged in as a registered customer
    And I have initiated checkout for plan "paid"
    When I complete the mock payment
    Then the response status should be 200
    And the subscription status should be "active"
    And the plan code should be "paid"
    And started_at should be set
    And current_period_end should be set

  @billing
  Scenario: After successful payment all API keys upgrade to paid tier
    Given I am logged in as a registered customer
    And I have created an API key on the free tier
    And I have initiated checkout for plan "paid"
    When I complete the mock payment
    Then all my active API keys should have tier "paid"

  @billing
  Scenario: After payment subscription endpoint reflects new plan
    Given I am logged in as a registered customer
    And I have initiated checkout for plan "paid"
    And I have completed the mock payment
    When I check my subscription
    Then the plan code should be "paid"

  @billing
  Scenario: Mock payment with unknown order ID returns 404
    Given I am logged in as a registered customer
    When I try to complete payment for order "order_mock_doesnotexist999"
    Then the response status should be 404

  # ── Payment History ───────────────────────────────────────────────────────────

  @billing
  Scenario: Payment history records successful payment
    Given I am logged in as a registered customer
    And I have completed a paid plan purchase
    When I get my payment history
    Then the response status should be 200
    And there should be at least 1 payment
    And the payment amount_paise should be 199900
    And the payment status should be "captured"
    And the payment currency should be "INR"

  # ── Rate Limits ───────────────────────────────────────────────────────────────

  @smoke @billing
  Scenario: Free tier API key usage is tracked correctly
    Given I am logged in as a registered customer
    And I have created an API key
    When I make 5 requests with that API key
    Then the usage report should show at least 5 total_requests_30d
    And the daily breakdown should contain today's date

  @billing
  Scenario: After upgrading to paid tier daily limit increases
    Given I am logged in as a registered customer
    And I have created an API key
    And I have completed a paid plan purchase
    When I check the usage report for my API key
    Then the daily_limit should be 10000

  @billing
  Scenario: Portal plans endpoint returns all portal tiers
    When I get the portal plans
    Then the response status should be 200
    And the portal plan list should contain "portal_free"
    And the portal plan list should contain "portal_starter"
    And the portal plan list should contain "portal_pro"
    And the portal plan list should contain "portal_enterprise"
