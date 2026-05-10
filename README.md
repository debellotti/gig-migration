# gig-migration

CSV → NiFi (validate + deduplicate) → Kafka → Java → PostgreSQL

## Start

```bash
make up
```

Wait ~60-90s for all services to be healthy, then open NiFi:

```bash
make nifi-open  # https://localhost:8443
```

Credentials: `admin` / `admin123456789`

Select all processors with **Ctrl+A** → right click → **Start**.

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

## Verify

```bash
make kafka-consume   # messages on the transactions topic
make db-list         # last 20 records in the DB
make db-count        # total record count
make db-totals       # breakdown by currency
make logs            # Java consumer logs
```

Records rejected by NiFi → `./data/errors/`

## Stop

```bash
make down    # stop everything, data is kept
make clean   # stop everything and wipe the DB
```
