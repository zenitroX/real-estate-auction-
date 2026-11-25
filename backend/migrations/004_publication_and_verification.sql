-- DDL Migration: 004_publication_and_verification.sql
-- Phase 1: Separate publication_status from 8-dimension verification_dimensions and risk_disclosures.
-- Revokes direct anon/authenticated SELECT on auction_properties so PII columns cannot be read via PostgREST.

ALTER TABLE auction_properties
    ADD COLUMN IF NOT EXISTS publication_status TEXT NOT NULL DEFAULT 'PENDING_ADMIN_APPROVAL',
    ADD COLUMN IF NOT EXISTS verification_dimensions JSONB NOT NULL DEFAULT '{}'::JSONB,
    ADD COLUMN IF NOT EXISTS risk_disclosures JSONB NOT NULL DEFAULT '[]'::JSONB,
    ADD COLUMN IF NOT EXISTS slug TEXT,
    ADD COLUMN IF NOT EXISTS last_source_confirmed_at TIMESTAMPTZ;

-- Backfill publication_status from legacy review_status
UPDATE auction_properties
SET publication_status = CASE
    WHEN review_status = 'PUBLISHED' THEN 'PUBLISHED'
    WHEN review_status = 'REJECTED' THEN 'UNPUBLISHED'
    ELSE 'PENDING_ADMIN_APPROVAL'
END
WHERE publication_status = 'PENDING_ADMIN_APPROVAL';

-- Backfill unique, URL-safe slug for existing rows
UPDATE auction_properties
SET slug = trim(both '-' from regexp_replace(lower(coalesce(property_title, 'auction')), '[^a-z0-9]+', '-', 'g')) || '-' || left(id, 8)
WHERE slug IS NULL;

-- Replace legacy status index with publication/discovery indexes
DROP INDEX IF EXISTS idx_auction_properties_status;
CREATE UNIQUE INDEX IF NOT EXISTS idx_auction_slug ON auction_properties (slug);
CREATE INDEX IF NOT EXISTS idx_auction_pub_date ON auction_properties (publication_status, auction_date);
CREATE INDEX IF NOT EXISTS idx_auction_district ON auction_properties (district);
CREATE INDEX IF NOT EXISTS idx_auction_category ON auction_properties (asset_category);
CREATE INDEX IF NOT EXISTS idx_auction_price ON auction_properties (reserve_price_inr);

-- Enforce single public read path through backend/app.py (service_role only)
DROP POLICY IF EXISTS "Public Read Published" ON auction_properties;
REVOKE SELECT ON auction_properties FROM anon, authenticated;
