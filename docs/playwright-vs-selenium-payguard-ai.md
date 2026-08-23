# Playwright vs Selenium for PayGuard-AI

**Date:** 22 August 2026  
**Project:** PayGuard-AI Mock Payment Gateway  
**Primary test stack:** Python 3.11.9 + pytest  
**Current regression baseline:** 92 tests passing

## Executive Summary

For PayGuard-AI, **Playwright is the stronger choice for browser-based end-to-end/UI automation**.

This is not because Selenium is obsolete. Selenium remains an excellent, mature, standards-oriented browser automation platform, particularly where WebDriver compatibility, broad language support, enterprise Grid infrastructure, or an existing Selenium estate are major requirements.

PayGuard-AI has different priorities:

- Python + pytest is already the core test stack.
- The project has a modern React dashboard.
- Payment workflows require reliable synchronization and test isolation.
- Failure diagnosis matters for a QA/AI-oriented project.
- CI/CD and parallel execution are expected.
- API and UI testing should coexist without duplicating the whole test architecture.
- The project has enough bandwidth to choose the better fit rather than preserve an existing Selenium investment.

### Recommendation

**Adopt Playwright for the browser/E2E layer while retaining the existing pytest API and unit tests.**

Do not replace the existing FastAPI/TestClient tests with browser tests. That would make the suite slower and less precise.

Recommended testing pyramid:

```text
                    Playwright E2E/UI
                 Critical user journeys
                           |
                    API / Integration
                    Existing pytest
                           |
                       Unit Tests
                  Domain / service logic
```

---

## 1. Project Context

PayGuard-AI is a Python/FastAPI mock payment gateway with a layered architecture and a React dashboard.

The backend currently covers:

- Card issuance
- Authorization
- Authorization idempotency
- Capture
- Capture idempotency
- Settlement
- Refunds
- Transaction state transitions
- Decimal-safe money handling
- Audit event creation and persistence
- Transaction and correlation-based audit queries
- Simulated technical failures
- Sensitive-data protections

The current regression suite contains **92 passing tests**.

Browser automation should therefore validate the actual user-facing workflows and UI-to-API integration rather than duplicate backend behavior already covered by API and unit tests.

---

## 2. Evaluation Criteria

This comparison evaluates:

1. Ease of setup
2. Python and pytest integration
3. Language support
4. Browser and platform support
5. Reliability and flakiness
6. Synchronization and waiting
7. Performance
8. Parallel execution
9. Debugging
10. Network/API capabilities
11. Browser isolation
12. CI/CD
13. Community and ecosystem
14. Architecture and maintainability
15. Learning curve
16. Long-term project fit
17. Payment-domain security considerations

---

## 3. High-Level Comparison

| Area | Playwright | Selenium | PayGuard-AI fit |
|---|---|---|---|
| Initial Python setup | Very easy | Easy | Playwright |
| pytest integration | Excellent, official plugin | Good | Playwright |
| Reliability | Strong built-in waiting | Strong with explicit synchronization | Playwright |
| Locator ergonomics | Excellent | Mature | Playwright |
| Test isolation | Strong BrowserContext model | Requires deliberate session design | Playwright |
| Debugging | Inspector + tracing + artifacts | Strong, often assembled from tools | Playwright |
| API testing | Built-in APIRequestContext | Usually external HTTP tooling | Playwright |
| Parallel execution | pytest-xdist | Excellent Grid support | Depends on scale |
| Distributed execution | Good | Excellent | Selenium |
| Cross-browser | Chromium, Firefox, WebKit | Broad WebDriver ecosystem | Depends |
| Language breadth | Python, JS/TS, Java, .NET | Very broad | Selenium |
| Enterprise legacy ecosystem | Good | Excellent | Selenium |
| Modern React UI | Excellent | Excellent | Playwright |
| Payment workflow E2E | Excellent | Excellent | Playwright |
| Project alignment | Excellent | Good | Playwright |

---

## 4. Setup and Ease of Use

### Playwright

Python setup is straightforward:

```powershell
pip install pytest-playwright
playwright install
```

The official Python documentation recommends the pytest plugin for end-to-end testing. It provides browser, context, and page fixtures and supports multiple browser configurations.

