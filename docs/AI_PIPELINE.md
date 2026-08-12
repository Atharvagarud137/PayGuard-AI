# AI_PIPELINE.md — PayGuard AI

## Purpose

This document describes how the AI Engine works internally — specifically the Root Cause Analysis (RCA) pipeline and the Test Case Generator — covering data flow, embedding strategy, storage, and prompt design.

## Pipeline 1: Root Cause Analysis (RCA)

### Objective

When a test fails, automatically analyze the failure log and produce a plain-language root cause summary, drawing on similar past failures for context.

### Step-by-Step Flow

| Step | Description |
|---|---|
| 1. Failure Capture | When a Pytest or Selenium test fails, the test framework captures the test name, stack trace, request/response payload (if applicable), and timestamp into a structured log entry |
| 2. Log Formatting | The failure is converted into a standardized text document combining all relevant fields, making it suitable for embedding |
| 3. Embedding | The formatted failure text is converted into a vector embedding using a local embedding model (via Ollama or a lightweight sentence-transformer) |
| 4. Similarity Search | ChromaDB is queried for the top-k most similar past failures using the new embedding |
| 5. Context Assembly | The current failure plus the retrieved similar past failures (and their previously generated RCA summaries, if available) are assembled into a prompt |
| 6. LLM Generation | The assembled prompt is sent to the local LLM (via Ollama) to generate a root cause summary, including a likely category (e.g., timeout, validation error, network decline, assertion mismatch) |
| 7. Storage | The new failure, its embedding, and the generated RCA summary are stored back into ChromaDB, enriching future similarity searches |
| 8. Output | The RCA summary is written to the CI job logs and saved as a markdown artifact |

### RCA Prompt Structure (Conceptual)

The prompt given to the LLM includes: the failing test name, the stack trace or assertion error, the relevant request/response payload, and up to three similar historical failures with their prior root cause summaries. The LLM is instructed to identify the most likely root cause category, explain its reasoning briefly, and suggest a corrective action if possible.

### Root Cause Categories (Classification Targets)

| Category | Example Trigger |
|---|---|
| Timeout | Settlement endpoint simulated with `X-Simulate-Failure: TIMEOUT` |
| Validation Error | Missing or malformed request fields |
| Network Decline | Insufficient funds or card inactive scenarios |
| Assertion Mismatch | Test expected one status, API returned another (potential regression) |
| Environment Issue | Service unavailable, connection refused, Docker container not running |

## Pipeline 2: AI Test Case Generator

### Objective

Automatically propose additional edge-case test scenarios by analyzing the Mock Payment Gateway's OpenAPI specification.

### Step-by-Step Flow

| Step | Description |
|---|---|
| 1. Spec Retrieval | The generator fetches the live OpenAPI spec from `/openapi.json` on the running Mock Payment Gateway |
| 2. Endpoint Parsing | Each endpoint's parameters, request schema, and response schema are extracted |
| 3. Prompt Construction | For each endpoint, a prompt is built asking the LLM to propose edge cases not already covered, given the field types and constraints |
| 4. LLM Generation | The local LLM (via Ollama) generates a list of suggested test scenarios per endpoint, including expected behavior |
| 5. Deduplication Check | Suggestions are compared against the existing test suite (by reading test function docstrings/names) to avoid proposing duplicates |
| 6. Output | Suggestions are compiled into a markdown report (`test_suggestions.md`) for manual review, categorized by endpoint |

### Example Suggestion Categories

| Category | Example |
|---|---|
| Boundary values | Authorization amount exactly equal to available balance |
| Type mismatches | Sending a string where a number is expected |
| Missing optional vs required fields | Omitting merchant_id in an authorization request |
| State transition violations | Attempting settlement before capture |
| Concurrency scenarios | Two simultaneous capture requests on the same transaction |

## Storage Design (ChromaDB)

| Collection | Contents | Used By |
|---|---|---|
| `failure_logs` | Embedded failure texts + metadata (test name, timestamp, category, RCA summary) | RCA Pipeline |
| `test_suggestions_history` | Previously suggested test cases per endpoint, to avoid duplicate suggestions across runs | Test Case Generator |

## Local LLM Configuration

| Setting | Value |
|---|---|
| Runtime | Ollama |
| Model | Llama 3.1 8B or Phi-3 (whichever runs comfortably on local hardware) |
| Embedding Model | A lightweight local embedding model compatible with Ollama or sentence-transformers |
| Temperature | Low (0.2–0.3) to keep RCA and suggestions focused and consistent rather than creative |

## Integration with CI/CD

The RCA pipeline is triggered as a dependent job in GitHub Actions that only runs if the test job fails, reading failure artifacts produced by that job. The Test Case Generator runs on a separate, manually triggered or scheduled workflow, since it doesn't depend on test failures and is more of a periodic review tool.

## Limitations and Considerations

Local LLM outputs may be less polished than hosted models like GPT-4, so RCA summaries and test suggestions should be treated as assistive drafts requiring human review rather than fully autonomous decisions — this is intentionally reflected in the CI design, where outputs are surfaced as artifacts/reports rather than auto-merged or auto-acted upon.