# AI_PIPELINE.md — PayGuard AI

## Purpose

This document defines the planned AI architecture for PayGuard AI.

The AI layer is intended to augment the project's test automation capabilities rather than replace deterministic automated testing or human engineering judgment.

The planned AI capabilities are:

1. **AI-assisted Root Cause Analysis (RCA)** for test failures
2. **AI-assisted Test Case Generation** from the Mock Payment Gateway's OpenAPI specification

The AI layer is intentionally planned after the payment-domain and reliability foundation. The current Mock Payment Gateway, transaction lifecycle, service layer, repository abstraction, and automated regression suite provide the deterministic foundation that the AI layer will eventually analyze.

> **Current status:** The AI pipelines described in this document are architectural designs and are not yet implemented.

---

# AI Architecture Overview

The planned AI architecture consists of two independent workflows.

```text
                         PayGuard AI
                              |
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
       Root Cause Analysis            Test Case Generator
              │                               │
              ▼                               ▼
       Test Failure Data              OpenAPI Specification
              │                               │
              ▼                               ▼
       Context Extraction             Endpoint Analysis
              │                               │
              ▼                               ▼
       Embedding / Retrieval             LLM Analysis
              │                               │
              ▼                               ▼
          ChromaDB                    Scenario Suggestions
              │                               │
              ▼                               ▼
       Local LLM via Ollama             Human Review
              │
              ▼
        RCA Report
````

The two pipelines solve different problems:

| Pipeline       | Input                                                     | Output                    | Primary Goal                        |
| -------------- | --------------------------------------------------------- | ------------------------- | ----------------------------------- |
| RCA            | Test failure, logs, stack trace, request/response context | Root cause summary        | Reduce failure-investigation effort |
| Test Generator | OpenAPI specification and existing test context           | Test scenario suggestions | Identify missing edge cases         |

---

# Current AI Status

The AI layer is currently **planned**.

No AI-generated RCA or test-case output should currently be treated as part of the project's implemented functionality.

### Current foundation

The following capabilities already provide the inputs required for the future AI layer:

* Mock Payment Gateway
* Card issuance
* Authorization
* Capture
* Settlement
* Full refunds
* Partial refunds
* Transaction lookup
* Transaction history
* Transaction state machine
* Payment service layer
* Repository abstraction
* Deterministic API failure simulation
* Automated API tests
* Automated service tests
* Automated state-machine tests

The current regression baseline is:

```text
36 API tests
14 Payment Service tests
14 State Machine tests
-----------------------
64 total tests
64 passed
0 failed
```

The AI layer should consume this deterministic test and failure data rather than attempting to replace the underlying test architecture.

---

# Design Principles

## 1. Deterministic Testing Comes First

AI should not be used to determine whether the payment system behaves correctly when deterministic tests can make that decision.

The intended hierarchy is:

```text
Payment Domain
      |
      v
Deterministic Automated Tests
      |
      v
Failure Data
      |
      v
AI Analysis
```

The test suite remains the source of truth for pass/fail behavior.

The AI layer assists with understanding failures and identifying additional scenarios.

---

## 2. AI Output Is Advisory

AI-generated output must initially be treated as an engineering aid rather than an authoritative decision.

```text
AI Output
    |
    v
Human / QA Review
    |
    v
Accepted / Modified / Rejected
```

The system should not automatically:

* Mark a failed test as passed
* Modify production code
* Merge generated tests
* Suppress failures
* Declare a root cause as confirmed without supporting evidence

This is particularly important for payment-system testing, where a plausible but incorrect explanation can be more dangerous than an obvious failure.

---

## 3. Local-First AI

The planned implementation uses local AI infrastructure where practical.

The intended architecture is:

```text
Application / Test Data
        |
        v
Local Embeddings
        |
        v
ChromaDB
        |
        v
Ollama
        |
        v
Local LLM
```

This approach supports:

* Local experimentation
* Reproducible demonstrations
* Reduced dependency on hosted AI APIs
* Lower external API cost
* Better control over test and failure data

---

## 4. Retrieval Before Generation

The RCA pipeline should not rely exclusively on the current stack trace.

Historical failures should be retrieved first:

```text
Current Failure
      |
      v
