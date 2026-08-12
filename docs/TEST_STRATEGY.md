# TEST_STRATEGY.md — PayGuard AI

## Purpose

This document defines the testing approach for PayGuard AI itself — both how we test the Mock Payment Gateway and Dashboard (the system under test), and how we validate that the AI Engine's outputs (RCA summaries, test case suggestions) are useful and accurate.

## Test Pyramid

| Layer | Tool | Proportion | Purpose |
|---|---|---|---|
| Unit Tests | Pytest | 50% | Validate individual functions in the payment gateway (e.g., card validation logic, amount calculations, status transitions) |
| API/Integration Tests | Pytest + HTTPX | 35% | Validate full payment flows end-to-end through the API (issuance → authorization → capture → settlement → refund) |
| UI Tests | Selenium | 10% | Validate dashboard displays correct transaction data and status updates |
| AI Validation Tests | Custom Pytest checks | 5% | Validate AI RCA and test case generation produce structurally correct, relevant outputs |

## Payment Flow Test Coverage

| Flow | Positive Cases | Negative Cases | Boundary Cases |
|---|---|---|---|
| Card Issuance | Valid card created successfully | Invalid card details rejected | Duplicate card number handling |
| Authorization | Sufficient balance approved | Insufficient balance declined | Exact balance match (edge case) |
| Capture | Full amount captured | Capture exceeds authorized amount rejected | Capture of zero amount |
| Settlement | Successful batch settlement | Settlement of already-settled transaction rejected | Settlement timeout simulation |
| Refund | Full refund processed | Refund exceeds original amount rejected | Partial refund followed by full refund attempt |

## AI-Augmentation Points

| Testing Activity | Without AI | With AI (PayGuard AI Approach) |
|---|---|---|
| Diagnosing test failures | Manually reading logs and stack traces | AI RCA Engine retrieves similar past failures and generates a plain-language root cause summary |
| Designing new test cases | Manually reviewing API spec for edge cases | AI Test Case Generator reads the OpenAPI spec and proposes edge cases automatically |
| Tracking recurring failure patterns | Manual log review over time | ChromaDB stores embedded failure history, allowing the RCA engine to recognize recurring issues |

## AI Output Validation Criteria

Since AI-generated content needs its own quality bar, we validate it as follows:

| AI Feature | Validation Method | Success Criteria |
|---|---|---|
| RCA Summary | Manual review against known injected failures | Correctly identifies failure category (e.g., timeout, validation error, decline) in at least 8 of 10 test cases |
| Test Case Suggestions | Manual review for relevance and non-duplication | At least 5 relevant, non-duplicate edge cases suggested per endpoint |

## Test Environment Strategy

| Environment | Purpose |
|---|---|
| Local (Docker Compose) | Development and manual testing |
| CI (GitHub Actions) | Automated test execution on every push, using service containers for the gateway, dashboard, ChromaDB, and Ollama |

## Failure Handling and RCA Trigger Flow

1. A test fails during CI execution.
2. The failure log (test name, stack trace, request/response payload) is captured and saved as a CI artifact.
3. The RCA pipeline is triggered automatically as a subsequent CI job, reading the failure artifact.
4. The RCA Engine embeds the failure text, queries ChromaDB for similar historical failures, and generates a summary using the local LLM.
5. The summary is posted to the CI job output/logs for review.

## Regression Strategy

All API and UI tests run on every push to any branch. A nightly scheduled run (via GitHub Actions cron) executes the full suite including AI validation tests, ensuring AI outputs remain consistent as the underlying model or prompt templates evolve.

## Tools Summary

| Tool | Purpose |
|---|---|
| Pytest | Unit and API test execution |
| HTTPX | HTTP client for API testing |
| Selenium | Browser automation for UI testing |
| LangChain | Orchestrating LLM calls for RCA and test generation |
| ChromaDB | Vector storage for failure embeddings |
| Ollama | Local LLM inference |
| GitHub Actions | CI/CD execution and scheduling |