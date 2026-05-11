# gig-migration

CSV → NiFi (validate + deduplicate) → Kafka → Java → PostgreSQL

## Start

```bash
docker compose up -d --build
```

This single command provisions the entire ecosystem:
- PostgreSQL initialized with the schema
- Kafka broker
- NiFi with the flow deployed and all processors started automatically
- Java microservice connected to Kafka and PostgreSQL

## Trigger the pipeline

Drop a CSV file into the `data/` folder:

```bash
cp transactions.csv ./data/
```

Expected format:

```
transaction_id,account_id,amount,currency,ts,status
550e8400-e29b-41d4-a716-446655440000,GIG-USR-1,99.99,EUR,2024-03-25T10:25:00Z,SUCCESS
```

## REST API

Base URL: `http://localhost:8080`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/accounts` | Create an account |
| GET | `/accounts/{id}` | Get account details |
| POST | `/transfers` | Transfer money between accounts |
| GET | `/accounts/{id}/transfers` | Transfer history for an account |

```bash
# create account
curl -X POST http://localhost:8080/accounts \
  -H "Content-Type: application/json" \
  -d '{"ownerName":"Alice","currency":"EUR","initialBalance":1000.00}'

# transfer
curl -X POST http://localhost:8080/transfers \
  -H "Content-Type: application/json" \
  -d '{"fromAccountId":"<id>","toAccountId":"<id>","amount":200.00}'
```

Run the full demo:

```bash
./test.sh
```

## Migration report

Compares the source CSV against the database and prints a reconciliation summary:

```bash
make report CSV=transactions_test.csv
```

Output:
```
==================================
        MIGRATION REPORT
==================================
Total Source Records:      42
Total Successfully Migrated: 38
Total Failed/Skipped:      4
----------------------------------
Source Financial Value:    12345.6700
Migrated Financial Value:  11980.2300
==================================
```

> Note: `transactions_test.csv` is the source file used for comparison. Keep it in the project root — do not drop it into `data/`.

## Verify

```bash
make kafka-consume   # messages on the transactions topic
make db-list         # last 20 records in the transactions table
make db-count        # total record count
make db-totals       # breakdown by currency
make logs            # Java consumer logs
```

## Stop

```bash
make down    # stop everything, data is kept
make clean   # stop everything and wipe the DB
```

---

## Design decisions

### Duplicate handling

The CSV may contain multiple rows with the same `transaction_id`. The deduplication logic lives entirely inside NiFi (a Groovy `ExecuteScript` processor called `DeduplicateCSV`) and runs before any data reaches Kafka or the database.

For each group of rows sharing the same `transaction_id`, only the one with the highest `amount` is kept. The others are silently discarded. This happens in-memory within a single flowfile, so no database upsert or Kafka consumer-side logic is needed to resolve conflicts — only clean records ever enter the pipeline.

### Malformed data

A row is considered malformed if any of its fields cannot be converted to the expected type:

| Field | Expected |
|-------|----------|
| `transaction_id` | UUID format |
| `account_id` | `GIG-USR-{integer}` |
| `amount` | Parseable as decimal |
| `currency` | Valid ISO 4217 code |
| `ts` | ISO 8601 datetime |
| `status` | Exactly `SUCCESS` |

Validation runs in the `FilterRows` NiFi processor (Groovy). Malformed rows are dropped from the flowfile before it moves downstream. If a processor fails due to a transient error (e.g. Kafka temporarily unavailable), the record enters a retry loop: up to 3 attempts with the attempt count tracked as a flowfile attribute. After 3 failures the record is routed to `./data/errors/` for inspection.

The source CSV also contains timestamps split across two lines due to embedded newlines. The `FixTimestampNewlines` processor (NiFi `ReplaceText`) normalises these before validation runs.

### Schema design

Monetary amounts are stored as `NUMERIC(19,4)` — never `FLOAT` — to avoid floating-point rounding errors. Timestamps use `TIMESTAMPTZ` to preserve timezone information. The `transfers` table uses foreign keys to `accounts` to enforce referential integrity at the database level.

Money transfers are executed atomically: both the debit and the credit happen inside a single `@Transactional` method with pessimistic write locks on both accounts. Accounts are always locked in UUID order to prevent deadlocks under concurrent requests.
