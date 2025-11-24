CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL,
    duration_ms INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- test data
INSERT INTO system_logs (operation_type, duration_ms) VALUES
('READ', 15),
('WRITE', 30),
('READ', 10);