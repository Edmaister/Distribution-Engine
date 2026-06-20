CREATE TABLE IF NOT EXISTS settlement_batch_items (
    batch_item_id UUID PRIMARY KEY,
    batch_id UUID NOT NULL,
    settlement_id UUID NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_batch
        FOREIGN KEY(batch_id)
        REFERENCES settlement_batches(batch_id)
);

CREATE INDEX IF NOT EXISTS idx_settlement_batch_items_batch
ON settlement_batch_items(batch_id);

CREATE INDEX IF NOT EXISTS idx_settlement_batch_items_settlement
ON settlement_batch_items(settlement_id);
