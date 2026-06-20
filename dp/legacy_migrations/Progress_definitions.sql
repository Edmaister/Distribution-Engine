CREATE TABLE IF NOT EXISTS progress_definitions (
    id BIGSERIAL PRIMARY KEY,
    product VARCHAR(100) NOT NULL,
    sub_product VARCHAR(100),
    completion_event VARCHAR(100) NOT NULL,
    milestones_json JSONB NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_progress_definitions_product_sub
    ON progress_definitions (product, sub_product, is_active);


