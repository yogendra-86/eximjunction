# features/signup_login.feature
Feature: Customer Signup and Login
  As a new visitor
  I want to create an account and log in
  So that I can access trade data through the portal

  @smoke @frontend
  Scenario: Successful signup redirects to dashboard
    Given I open the signup page
    When I fill in the signup form with valid details
    And I submit the signup form
    Then I should be redirected to the dashboard
    And the dashboard should show my name

  @frontend
  Scenario: Signup with duplicate email shows error message
    Given I have already signed up with email "duplicate_fe@example.com"
    And I open the signup page
    When I fill email "duplicate_fe@example.com" and password "Pass@1234"
    And I submit the signup form
    Then an error message should be visible
    And the error should mention "already registered"

  @frontend
  Scenario: Signup with short password shows validation error
    Given I open the signup page
    When I fill email "shortpass@example.com" and password "abc"
    And I submit the signup form
    Then the form should not submit due to validation

  @frontend
  Scenario: Login link on signup page navigates correctly
    Given I open the signup page
    When I click the login link
    Then I should be on the login page

  @smoke @frontend
  Scenario: Successful login redirects to dashboard
    Given I have an account with email "login_fe@example.com" and password "Login@1234"
    And I open the login page
    When I fill email "login_fe@example.com" and password "Login@1234"
    And I click the login button
    Then I should be redirected to the dashboard

  @frontend
  Scenario: Login with wrong password shows error
    Given I have an account with email "wrongpass_fe@example.com" and password "Right@1234"
    And I open the login page
    When I fill email "wrongpass_fe@example.com" and password "Wrong@9999"
    And I click the login button
    Then an error message should be visible

  @frontend
  Scenario: Logged in user sees dashboard link in navbar
    Given I am logged in as a customer
    When I open the landing page
    Then the navbar should show "Dashboard" link
    And the navbar should show "Logout" button

  @frontend
  Scenario: Logout clears session and redirects to home
    Given I am logged in as a customer
    When I click the logout button
    Then I should be on the landing page
    And the navbar should show "Login" link
