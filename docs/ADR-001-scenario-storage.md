# ADR-001: Scenario definition and run evidence storage

- **Date:** 23 November 2026
- **Status:** Accepted for incremental implementation
- **Scope:** Day 4 design only; no schema or persistence code is implemented by this ADR.

## Context

PayGuard-AI already uses PostgreSQL, SQLAlchemy and Alembic in a modular monolith. Migrations run through the explicitly configured `PAYGUARD_MIGRATION_DATABASE_URL` and the `payguard_migrator` role; the API uses the restricted `payguard_app` role. The Day 3 scenario schema provides typed, frozen definitions and run/result records, with scalar-only parameters and outputs.

Scenario storage must retain the exact scenario version used by a run, preserve useful evidence after failures, allow deterministic reconstruction, and avoid creating an unnecessary service, broker or new database. Synthetic data only is permitted.

## Decision

Use the existing PostgreSQL database and incremental Alembic migrations. Store fixed identifiers, status, timestamps and query fields in relational columns; store the validated scenario payload and bounded scalar evidence in PostgreSQL JSONB. The JSONB payload is not an executable-code container.

### 1. Versioned scenario definitions

The planned `scenario_definitions` table stores one immutable row per logical scenario version:

| Field | Design |
|---|---|
| `scenario_id` | Stable restricted-format logical identifier |
| `version` | Positive logical scenario version |
| `schema_version` | Version of the serialized definition format, separate from logical version |
| `name`, `description`, `tags` | Validated searchable metadata |
| `definition_json` | Complete validated definition, JSONB |
| `definition_sha256` | SHA-256 digest of canonical serialized definition |
| `created_at` | Timezone-aware database timestamp |

- Composite primary key: `(scenario_id, version)`.
- Logical versions are insert-only. Editing a scenario creates a new version; repository/API code must not overwrite an existing definition version.
- The digest is computed from a canonical JSON representation before persistence (stable key ordering and separators, with the serialization format version recorded). It is a consistency fingerprint, not a signature or a trust boundary.
- Metadata columns are derived from the validated payload. Persistence must verify that the extracted values and digest correspond to the payload.

### 2. Run records and snapshots

The planned `scenario_runs` table stores:

- UUID `run_id` primary key.
- `scenario_id` and `scenario_version`, with a restrictive composite foreign key to the stored definition version.
- `status`, `created_at`, `started_at`, `finished_at` and optional sanitized `failure_reason`.
- `definition_snapshot` JSONB and `snapshot_sha256`, frozen when the run is created.

The snapshot is deliberately redundant with the referenced definition. It makes a run self-contained for later report/replay, even if retrieval or retention of the definition changes. It must match the referenced version at creation. A run is never silently re-pointed to a newer scenario version.

- Status transitions are monotonic: `pending -> running -> passed | failed | cancelled`. Terminal states cannot be reopened.
- Database checks enforce the basic status/timestamp combinations and positive versions where feasible; transition and snapshot validation remain repository/service responsibilities.
- Foreign keys use restrictive deletion behavior. Run evidence is not cascade-deleted when a definition is archived or when synthetic payment state is reset.

### 3. Result and event tables, introduced in later increments

The target storage shape includes separate, run-scoped tables. These are not part of Day 5's initial persistence slice unless the later scheduled scope requires them.

| Table | Planned fields and invariants |
|---|---|
| `scenario_step_results` | `run_id`, `step_id`, `ordinal`, status, start/finish times, scalar-output JSONB and sanitized error; unique step ID and ordinal per run |
| `scenario_assertion_results` | `run_id`, assertion ID, status, expected/observed JSONB and sanitized message; unique assertion ID per run |
| `scenario_run_events` | Per-run sequence, event type, timestamp, optional step ID and sanitized JSONB payload; append-only |

Step and assertion identifiers are validated against the frozen run snapshot. These tables use restrictive run references and are introduced in the days assigned to runner, assertions and timeline/evidence work.

