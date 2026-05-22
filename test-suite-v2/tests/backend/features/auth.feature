# features/auth.feature
Feature: Customer Authentication
  As a trade data customer
  I want to register and manage my account
  So that I can access trade data through the API

  Background:
    Given the API is running at base URL

  # â”€â”€ Registration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  @smoke @auth
  Scenario: Successful customer signup
    Given I have valid signup details
        When I submit the signup form
    Then the response status should be 201
    And the response should contain an access_token
    And the token type should be bearer
    And a free subscription should be auto-created
    And a default API key should be auto-created with tier free

  @auth
  Scenario: Duplicate email registration is rejected
    Given a customer with email "existing@example.com" is already registered
    When I try to signup with email "existing@example.com"
    Then the response status should be 409
    And the error detail should mention "already registered"

  @auth
  Scenario Outline: Invalid signup inputs are rejected
    When I submit signup with "<field>" as "<value>"
    Then the response status should be 422

    Examples:
      | field    | value          |
      | email    | not-an-email   |
      | email    | missing@       |
      | password | 123            |
      | password |                |

  # â”€â”€ Login â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  @smoke @auth
  Scenario: Successful customer login
    Given a registered customer with email "login_test@example.com" and password "LoginPass@1234"
    When I login with email "login_test@example.com" and password "LoginPass@1234"
    Then the response status should be 200
    And the response should contain an access_token
    And expires_in_minutes should be 480

  @auth
  Scenario: Login with wrong password is rejected
    Given a registered customer with email "wrongpass@example.com" and password "RightPass@1234"
    When I login with email "wrongpass@example.com" and password "WrongPass@9999"
    Then the response status should be 401

  @auth
  Scenario: Login with non-existent email is rejected
    When I login with email "nobody@nowhere.com" and password "AnyPass@1234"
    Then the response status should be 401

  @auth
  Scenario: JWT token grants access to protected customer endpoint
    Given a registered customer with email "token_test@example.com" and password "TokenPass@1234"
    And I have logged in as that customer
    When I call GET /auth/me with the customer token
    Then the response status should be 200
    And the email in response should be "token_test@example.com"

  @auth @security
  Scenario: Expired or invalid token is rejected
    When I call GET /auth/me with token "Bearer invalid.token.here"
    Then the response status should be 401

  @auth @security
  Scenario: Admin token cannot access customer endpoint
    Given I have a valid admin token
    When I call GET /auth/me with the admin token
    Then the response status should be 401

  @auth @security
  Scenario: Customer token cannot access admin endpoint
    Given a registered customer with email "scope_test@example.com" and password "ScopePass@1234"
    And I have logged in as that customer
    When I call GET /auth/admin/me with the customer token
    Then the response status should be 401

  # â”€â”€ API Key Management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  @smoke @auth
  Scenario: Customer can create a named API key
    Given I am logged in as a registered customer
    When I create an API key named "Production Key"
    Then the response status should be 201
    And the plaintext_key should start with "tdk_"
    And the key_prefix should be the first 12 characters of plaintext_key
    And the key name should be "Production Key"
    And the tier should be "free"

  @auth
  Scenario: Revoked API key no longer grants data access
    Given I am logged in as a registered customer
    And I have created an API key
    When I revoke that API key
    Then the API key should return 401 on data endpoints

  @auth @security
  Scenario: Customer cannot revoke another customer's API key
    Given two registered customers exist
    When customer A tries to revoke customer B's API key
    Then the response status should be 404

  # â”€â”€ Admin Login â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  @smoke @auth
  Scenario: Admin can login with correct credentials
    When I login as admin with correct credentials
    Then the response status should be 200
    And the response should contain an access_token

  @auth
  Scenario: Admin login with wrong password fails
    When I login as admin with wrong password
    Then the response status should be 401