Embedding
      |
      v
Similarity Search
      |
      v
Historical Failures
      |
      v
Context Assembly
      |
      v
LLM
      |
      v
RCA Summary
```

This allows recurring failure patterns to become increasingly useful over time.

---

# Pipeline 1 — Root Cause Analysis

## Objective

The RCA pipeline is intended to analyze failed automated tests and produce a concise, evidence-based explanation of the likely cause.

The system should use:

* Test name
* Failure message
* Stack trace
* Request data where available
* Response data where available
* HTTP status code where applicable
* Test execution metadata
* Historical similar failures

The resulting report should identify:

1. Failure category
2. Likely affected component
3. Evidence supporting the conclusion
4. Similar historical failures
5. Suggested investigation or corrective action

---

# RCA Pipeline Flow

The planned RCA workflow is:

```text
Test Execution
      |
      v
Test Failure
      |
      v
Failure Artifact Collection
      |
      v
Failure Context Extraction
      |
      v
Failure Normalization
      |
      v
Embedding Generation
      |
      v
ChromaDB Similarity Search
      |
      v
Context Assembly
      |
      v
Local LLM via Ollama
      |
      v
RCA Validation
      |
      v
RCA Report
      |
      ├──────────────► CI Artifact
      |
      └──────────────► Failure History
```

---

# RCA Step-by-Step Design

| Step | Component             | Responsibility                                               | Status                     |
| ---: | --------------------- | ------------------------------------------------------------ | -------------------------- |
|    1 | Test Execution        | Execute Pytest/Selenium tests                                | Current / Selenium planned |
|    2 | Failure Capture       | Capture failed test metadata and diagnostics                 | Planned                    |
|    3 | Context Extraction    | Extract relevant failure information                         | Planned                    |
|    4 | Failure Normalization | Convert failure information into a consistent representation | Planned                    |
|    5 | Embedding Generation  | Convert failure context into a vector representation         | Planned                    |
|    6 | ChromaDB Retrieval    | Retrieve similar historical failures                         | Planned                    |
|    7 | Context Assembly      | Combine current and historical failure context               | Planned                    |
|    8 | LLM Analysis          | Generate an evidence-based RCA                               | Planned                    |
|    9 | Output Validation     | Evaluate whether the RCA is supported by available evidence  | Planned                    |
|   10 | Report Generation     | Produce a human-readable RCA report                          | Planned                    |
|   11 | Historical Storage    | Store the failure and RCA for future retrieval               | Planned                    |

---

# Failure Context Model

The RCA pipeline should normalize failures into a structured representation before embedding them.

A conceptual failure record is:

```json
{
  "test_name": "test_capture_exceeds_authorized_amount",
  "test_layer": "api",
  "timestamp": "2026-08-12T07:19:35Z",
  "endpoint": "/api/v1/transactions/{transaction_id}/capture",
  "http_method": "POST",
  "request_payload": {
    "capture_amount": 150
  },
  "response_status": 400,
  "response_body": {},
  "expected": "400",
  "actual": "500",
  "error_message": "AssertionError",
  "stack_trace": "...",
  "environment": "local"
}
```

The exact schema will be finalized when the failure-ingestion implementation is introduced.

The model should remain structured enough to support filtering and metadata-based retrieval while also producing normalized text suitable for embeddings.

---

# Failure Normalization

Raw failure logs often contain information that reduces similarity-search quality, such as:

* UUIDs
* Timestamps
* Random identifiers
* Temporary file paths
* Memory addresses
* Dynamic request identifiers

The future pipeline should normalize these values where appropriate.

For example:

```text
transaction_id=e9fa7848-3e2c-424b-b14d-3001fca837be
```

could be normalized to:

```text
transaction_id=<TRANSACTION_ID>
```

The objective is to preserve the failure pattern while reducing irrelevant differences.

This should be implemented carefully because over-normalization can remove information that is actually useful for diagnosing a failure.

---

# Failure Categories

The initial RCA classifier should use a controlled set of categories.

| Category                 | Example                                           |
| ------------------------ | ------------------------------------------------- |
| Timeout                  | `X-Simulate-Failure: TIMEOUT`                     |
| Network Error            | `X-Simulate-Failure: NETWORK_ERROR`               |
| Invalid Response         | Simulated invalid server response                 |
| Validation Error         | Missing or malformed request data                 |
| Business Rule Violation  | Capture or refund exceeds allowed amount          |
| Invalid State Transition | Settlement attempted before capture               |
| Authorization Decline    | Insufficient funds or inactive card               |
| Assertion Mismatch       | Actual API behavior differs from test expectation |
| Persistence Error        | Database transaction or storage failure           |
| Concurrency Error        | Conflicting simultaneous operations               |
| Environment Issue        | Service unavailable or dependency failure         |
| Unknown                  | Evidence is insufficient to determine the cause   |

The category list should evolve as the project introduces persistence, concurrency, CI/CD, and additional infrastructure.

---

# RCA Prompt Design

The LLM should receive structured evidence rather than an unrestricted raw log dump.

A conceptual prompt structure is:

```text
SYSTEM
You are analyzing an automated payment-system test failure.

