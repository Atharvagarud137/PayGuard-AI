# PRD.md — PayGuard AI

## Problem Statement

Payment system testing today relies heavily on manual test case design and slow root cause analysis when tests fail. QA engineers spend significant time investigating why automated tests break, and test coverage often lags behind evolving payment flows. PayGuard AI addresses this by combining traditional test automation with AI-driven root cause analysis and test case generation, specifically modeled around payment gateway workflows.

## Goals

| Goal | Description |
|---|---|
| Demonstrate automation expertise | Build a robust API and UI test suite covering realistic payment flows |
| Demonstrate applied AI expertise | Use LangChain, ChromaDB, and a local LLM to automate RCA and test case suggestions |
| Create a portfolio-ready artifact | Fully documented, containerized, and CI/CD-integrated project suitable for technical interviews |

## Target User (Persona)

Since this is a portfolio project, the primary "user" is a **recruiter or technical interviewer** evaluating hands-on skill in test automation and applied AI. The secondary persona is **you**, using this project as a live demo during interviews.

## Scope

### In Scope

| Feature | Description |
|---|---|
| Mock Payment Gateway API | FastAPI service simulating card issuance, authorization, capture, settlement, and refund |
| Web Dashboard | Simple UI showing transaction status, used as Selenium's test target |
| API Test Suite | Pytest-based tests covering positive, negative, and boundary conditions |
| UI Test Suite | Selenium tests validating dashboard behavior |
| AI RCA Engine | LangChain + ChromaDB + local LLM (Ollama) pipeline that analyzes failed test logs and generates root cause summaries |
| AI Test Case Generator | LLM-based suggestion engine that reads the API spec and proposes additional edge-case tests |
| CI/CD Pipeline | GitHub Actions running tests on push, triggering RCA on failure |
| Containerization | Docker Compose orchestrating the API, dashboard, and AI services |

### Out of Scope

| Item | Reason |
|---|---|
| Real payment network integration (actual VISA/Mastercard APIs) | Not feasible or necessary for a demo project; mock flows are sufficient |
| User authentication/authorization system | Adds complexity without contributing to the core skill showcase |
| Production-grade security hardening (e.g., real PCI-DSS certification) | Out of scope for a portfolio project, though PCI-DSS *principles* will be reflected in test design |
| Multi-language support | English-only for simplicity |

## Success Criteria

| Metric | Target |
|---|---|
| API test coverage | 90%+ of payment flow endpoints |
| UI test coverage | Core dashboard interactions (view transaction, filter by status, view details) |
| AI RCA accuracy | Correctly identifies root cause category (e.g., timeout, validation error, network decline) in test failure summaries |
| AI test case generation | Produces at least 5 relevant edge-case suggestions per API endpoint |
| CI/CD | All tests run automatically on push; failures trigger AI RCA output in pipeline logs |
| Documentation | Complete PRD, Architecture, Test Strategy, and Setup docs, written clearly enough for a new developer to onboard in under 30 minutes |

## High-Level Feature List by Phase

| Phase | Deliverable |
|---|---|
| Phase 1 | Mock Payment Gateway API |
| Phase 2 | API + UI Test Automation Suite |
| Phase 3 | AI RCA Layer |
| Phase 4 | AI Test Case Generator |
| Phase 5 | Docker Compose + CI/CD Integration |

## Assumptions

- Local LLM (Ollama) will be used for all AI features to avoid API costs and keep the project fully offline-capable.
- The project will run entirely on your local machine and OneDrive-synced directory, with mitigations in place for sync-related file lock issues.
- IntelliJ IDEA (Ultimate or Community with Python support) will be the primary development environment.