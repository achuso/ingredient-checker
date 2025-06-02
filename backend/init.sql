-- UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'scan_verdict') THEN
        CREATE TYPE scan_verdict AS ENUM ('safe', 'potentially unsafe', 'unsafe');
    END IF;
END$$;

-- Users table
CREATE TABLE users (
    user_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT                 NOT NULL,
    created_at    TIMESTAMP            DEFAULT CURRENT_TIMESTAMP
);

-- Master list of dietary restrictions
CREATE TABLE dietary_restrictions (
    restriction_id UUID PRIMARY KEY    DEFAULT gen_random_uuid(),
    name           TEXT     UNIQUE     NOT NULL
);

INSERT INTO dietary_restrictions (name) VALUES
    ('celiac'),
    ('vegan'),
    ('nut_allergy')
;

----------------------------------------
-- Scans table
-- Store one row per image‐scan, with a summary verdict
----------------------------------------
CREATE TABLE scans (
    scan_id       UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID         REFERENCES users(user_id) ON DELETE CASCADE,
    s3_image_url  TEXT         NOT NULL,
    final_verdict scan_verdict NOT NULL,
    scanned_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

----------------------------------------
-- Link table
-- Which restriction(s) were used for this scan
----------------------------------------
CREATE TABLE scan_dietary_restrictions (
    scan_id        UUID REFERENCES scans(scan_id) ON DELETE CASCADE,
    restriction_id UUID REFERENCES dietary_restrictions(restriction_id) ON DELETE CASCADE,
    PRIMARY KEY (scan_id, restriction_id)
);

----------------------------------------
-- Ingredients extracted per scan, with per‐ingredient verdict
----------------------------------------
CREATE TABLE scan_ingredients (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id         UUID         REFERENCES scans(scan_id) ON DELETE CASCADE,
    ingredient_name TEXT         NOT NULL,
    verdict         scan_verdict NOT NULL,
    is_trace        BOOLEAN      DEFAULT FALSE
);