Your job is to identify the most likely root cause using only the
evidence provided.

Do not invent missing facts.
Clearly distinguish evidence from inference.
If the evidence is insufficient, classify the failure as UNKNOWN.

CURRENT FAILURE

Test:
{test_name}

Test Layer:
{test_layer}

Endpoint:
{endpoint}

Request:
{request}

Expected:
{expected}

Actual:
{actual}

Error:
{error_message}

Stack Trace:
{stack_trace}

HISTORICAL SIMILAR FAILURES

Failure 1:
{historical_failure_1}

Failure 2:
{historical_failure_2}

Failure 3:
{historical_failure_3}

TASK

Return:

1. Failure category
2. Likely root cause
3. Evidence
4. Similar historical pattern
5. Recommended investigation
6. Confidence level
```

The final implementation may use structured output rather than plain text.

---

# RCA Output Contract

A future RCA result should follow a predictable structure.

Conceptually:

```json
{
  "failure_category": "Assertion Mismatch",
  "root_cause": "The API returned a different status than the test expected.",
  "evidence": [
    "Expected HTTP 409",
    "Received HTTP 200",
    "Transaction was already settled"
  ],
  "historical_matches": [
    "failure-id-001",
    "failure-id-014"
  ],
  "recommended_action": "Verify transaction state validation before settlement.",
  "confidence": 0.91
}
```

The exact schema will be defined when the RCA service is implemented.

---

# RCA Confidence

The AI should not present every conclusion with the same level of certainty.

A future implementation should distinguish between:

```text
High Confidence
    |
    | Strong evidence directly supports the conclusion
    v

Medium Confidence
    |
    | Evidence supports a likely explanation
    v

Low Confidence
    |
    | Multiple explanations remain plausible
    v

Unknown
```

Confidence should be treated as an indicator of evidence strength rather than a guarantee of correctness.

---

# RCA Validation

AI-generated RCA output requires its own validation.

Future validation should check:

### Category Accuracy

Was the failure assigned to the correct category?

### Evidence Consistency

Does the explanation match the actual failure information?

### Unsupported Claims

Did the LLM introduce facts that are not present in the supplied evidence?

### Historical Relevance

Were retrieved failures actually similar to the current failure?

### Actionability

Does the recommended investigation help an engineer determine the next step?

### Reproducibility

Can the explanation be produced consistently for deterministic failures?

---

# Initial RCA Evaluation Target

Once the RCA pipeline is implemented, the project should establish a deterministic evaluation dataset.

The initial target is:

> Correctly classify at least 8 out of 10 known, deterministically injected failure scenarios.

The evaluation dataset should contain known failures such as:

* Simulated timeout
* Simulated network error
* Simulated invalid response
* Validation failure
* Invalid lifecycle state
* Capture amount violation
* Refund amount violation
* Assertion mismatch
* Missing transaction
* Environment failure

The target is an evaluation criterion, not a claim about the current system.

---

# Pipeline 2 — AI Test Case Generator

## Objective

The AI Test Case Generator is intended to identify additional test scenarios that are not already covered by the existing automated test suite.

The generator will analyze:

* FastAPI OpenAPI specification
* Request schemas
* Response schemas
* Validation constraints
* Transaction lifecycle rules
* Existing tests
* Previously generated suggestions

The output will be a reviewable list of candidate scenarios.

---

# Test Generator Flow

```text
FastAPI OpenAPI Specification
              |
              v
       Endpoint Extraction
              |
              v
       Schema Analysis
              |
              v
       Existing Test Analysis
              |
              v
       Coverage Gap Analysis
              |
              v
        LLM Generation
              |
              v
       Deduplication
              |
              v
     Scenario Validation
              |
              v
       Markdown Report
              |
              v
         Human Review