Playwright manages its browser binaries, reducing driver-management work.

For this repository, the setup path becomes:

```text
clone
  -> create venv
  -> install requirements
  -> playwright install
  -> pytest
```

### Selenium

Modern Selenium is much easier than historical Selenium setups because Selenium Manager can automatically manage drivers when needed.

However, Selenium still exposes more of the WebDriver/session model, and remote execution introduces additional infrastructure when Grid is used.

### Verdict

**Playwright wins for this project.**

Selenium setup is no longer difficult, but Playwright has fewer moving parts for a new Python/pytest contributor.

---

## 5. Language and Platform Support

### Playwright

Playwright officially supports:

- Python
- JavaScript/TypeScript
- Java
- .NET

Python has synchronous and asynchronous APIs, with pytest as the recommended E2E integration.

Playwright supports Chromium, Firefox, WebKit, and branded Chromium browsers such as Chrome and Edge.

### Selenium

Selenium has a broader language ecosystem, including:

- Python
- Java
- C#
- Ruby
- JavaScript
- Kotlin through Java bindings

Selenium is built around the W3C WebDriver standard and has extensive browser/vendor support.

### Verdict

**Selenium wins ecosystem breadth. Playwright wins project alignment.**

PayGuard-AI is already Python + pytest, so Selenium's extra language breadth provides little immediate benefit.

---

## 6. Test Reliability and Flakiness

This is one of the most important categories for PayGuard-AI.

Payment workflows contain state transitions such as:

```text
AUTHORIZED
    -> CAPTURED
    -> SETTLED
    -> PARTIALLY_REFUNDED
    -> REFUNDED
```

A UI test that clicks Capture before the dashboard is ready can produce a misleading failure.

### Playwright

Playwright performs actionability checks before interactions. For example, a click waits for the target to be resolved, visible, stable, able to receive events, and enabled.

Playwright also provides web-first assertions that wait for expected UI state.

This is particularly useful for a React dashboard with asynchronous state updates.

### Selenium

Selenium can be highly reliable, but synchronization is more explicit.

It provides:

- Implicit waits
- Explicit waits
- Fluent waits
- Expected conditions

Selenium documentation also warns against mixing implicit and explicit waits because this can produce unpredictable timing.

### Verdict

**Playwright has the advantage for PayGuard-AI.**

The framework reduces the amount of custom synchronization code that the team must maintain.

---

## 7. Performance

There is no responsible universal claim that one framework is always faster.

Actual performance depends on:

- Browser startup
- Application response time
- Number of tests
- Test isolation
- Network activity
- Parallel workers
- CI hardware
- Artifact collection

Playwright's BrowserContext model allows isolated sessions without requiring a completely separate browser process for every test.

Selenium's WebDriver architecture is intentionally standardized and remains highly effective.

For PayGuard-AI, architecture matters more than theoretical single-test speed.

### Verdict

Choose Playwright for its overall execution model and reliability, not because of an arbitrary benchmark percentage.

---

## 8. Parallel Execution

### Playwright

Playwright's Python pytest integration works naturally with `pytest-xdist`:

```powershell
pytest --numprocesses auto
```

Its isolated browser contexts also fit independent payment test data well.

### Selenium

Selenium's major advantage is Selenium Grid, which is designed to distribute WebDriver sessions across multiple machines and browsers.

That becomes especially valuable at very large scale.

### PayGuard-AI

The current project does not justify building Grid infrastructure simply to run browser tests.

A pytest-xdist + Playwright approach is simpler.

### Verdict

**Playwright for current project simplicity. Selenium for very large distributed WebDriver infrastructure.**

---

## 9. Debugging and Failure Analysis

This category strongly favors Playwright.

### Playwright Inspector

Playwright Inspector can:

- Step through actions
- Inspect locators
- Highlight elements
- Help diagnose locator failures

PowerShell:

```powershell
$env:PWDEBUG=1
pytest -s
```

### Trace Viewer

Playwright can retain detailed traces for failed tests.

A useful CI setting is:

```text
--tracing=retain-on-failure
```

Screenshots and video can also be retained only on failures.

