CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(50)   PRIMARY KEY,
    account_id     VARCHAR(20)   NOT NULL,
    amount         NUMERIC(19,4) NOT NULL CHECK (amount >= 0),
    currency       VARCHAR(3)    NOT NULL,
    ts             TIMESTAMPTZ   NOT NULL,
    status         VARCHAR(20)   NOT NULL,
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