```

---

# Test Generator Step-by-Step Design

| Step | Component              | Responsibility                                         | Status  |
| ---: | ---------------------- | ------------------------------------------------------ | ------- |
|    1 | OpenAPI Retrieval      | Load `/openapi.json`                                   | Planned |
|    2 | Endpoint Parsing       | Extract routes, parameters, schemas, and responses     | Planned |
|    3 | Constraint Extraction  | Identify validation and domain-relevant constraints    | Planned |
|    4 | Existing Test Analysis | Identify already-covered scenarios                     | Planned |
|    5 | Gap Analysis           | Identify potential coverage gaps                       | Planned |
|    6 | LLM Generation         | Generate candidate scenarios                           | Planned |
|    7 | Deduplication          | Remove duplicate or substantially equivalent scenarios | Planned |
|    8 | Scenario Validation    | Verify generated scenarios against the API contract    | Planned |
|    9 | Report Generation      | Produce a reviewable report                            | Planned |
|   10 | History Storage        | Store accepted/rejected suggestions                    | Planned |

---

# Example Test Scenario Categories

The generator should consider multiple classes of test scenarios.

| Category           | Example                                               |
| ------------------ | ----------------------------------------------------- |
| Boundary Value     | Authorization amount exactly equals available balance |
| Lower Boundary     | Minimum permitted transaction amount                  |
| Upper Boundary     | Maximum permitted transaction amount                  |
| Missing Field      | Omit required `merchant_id`                           |
| Invalid Type       | Send a string where a numeric amount is required      |
| Invalid Enum       | Unsupported card network                              |
| Invalid State      | Settlement before capture                             |
| Repeated Operation | Capture the same transaction twice                    |
| Refund Boundary    | Refund exactly the remaining refundable amount        |
| Refund Overflow    | Refund one unit beyond the remaining amount           |
| Resource Error     | Use a nonexistent transaction ID                      |
| Failure Simulation | Execute endpoint with `X-Simulate-Failure`            |
| Concurrency        | Submit two capture requests simultaneously            |
| Idempotency        | Repeat an operation with the same idempotency key     |
| Persistence        | Verify transaction state after application restart    |

Not every category will be applicable to every endpoint.

---

# Existing Test Awareness

The generator should not simply produce generic edge cases.

It should compare generated scenarios against existing tests.

Conceptually:

```text
OpenAPI
   |
   v
Endpoint Rules
   |
   +───────────────+
   |               |
   v               v
Existing Tests   Existing Suggestions
   |               |
   +───────┬───────+
           |
           v
      Coverage Gaps
           |
           v
      LLM Suggestions
