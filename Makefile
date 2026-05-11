.PHONY: up down logs ps \
        nifi-open \
        kafka-consume kafka-offsets \
        db-list db-count db-totals \
        report \
        clean

KAFKA  := $(shell docker compose ps -q kafka)
PG     := $(shell docker compose ps -q postgres)

# --- Lifecycle ---

up:
	docker compose up -d --build

down:
	docker compose down

clean:
	docker compose down -v

logs:
	docker compose logs -f rest-api

ps:
	docker compose ps

# --- NiFi ---

nifi-open:
	open https://localhost:8443

# --- Kafka ---

kafka-consume:
	docker exec -it $(KAFKA) \
		/opt/kafka/bin/kafka-console-consumer.sh \
		--bootstrap-server localhost:9092 \
		--topic transactions \
		--from-beginning

kafka-offsets:
	docker exec -it $(KAFKA) \
		/opt/kafka/bin/kafka-run-class.sh kafka.tools.GetOffsetShell \
		--broker-list localhost:9092 \
		--topic transactions

# --- Report ---

report:
	@test -n "$(CSV)" || (echo "Usage: make report CSV=<path/to/source.csv>"; exit 1)
	python3 report.py $(CSV)

# --- PostgreSQL ---

db-list:
	docker exec -it $(PG) \
		psql -U gig -d gigdb -c \
		"SELECT * FROM transactions ORDER BY created_at DESC LIMIT 20;"

db-count:
	docker exec -it $(PG) \
		psql -U gig -d gigdb -c \
		"SELECT COUNT(*) FROM transactions;"

db-totals:
	docker exec -it $(PG) \
		psql -U gig -d gigdb -c \
		"SELECT currency, COUNT(*), SUM(amount) FROM transactions GROUP BY currency;"