This gives a useful CI artifact pipeline:

```text
test failure
    -> screenshot
    -> trace
    -> optional video
    -> failure diagnosis
```

### Selenium

Selenium has strong debugging options through browser developer tools, WebDriver logs, screenshots, Grid observability, IDE debugging, and third-party reporting systems.

However, the experience is generally more assembled from separate components.

### Verdict

**Playwright wins.**

For a QA-oriented project, built-in trace evidence can significantly reduce the time spent reproducing failures.

---

## 10. Locators and UI Maintainability

### Playwright

Playwright provides semantic locator APIs such as:

```python
page.get_by_role(...)
page.get_by_label(...)
page.get_by_text(...)
page.get_by_test_id(...)
```

Example:

```python
page.get_by_role("button", name="Capture").click()
```

This is preferable to brittle DOM-position selectors.

### Selenium

Selenium provides mature locators including:

- ID
- Name
- CSS
- XPath
- Class name
- Tag name
- Link text

Selenium itself is not difficult to maintain. Poor locator strategy is the actual problem.

### Recommendation

For PayGuard-AI:

1. Prefer accessible roles and labels.
2. Use stable `data-testid` attributes for complex components.
3. Avoid XPath unless necessary.
4. Never locate elements by visual position.
5. Keep locators inside page/component objects.

### Verdict

**Playwright has the better ergonomics.**

---

## 11. Browser Isolation and Payment Test Data

Payment tests should not accidentally inherit:

- Authentication state
- Cookies
- Local storage
- Previous transaction state
- Previous dashboard state

Playwright's BrowserContext model maps naturally to independent payment tests:

```text
Test A -> Context A -> Card A -> Transaction A
Test B -> Context B -> Card B -> Transaction B
```

Selenium can provide equivalent isolation, but session lifecycle must be managed deliberately.

### Verdict

**Playwright is the better ergonomic fit.**

---

## 12. API and Hybrid Testing

Playwright can send HTTP requests through `APIRequestContext`.

This makes hybrid tests possible:

```text
API: create card
  ->
API: authorize payment
  ->
UI: open dashboard
  ->
UI: verify transaction
  ->
UI: capture payment
  ->
API: verify state
```

This avoids using the UI to prepare every prerequisite.

The existing FastAPI/TestClient suite should remain because it is faster and more focused.

### Verdict

**Playwright is particularly strong for PayGuard-AI's API + UI testing model.**

---

## 13. CI/CD Integration

Playwright has official CI guidance for GitHub Actions and container-based execution.

A future pipeline can follow:

```text
Checkout
  ->
Install Python dependencies
  ->
Install Playwright browsers
  ->
Start application
  ->
Run pytest
  ->
Upload failure artifacts
```

Example:

```powershell
python -m playwright install --with-deps
pytest --tracing=retain-on-failure
```

Selenium also integrates very well with CI/CD, especially where Selenium Grid or remote browser infrastructure already exists.

### Verdict

**Both are strong. Playwright is simpler for this repository.**

---

## 14. Community and Ecosystem

### Selenium strengths

- Very long industry history
- W3C WebDriver standard
- Mature Selenium Grid
- Broad enterprise adoption
- Extensive third-party integrations
- Large pool of experienced engineers
- Very broad language support

### Playwright strengths

- Strong modern browser automation ecosystem
- Excellent documentation
- Strong Python/pytest integration
- Modern debugging tooling
- Strong TypeScript/JavaScript ecosystem
- Good fit for modern web applications

### Verdict

**Selenium wins breadth and longevity. Playwright wins modern E2E developer experience.**

---

## 15. Maintenance Considerations

### Playwright advantages

- Less custom synchronization
- Strong locators
- Browser contexts
- Built-in tracing
- Integrated browser management
- Strong pytest fixtures
- Good isolation
- API testing support

### Playwright disadvantages

- Browser binaries add installation/storage considerations.
- Browser versions should remain aligned with the dependency.
- Teams experienced only with WebDriver need to learn a different model.
- Some enterprise environments are already standardized around Selenium.

### Selenium advantages