```

The generator should prefer scenarios that:

* Exercise an uncovered rule
* Explore an untested boundary
* Validate a meaningful negative path
* Test an important state transition
* Expose a realistic reliability risk

It should avoid producing large numbers of trivial variations merely to inflate the test count.

---

# Test Scenario Output Contract

A future generated scenario should follow a structured format.

Example:

```json
{
  "endpoint": "POST /api/v1/transactions/{transaction_id}/refund",
  "category": "Boundary Value",
  "scenario": "Refund exactly the remaining refundable amount after a partial refund.",
  "preconditions": [
    "Transaction is SETTLED",
    "A previous partial refund has been completed"
  ],
  "request": {
    "refund_amount": 50
  },
  "expected_status": 200,
  "expected_transaction_status": "REFUNDED",
  "reason": "Validates the transition from PARTIALLY_REFUNDED to REFUNDED.",
  "duplicate": false
}
```

The exact schema will be finalized during implementation.

---

# Test Suggestion Validation

Generated scenarios should be validated before being considered useful.

Validation should check:

## API Contract

Does the proposed request match the actual OpenAPI schema?

## Domain Correctness

Does the scenario respect the actual payment lifecycle?

## Existing Coverage

Is the scenario genuinely different from an existing test?

## Expected Behavior

Is the predicted response/status consistent with the current implementation?

## Executability

Can the scenario realistically be implemented as an automated test?

## Value

Does the scenario test meaningful behavior rather than creating an artificial variation?

---

# Initial Test Generation Target

Once implemented, the initial evaluation target is:

> Generate at least 5 relevant, non-duplicate edge-case scenarios per selected endpoint.

Generated scenarios should then be reviewed and classified as:

```text
Generated
    |
    +── Accepted
    |
    +── Modified
    |
    +── Rejected
```

The acceptance rate should be tracked separately from the raw number of generated scenarios.

Generating 100 useless tests is not better than generating 10 useful ones. Humanity has already demonstrated this repeatedly with software requirements documents.

---

# ChromaDB Storage Design

ChromaDB is planned as the vector storage layer for historical AI context.

The initial design contains two collections.

## Collection: `failure_logs`

Stores historical test failures and RCA context.

Potential metadata:

| Metadata           | Purpose                                    |
| ------------------ | ------------------------------------------ |
| `failure_id`       | Unique failure identifier                  |
| `test_name`        | Failed test                                |
| `test_layer`       | API, service, state machine, UI, etc.      |
| `endpoint`         | Related API endpoint                       |
| `failure_category` | Classified failure category                |
| `timestamp`        | Failure occurrence time                    |
| `environment`      | Execution environment                      |
| `git_commit`       | Code version                               |
| `rca_summary`      | Previously generated RCA                   |
| `status_code`      | Relevant HTTP status                       |
| `resolved`         | Whether the failure was confirmed/resolved |

The failure text itself will be embedded for similarity retrieval.

---

## Collection: `test_suggestions_history`

Stores previously generated test scenarios.

Potential metadata:

| Metadata        | Purpose                         |
| --------------- | ------------------------------- |
| `suggestion_id` | Unique suggestion identifier    |
| `endpoint`      | Related endpoint                |
| `category`      | Scenario category               |
| `scenario`      | Generated scenario description  |
| `status`        | Accepted, modified, or rejected |
| `timestamp`     | Generation time                 |
| `source`        | Generator run identifier        |

This collection helps prevent repeated generation of substantially identical suggestions.

---

# Retrieval Strategy

The RCA pipeline should initially retrieve a small number of highly relevant historical failures.

Conceptually:

```text
Current Failure
      |
      v
Embedding
      |
      v
ChromaDB
      |
      v
Top-K Similar Failures
      |
      v
Metadata Filtering
      |
      v
