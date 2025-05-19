-- UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'scan_verdict') THEN
        CREATE TYPE scan_verdict AS ENUM ('safe', 'potentially unsafe', 'unsafe');
    END IF;
END$$;

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dietary_restrictions (
    restriction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL
);

INSERT INTO dietary_restrictions (name) VALUES
    ('celiac'),
    ('vegan'),
    ('nut_allergy')
;

CREATE TABLE user_dietary_preferences (
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    restriction_id UUID REFERENCES dietary_restrictions(restriction_id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, restriction_id)
);

CREATE TABLE scans (
    scan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    s3_image_url TEXT NOT NULL,
    final_verdict scan_verdict NOT NULL,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scan_ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans(scan_id) ON DELETE CASCADE,
    ingredient_name TEXT NOT NULL,
    verdict scan_verdict NOT NULL,
    is_trace BOOLEAN DEFAULT FALSE,
);

CREATE TABLE password_resets (
    reset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE
);