- W3C WebDriver standard
- Very mature architecture
- Broad browser and language support
- Strong remote execution
- Large existing knowledge base
- Large ecosystem

### Selenium disadvantages

- More synchronization responsibility
- More infrastructure decisions
- Greater opportunity for poor wait strategies
- Grid can be unnecessary overhead for a small project
- Debugging often requires more external tooling

---

## 16. Recommended Architecture

Do not create a second testing architecture merely because a browser framework is being introduced.

Recommended structure:

```text
tests/
├── api/
│   ├── test_authorization.py
│   ├── test_capture.py
│   ├── test_settlement.py
│   ├── test_refund.py
│   ├── test_audit.py
│   └── ...
│
├── unit/
│   ├── test_money.py
│   ├── test_state_machine.py
│   ├── test_payment_service.py
│   ├── test_audit_service.py
│   └── ...
│
└── e2e/
    ├── conftest.py
    ├── pages/
    │   ├── dashboard_page.py
    │   ├── transaction_page.py
    │   └── card_page.py
    ├── components/
    │   ├── transaction_table.py
    │   └── status_badge.py
    ├── test_authorization_flow.py
    ├── test_capture_flow.py
    ├── test_settlement_flow.py
    ├── test_refund_flow.py
    └── test_audit_visibility.py
```

---

## 17. Recommended Playwright Adoption Plan

### Phase 1: Infrastructure

Add:

```text
pytest-playwright
playwright
pytest-xdist
```

Install the required browsers and create dedicated E2E configuration.

### Phase 2: Fixtures

Create fixtures for:

- Application base URL
- API setup
- Browser context
- Test card
- Authorized transaction
- Captured transaction
- Settled transaction

Each test should receive independent payment data.

### Phase 3: Page and Component Objects

Create:

```text
DashboardPage
TransactionPage
CardPage
AuditPage
```

and reusable components such as:

```text
TransactionTable
StatusBadge
TransactionDetails
```

Tests should express business behavior rather than DOM mechanics.

### Phase 4: First Workflows

Start with:

1. Authorization
2. Capture
3. Refund

Then expand to:

4. Settlement
5. Audit visibility
6. Failure scenarios
7. Idempotency UI behavior
8. Dashboard filtering/search

### Phase 5: CI

Add Playwright E2E tests to GitHub Actions and retain failure artifacts.

Only after the E2E suite is stable should the project expand its browser matrix.

---

## 18. Example Test Style

A future Playwright test should read approximately like:

```python
def test_capture_authorized_transaction(
    page,
    authorized_transaction,
):
    dashboard = DashboardPage(page)

    dashboard.open_transactions()

    transaction = dashboard.transaction(
        authorized_transaction["transaction_id"]
    )

    transaction.capture(amount="1000")

    transaction.expect_status("CAPTURED")
    transaction.expect_captured_amount("1000")
```

The page/component layer should contain locator and interaction details.

---

## 19. What Should NOT Be Rewritten

The existing 92-test regression baseline should be preserved.

Do not rewrite these as browser tests:

```text
test_money.py
test_state_machine.py
test_payment_service.py
```

These belong at the unit/service layer.

Do not rewrite the entire API suite as UI tests.

For example:

```text
POST /authorize
-> assert HTTP 200
-> assert transaction state
```

is correctly tested through an API test.

A browser test should validate something like:

```text
Open dashboard
-> Find transaction
-> Click Capture
-> UI shows CAPTURED
-> Captured amount is displayed
```

This prevents the E2E suite from becoming an expensive duplicate of backend testing.

---

## 20. When Selenium Would Be Better

Selenium becomes the better choice if the project develops requirements such as:

### Broad enterprise language support

Automation must be maintained across Java, C#, Python, and JavaScript teams.

### Existing Selenium infrastructure

The organization already has:

- Selenium Grid
- Grid-compatible reporting
- Selenium cloud providers
- Existing page-object libraries
- Large Selenium expertise

### Large distributed browser farms

Thousands of tests must run across many machines and browser/OS combinations.

### WebDriver-standard requirements

The organization specifically requires standards-based WebDriver automation.

None of these requirements currently outweigh Playwright for PayGuard-AI.

---