Relevant Context
```

The initial implementation can use a small `k`, such as:

```text
k = 3
```

The exact value should be evaluated empirically.

Retrieval should prioritize semantic similarity while allowing metadata filters such as:

* Test layer
* Endpoint
* Failure category
* Environment
* HTTP status

The system should avoid retrieving unrelated failures merely because they share generic words such as `AssertionError`.

---

# Embedding Strategy

The project intends to use a local embedding model.

Potential implementation options include:

* Ollama-compatible embedding models
* Sentence-transformers
* Another lightweight local embedding model

The final model should be selected based on:

* Local hardware requirements
* Embedding quality
* Inference speed
* Reproducibility
* Ease of local setup
* Compatibility with ChromaDB

The embedding model is an implementation decision that should not be considered finalized until the AI pipeline is built and evaluated.

---

# Local LLM Configuration

The planned runtime is:

| Setting         | Planned Value                                  |
| --------------- | ---------------------------------------------- |
| Runtime         | Ollama                                         |
| Model           | Local model appropriate for available hardware |
| Embedding Model | Lightweight local embedding model              |
| Temperature     | Approximately 0.2–0.3                          |
| Vector Store    | ChromaDB                                       |

Potential local LLM candidates include:

* Llama-family models
* Phi-family models
* Other models that provide acceptable local inference performance

The exact model should be selected through evaluation rather than permanently hard-coded into the architecture document.

---

# Prompt Engineering Principles

The AI prompts should follow several rules.

## Evidence First

The model should receive the relevant evidence before being asked for a conclusion.

## No Fabrication

The model should explicitly state when the evidence is insufficient.

## Structured Output

Responses should follow a predictable schema to make validation and reporting easier.

## Low Creativity

RCA and test generation are analytical tasks.

The system should use a relatively low temperature rather than encouraging creative output.

## Explicit Constraints

The prompts should tell the model:

* What information it can use
* What it must not assume
* What format it must return
* How to handle uncertainty

---

# AI Safety and Trust Boundaries

The AI engine should not have unrestricted authority over the project.

The initial architecture should enforce these boundaries:

```text
                    AI Engine
                        |
          ┌─────────────┴─────────────┐
          |                           |
          v                           v
      Read Data                  Generate Output
          |                           |
          v                           v
   Logs / OpenAPI             Reports / Suggestions
                                      |
                                      v
                                Human Review
```

The AI should not directly:

* Modify source code
* Modify database records
* Change transaction state
* Suppress automated tests
* Approve deployments
* Merge pull requests
* Alter CI results

Any future automation beyond reporting should be explicitly designed and validated before being enabled.

---

# CI/CD Integration

The AI pipelines are intended to integrate with GitHub Actions after the CI/CD foundation is implemented.

## Planned RCA Workflow

```text
Pull Request / Commit
        |
        v
Automated Tests
        |
   ┌────┴────┐
   |         |
 PASS      FAIL
   |         |
   v         v
Continue   Failure Artifacts
             |
             v
          RCA Job
             |
             v
        ChromaDB Retrieval
             |
             v
          Ollama LLM
             |
             v
         RCA Report
             |
             v
       CI Artifact
```

The RCA job should run only when useful failure artifacts are available.

---

# Test Generator CI Workflow

The test generator does not need to run for every commit.

The planned execution modes are:

* Manual GitHub Actions workflow
* Scheduled workflow
* Local developer execution

Conceptually:

```text
Manual / Scheduled Trigger
          |
          v
   Running API Gateway
          |
          v
     OpenAPI Spec
          |
          v
   Existing Test Analysis
          |
          v
      LLM Generator
          |
          v
   Deduplication / Validation
          |
          v
 test_suggestions.md
          |
          v
      Human Review
```

The generator should not automatically add generated tests to the repository during the initial implementation.

---

# AI Reports

## RCA Report

A future RCA report should contain:

```text
# Root Cause Analysis

## Test
<test name>

## Failure Category
<category>

## Summary
<root cause summary>

## Evidence
- <evidence 1>
- <evidence 2>

## Historical Matches
- <failure 1>
- <failure 2>

## Recommended Investigation
<recommended action>

## Confidence
<confidence>
```

The report should make it possible for a developer or QA engineer to independently verify the AI's reasoning.

---

## Test Suggestion Report

A future test suggestion report should contain:

```text
# AI Test Suggestions

## Endpoint
POST /api/v1/transactions/{transaction_id}/refund

### Suggestion

Category:
Boundary Value

Scenario:
Refund exactly the remaining refundable amount.

Expected Result:
HTTP 200
Transaction status = REFUNDED

Reason:
Validates the final transition from PARTIALLY_REFUNDED to REFUNDED.

