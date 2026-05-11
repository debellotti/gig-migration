CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(50)   PRIMARY KEY,
    account_id     VARCHAR(20)   NOT NULL,
    amount         NUMERIC(19,4) NOT NULL CHECK (amount >= 0),
    currency       VARCHAR(3)    NOT NULL,
    ts             TIMESTAMPTZ   NOT NULL,
    status         VARCHAR(20)   NOT NULL,
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS accounts (
    id          UUID          PRIMARY KEY,
    owner_name  VARCHAR(100)  NOT NULL,
    balance     NUMERIC(19,4) NOT NULL CHECK (balance >= 0),
    currency    VARCHAR(3)    NOT NULL,
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transfers (
    id              UUID          PRIMARY KEY,
    from_account_id UUID          NOT NULL REFERENCES accounts(id),
    to_account_id   UUID          NOT NULL REFERENCES accounts(id),
    amount          NUMERIC(19,4) NOT NULL CHECK (amount > 0),
    currency        VARCHAR(3)    NOT NULL,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