For event sequencing, the runner/repository allocates the next sequence while locking the run row. Event records are insert-only; future migrations and privilege tests must enforce the intended append-only boundary, not rely solely on a UI convention.

### 4. Serialization, query and indexing

- Use JSONB for the validated definition snapshot, step outputs, assertion expected/observed values and event payloads. Keep status, IDs, sequence and timestamps relational.
- Use the existing Pydantic schemas and versioned serialization. Reject unknown fields, nested step parameters/outputs and executable-oriented parameter names; never store arbitrary code.
- Compute digests from canonical serialized data before JSONB storage. Do not hash PostgreSQL's rendered JSONB text.
- Initial indexes: the definition composite primary key; runs by `(scenario_id, scenario_version, created_at)` and `(status, created_at)`; step results by `(run_id, ordinal)`; assertions by run; events by `(run_id, sequence)`. Add other indexes only after an observed query need.
- Apply bounded payload sizes in validation/persistence. Redact sensitive fields before evidence persistence. Scenario parameters and evidence must not contain real PAN, CVV/CVC, production credentials or raw payment request bodies.

### 5. Transaction boundaries and failure evidence

- Saving a new scenario version and its digest is one database transaction.
- Creating a run and freezing its definition snapshot is one transaction.
- A runner step's status/result and its corresponding scenario event should commit together within the scenario-evidence transaction.
- A simulated payment operation retains its own payment-service transaction boundary. A response-loss-after-commit scenario intentionally represents an outcome where the payment mutation committed but the runner's subsequent evidence transaction records the lost response/ambiguous result. These two commits cannot be claimed atomic; they must be linked with stable run/step/transaction/correlation identifiers and tested for recovery/replay behavior.
- Run failures must preserve the run and its evidence. No blanket exactly-once guarantee is implied.

### 6. Migration and privilege boundary

The next migration follows the existing Alembic chain (current head is `005_audit_reference_without_fk`). Migration DDL is executed only with the migration-owner connection and `payguard_migrator`. The runtime `payguard_app` role receives only the table access needed for scenario operations and must not gain schema ownership, CREATE or migration privileges. Privilege tests must use the correct owner/runtime roles and a disposable PostgreSQL database.

The Day 5 implementation must not change the existing audit-history privileges, audit triggers or database role separation.

### 7. Retention and deletion

No hard-delete API is planned for scenario versions or run evidence in the initial lab. Definitions are immutable and runs/evidence are retained by default. A retention/export policy is a separate future decision; any cleanup must be explicit, tested and must not cascade-delete run evidence or alter audit history.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| One opaque JSON document per run with no relational tables | Makes run status, version references, step ordering and consistency constraints harder to query and verify |
| Fully normalize scenario definitions into many step/parameter tables immediately | Adds complexity before the runner and authoring requirements are proven; the typed definition is bounded and versioned |
| Separate database, microservice or distributed broker | No demonstrated need; violates the modular-monolith and incremental delivery constraints |
| Mutable scenario row with a single version field | Risks changing the definition against which historical runs were executed |

## Consequences

- Definition versions and run snapshots are durable, explicit and queryable.
- JSONB schema evolution requires a recorded serialization version and canonical serializer.
- The runner must use explicit transaction boundaries and identifiers to capture ambiguous outcomes.
- The implementation is phased. Day 5 starts with definition/run persistence; runner results, assertion results and timeline events arrive in their scheduled increments.
- This ADR does not claim implementation, tests, PCI compliance or real payment processing.


## Day 5 implementation record (24 November 2026)

The initial persistence slice implements the definition and run tables, canonical JSON digests, insert-only definition versions, frozen run snapshots, composite version references, query indexes and a 64 KiB payload bound. JSON snapshots are revalidated using JSON-mode parsing so strict Decimal values round-trip. Runtime privileges are restricted to inserts/reads for definitions and lifecycle-column updates for runs. Step/assertion result and timeline persistence, runner transitions and report artifacts remain scheduled for later days. This record is implementation status, not an extension of the accepted design's claims.