Status:
Pending Review
```

The report should distinguish generated suggestions from accepted tests.

---

# Data Retention and Privacy

The AI pipeline will process test failures and payment-domain data.

The system must therefore ensure that AI storage contains only non-production test information.

The project should never send real payment credentials or production cardholder information into the AI pipeline.

The AI environment should use:

* Synthetic card data
* Synthetic transaction data
* Non-production merchant identifiers
* Sanitized request/response payloads
* Sanitized stack traces

Sensitive values should be redacted before persistence or embedding.

---

# AI Observability

When the AI pipeline is implemented, the system should capture enough information to understand AI behavior.

Potential telemetry includes:

* Pipeline execution time
* Embedding generation time
* Retrieval latency
* Number of retrieved documents
* LLM inference latency
* Token usage where available
* Model identifier
* Prompt version
* Output validation status
* Human acceptance/rejection of suggestions

OpenTelemetry is planned for broader application and AI observability.

---

# Failure Feedback Loop

The RCA pipeline is designed to improve through accumulated historical data.

```text
Test Failure
     |
     v
RCA
     |
     v
Human Review
     |
     v
Confirmed Root Cause
     |
     v
Historical Failure Store
     |
     v
Future Similar Failure
     |
     v
Better Retrieval Context
```

The same principle applies to test generation:

```text
Generated Suggestion
        |
        v
Human Review
        |
   ┌────┴────┐
   v         v
Accepted   Rejected
   |         |
   └────┬────┘
        v
Suggestion History
        |
        v
Future Deduplication
```

This creates a feedback mechanism without giving the AI unrestricted authority over the codebase.

---

# Implementation Dependencies

The AI layer depends on several capabilities that are not currently implemented.

| Dependency                       | Required For                 | Status      |
| -------------------------------- | ---------------------------- | ----------- |
| Reliable payment domain          | Meaningful failure analysis  | Implemented |
| Automated regression suite       | Failure source               | Implemented |
| Deterministic failure simulation | RCA evaluation               | Implemented |
| Transaction history              | Payment lifecycle context    | Implemented |
| Persistent storage               | Durable AI context           | Planned     |
| Failure artifact collection      | RCA input                    | Planned     |
| ChromaDB                         | Historical retrieval         | Planned     |
| Embedding model                  | Semantic retrieval           | Planned     |
| Ollama                           | Local LLM execution          | Planned     |
| LLM                              | RCA and generation           | Planned     |
| GitHub Actions                   | Automated AI execution       | Planned     |
| OpenTelemetry                    | AI/application observability | Planned     |

The AI implementation should therefore follow the project's incremental architecture rather than being introduced before the required foundation exists.

---

# Recommended Implementation Order

The AI layer should be implemented in the following order:

```text
1. Payment Reliability Foundation
          |
          v
2. Persistent Storage
          |
          v
3. Structured Logging
          |
          v
4. Failure Artifact Collection
          |
          v
5. Failure Normalization
          |
          v
6. Embedding Pipeline
          |
          v
7. ChromaDB Retrieval
          |
          v
8. Ollama Integration
          |
          v
9. RCA Generation
          |
          v
10. RCA Evaluation
          |
          v
11. OpenAPI Test Generator
          |
          v
12. Suggestion Validation
          |
          v
