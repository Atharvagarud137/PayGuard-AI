# TECH_STACK.md — PayGuard AI

## Purpose

This document lists every technology used in PayGuard AI along with the reasoning behind each choice, so the stack decisions are clear for anyone reviewing the project — including you, when explaining design choices in interviews.

## Backend / System Under Test

| Technology | Purpose | Why Chosen |
|---|---|---|
| Python 3.12 | Core language | Mature ecosystem for both test automation and AI tooling; matches your existing skill set |
| FastAPI | Mock Payment Gateway framework | Auto-generates OpenAPI spec (needed for the AI Test Case Generator), async support, fast to build with, widely used in modern backend systems |
| Pydantic | Data validation | Built into FastAPI; enforces strict schema validation for payment payloads, mirroring real-world payment API rigor |
| Uvicorn | ASGI server | Standard lightweight server for running FastAPI apps |

## Frontend / Dashboard

| Technology | Purpose | Why Chosen |
|---|---|---|
| HTML/JS (or lightweight framework, TBD) | Web Dashboard | Kept intentionally simple since its primary role is to serve as a realistic Selenium test target, not a production UI |

## Test Automation

| Technology | Purpose | Why Chosen |
|---|---|---|
| Pytest | Unit and API testing framework | Industry standard, matches your existing testing background, integrates cleanly with CI |
| HTTPX | HTTP client for API tests | Async-compatible, works well with FastAPI's async endpoints |
| Selenium | UI test automation | Widely used in enterprise QA (matches your Worldline experience), demonstrates browser automation skills |

## AI Engine

| Technology | Purpose | Why Chosen |
|---|---|---|
| LangChain | Orchestration framework for LLM pipelines | Directly reused from your existing AI Incident Intelligence Platform experience; strong ecosystem for RAG pipelines |
| ChromaDB | Vector database for failure log embeddings | Lightweight, easy to run locally, already proven in your prior project |
| Ollama | Local LLM inference server | Enables fully offline AI features with no API costs, ideal for live demos without internet dependency |

## Containerization and Orchestration

| Technology | Purpose | Why Chosen |
|---|---|---|
| Docker | Containerizing each service | Ensures consistent environments across development and CI, industry-standard practice |
| Docker Compose | Multi-service orchestration | Simplifies running the gateway, dashboard, ChromaDB, and Ollama together with a single command |

## CI/CD

| Technology | Purpose | Why Chosen |
|---|---|---|
| GitHub Actions | Continuous integration pipeline | Free for public repos, integrates natively with GitHub, supports scheduled runs and service containers needed for ChromaDB/Ollama in CI |

## Development Environment

| Tool | Purpose |
|---|---|
| IntelliJ IDEA | Primary IDE for writing and running code |
| Git | Version control |
| Python venv | Dependency isolation |

## Summary Rationale

The stack was chosen to directly showcase two intersecting skill sets: enterprise-grade payment system test automation (Pytest, Selenium, FastAPI) and applied generative AI engineering (LangChain, ChromaDB, Ollama). Every tool either mirrors your existing professional experience at Worldline or extends your prior AI Incident Intelligence Platform work, making the project a coherent demonstration of both domains rather than two disconnected skill showcases.