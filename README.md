# PayGuard AI

**AI-Augmented Test Automation Framework for Payment Systems**

PayGuard AI is a portfolio project combining payment domain test automation with applied AI. It simulates a payment gateway (card issuance, authorization, capture, settlement, refund), tests it end-to-end using Pytest (API) and Selenium (UI), and layers in AI-driven root cause analysis and test case generation using LangChain, ChromaDB, and a local LLM (Ollama).

## Why This Project Exists

Traditional QA automation validates that systems work. PayGuard AI goes further — when tests fail, an AI pipeline automatically analyzes logs and suggests root causes, and when new endpoints are added, AI suggests edge-case test scenarios that might otherwise be missed.

## Core Components

| Component | Description |
|---|---|
| Mock Payment Gateway | FastAPI service simulating VISA/Mastercard-style payment flows |
| Web Dashboard | Simple UI displaying transaction status, used as the Selenium test target |
| API Test Suite | Pytest tests covering positive, negative, and boundary conditions |
| UI Test Suite | Selenium tests validating dashboard behavior |
| AI RCA Engine | LangChain + ChromaDB + Ollama pipeline that summarizes root causes of test failures |
| AI Test Case Generator | LLM-based suggestions for additional test scenarios based on the API spec |
| CI/CD Pipeline | GitHub Actions running tests automatically and triggering RCA on failure |
| Containerization | Docker Compose orchestrating all services |

## Tech Stack

Python · FastAPI · Pytest · Selenium · LangChain · ChromaDB · Ollama · Docker · GitHub Actions

## Project Status

Currently in early development. See `docs/PRD.md` for full scope and goals, and `docs/ARCHITECTURE.md` (coming soon) for system design details.

## Documentation

| Document | Purpose |
|---|---|
| `docs/PRD.md` | Product requirements, scope, and success criteria |
| `docs/ARCHITECTURE.md` | System design and component interactions |
| `docs/TEST_STRATEGY.md` | Test pyramid, coverage goals, AI-augmentation points |
| `docs/TECH_STACK.md` | Tools used and justification |
| `docs/API_SPEC.md` | Mock payment gateway endpoint definitions |
| `docs/AI_PIPELINE.md` | RCA and test-generation pipeline design |
| `docs/SETUP.md` | Local setup instructions |

## Author

Atharva Garud — Associate Engineer @ Worldline, ISTQB Certified, building at the intersection of quality engineering and applied AI.