13. CI/CD Integration
```

This ordering prevents the AI layer from becoming a substitute for missing reliability, persistence, or observability infrastructure.

---

# Current vs Planned AI Stack

| Component                  | Current Status | Planned Role                                |
| -------------------------- | -------------- | ------------------------------------------- |
| Pytest                     | Implemented    | Source of automated test failures           |
| Selenium                   | Planned        | Future UI failure source                    |
| Structured Failure Records | Planned        | Standard RCA input                          |
| Embeddings                 | Planned        | Semantic failure representation             |
| ChromaDB                   | Planned        | Historical failure and suggestion retrieval |
| Ollama                     | Planned        | Local LLM runtime                           |
| Local LLM                  | Planned        | RCA and test-scenario generation            |
| LangChain                  | Planned        | LLM/RAG orchestration                       |
| LangGraph                  | Planned        | Multi-step AI workflow orchestration        |
| OpenTelemetry              | Planned        | AI and application observability            |
| GitHub Actions             | Planned        | Automated AI workflow execution             |

---

# Success Criteria

The AI layer should be considered successful only if it provides measurable value over the existing deterministic testing process.

## RCA Success Criteria

The initial evaluation should measure:

* Failure-category accuracy
* Root-cause accuracy
* Evidence consistency
* Historical retrieval relevance
* Unsupported-claim rate
* Human acceptance rate
* Time saved during failure investigation

Initial classification target:

> At least 8 out of 10 known deterministic failure scenarios correctly classified.

---

## Test Generator Success Criteria

The initial evaluation should measure:

* Number of useful scenarios
* Duplicate rate
* Domain correctness
* API-contract correctness
* Boundary coverage
* Negative-case coverage
* Human acceptance rate
* Number of generated scenarios eventually converted into automated tests

Initial generation target:

> At least 5 relevant, non-duplicate edge-case scenarios per selected endpoint.

These targets should be revised after a representative evaluation dataset exists.

---

# Current Limitations

The planned AI architecture has several limitations.

### Local Model Quality

Small local models may produce less accurate or less detailed results than larger hosted models.

### Retrieval Quality

Poor embeddings or irrelevant historical data can result in misleading context.

### Hallucination

An LLM may generate plausible explanations that are not supported by the actual failure.

### Test Generation Accuracy

A generated scenario may appear reasonable while contradicting the actual payment-domain implementation.

### Evaluation Difficulty

RCA quality is not fully captured by a simple exact-match metric.

### Historical Data Dependency

The RCA system becomes more useful as high-quality historical failure data accumulates.

### Infrastructure Complexity

ChromaDB, Ollama, embeddings, observability, and CI integration introduce additional operational complexity.

These limitations are why the AI layer is intentionally positioned after the payment reliability foundation.

---

# Architectural Boundary

The final intended boundary is:

```text
┌─────────────────────────────────────────┐
│         Deterministic System            │
│                                         │
│ FastAPI                                 │
│ Payment Service                         │
│ State Machine                           │
│ Repository                              │
│ PostgreSQL                              │
│ Pytest                                  │
└────────────────────┬────────────────────┘
                     |
                     | Test Results / API Spec
                     v
┌─────────────────────────────────────────┐
│              AI Layer                   │
│                                         │
│ Failure Context Extraction              │
│ Embeddings                              │
│ ChromaDB                                │
│ Ollama                                  │
│ RCA                                     │
│ Test Generation                         │
└────────────────────┬────────────────────┘
                     |
                     v
┌─────────────────────────────────────────┐
│             Human Review                │
│                                         │
│ Validate RCA                            │
│ Review Test Suggestions                 │
│ Decide Corrective Action                │
└─────────────────────────────────────────┘
```

The deterministic payment system remains the source of truth.

The AI layer exists to make the testing process more intelligent, explainable, and efficient.

---

# Current AI Pipeline Status

### Completed Foundation

* [x] Mock Payment Gateway
* [x] Payment transaction lifecycle
* [x] State machine
* [x] Payment service layer
* [x] Repository abstraction
* [x] Transaction history
* [x] Automated API tests
* [x] Automated service tests
* [x] Automated state-machine tests
* [x] Deterministic failure simulation

### Planned

* [ ] Structured failure artifact collection
* [ ] Failure normalization
* [ ] Local embedding pipeline
* [ ] ChromaDB integration
* [ ] Ollama integration
* [ ] RCA pipeline
* [ ] RCA evaluation dataset
* [ ] RCA report generation
* [ ] OpenAPI test-case generator
* [ ] Existing-test coverage analysis
* [ ] Test suggestion deduplication
* [ ] Test suggestion validation
* [ ] Human feedback tracking
* [ ] AI observability
* [ ] GitHub Actions AI workflow
* [ ] Historical failure feedback loop

---

# Final Architecture Principle

PayGuard AI is not intended to become an LLM that happens to run some tests.

The intended architecture is:

```text
Reliable Payment System
          |
          v
Reliable Automated Tests
          |
          v
High-Quality Failure Data
          |
          v
Retrieval + Local AI
          |
          v
Evidence-Based Analysis
          |
          v
Human Validation
```

The AI layer should make an already reliable QA system more capable of understanding failures and discovering meaningful test scenarios.

It should not be used to hide unreliable engineering underneath a layer of impressive-looking AI output. That would be the software equivalent of putting a spoiler on a car with no engine.