## 21. Final Decision

### Recommended tool: Playwright

**Decision confidence: High**

| Requirement | Weight | Playwright | Selenium |
|---|---:|---:|---:|
| Python + pytest fit | High | 5/5 | 4/5 |
| React UI testing | High | 5/5 | 4.5/5 |
| Reliability | Very High | 5/5 | 4/5 |
| Debugging | Very High | 5/5 | 4/5 |
| Test isolation | Very High | 5/5 | 4/5 |
| CI integration | High | 5/5 | 5/5 |
| Parallel execution | High | 4.5/5 | 5/5 |
| Distributed infrastructure | Medium | 4/5 | 5/5 |
| Language breadth | Low | 4/5 | 5/5 |
| Modern developer experience | High | 5/5 | 4/5 |
| API + UI testing | High | 5/5 | 3.5/5 |
| Long-term maintainability | Very High | 5/5 | 4/5 |

These scores are project-specific engineering judgments, not universal framework rankings.

---

## 22. Should This Comparison Be Added to GitHub?

### Yes.

The document has real architectural value because browser-framework selection affects:

- Test architecture
- Dependencies
- CI configuration
- Developer onboarding
- Fixture design
- Page-object structure
- Debugging workflows
- Long-term maintenance

Without documentation, a future contributor may reasonably ask:

> Why are we using Playwright instead of Selenium?

Recording the decision prevents it from becoming undocumented team folklore.

### Recommended location

```text
docs/
└── testing/
    └── playwright-vs-selenium.md
```

Add a short README reference:

```markdown
### Testing Architecture

PayGuard-AI uses pytest for unit and API-level testing and Playwright
for browser-based end-to-end testing.

See
[`docs/testing/playwright-vs-selenium.md`](docs/testing/playwright-vs-selenium.md)
for the framework evaluation and architectural rationale.
```

---

## 23. Why the Document Adds Value

### 1. It records an architectural decision

Future contributors can see that Playwright was selected deliberately.

### 2. It improves onboarding

A new QA engineer can quickly understand:

```text
Unit test -> pytest
API test  -> pytest/TestClient
UI/E2E   -> Playwright
```

### 3. It prevents unnecessary rewrites

The document makes it clear why the existing API and unit layers should not be replaced by browser tests.

### 4. It provides criteria for future reconsideration

Technology choices should not become permanent doctrine.

If requirements later shift toward:

```text
large Selenium Grid
multiple programming languages
enterprise WebDriver infrastructure
```

the documented criteria provide a rational trigger for reevaluation.

---

## 24. Final Recommendation

> **Use Playwright for PayGuard-AI's browser/E2E automation, keep the existing pytest API and unit tests, and document the decision as a testing architecture decision record in `docs/testing/playwright-vs-selenium.md`.**

This gives the project modern browser automation without throwing away the 92-test backend regression suite that is already working.

---

## 25. Official References

The comparison should be maintained against official documentation:

### Playwright

- [Playwright Python installation and pytest integration](https://playwright.dev/python/docs/intro)
- [Playwright browser support](https://playwright.dev/python/docs/browsers)
- [Playwright auto-waiting and actionability](https://playwright.dev/python/docs/actionability)
- [Playwright debugging and Inspector](https://playwright.dev/python/docs/running-tests)
- [Playwright Trace Viewer](https://playwright.dev/python/docs/trace-viewer)
- [Playwright API testing](https://playwright.dev/python/docs/api-testing)
- [Playwright CI guidance](https://playwright.dev/python/docs/ci)

### Selenium

- [Selenium documentation](https://www.selenium.dev/documentation/)
- [Selenium Manager](https://www.selenium.dev/documentation/selenium_manager/)
- [Selenium waiting strategies](https://www.selenium.dev/documentation/webdriver/waits/)
- [Selenium Grid](https://www.selenium.dev/documentation/grid/getting_started/)
- [Selenium WebDriver BiDi](https://www.selenium.dev/documentation/webdriver/bidi/)
- [Selenium test practices and Page Objects](https://www.selenium.dev/documentation/test_practices/)

Framework capabilities change over time, so these references should be revisited when the automation stack is upgraded.
