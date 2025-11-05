-- PostgreSQL Schema for Collection History
-- Phase 6.1: Data Collector Service

-- Collection history table
CREATE TABLE IF NOT EXISTS collection_history (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    task_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    metrics_collected INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_collection_customer ON collection_history(customer_id);
CREATE INDEX IF NOT EXISTS idx_collection_provider ON collection_history(provider);
CREATE INDEX IF NOT EXISTS idx_collection_task ON collection_history(task_id);
CREATE INDEX IF NOT EXISTS idx_collection_status ON collection_history(status);
CREATE INDEX IF NOT EXISTS idx_collection_started ON collection_history(started_at DESC);

-- Comments
COMMENT ON TABLE collection_history IS 'Tracks all data collection operations';
COMMENT ON COLUMN collection_history.customer_id IS 'Customer identifier';
COMMENT ON COLUMN collection_history.provider IS 'Cloud provider (vultr, aws, gcp, azure)';
COMMENT ON COLUMN collection_history.task_id IS 'Unique task identifier';
COMMENT ON COLUMN collection_history.status IS 'Collection status (queued, running, success, failed)';
COMMENT ON COLUMN collection_history.metrics_collected IS 'Number of metrics collected';
COMMENT ON COLUMN collection_history.error_message IS 'Error message if collection failed';
