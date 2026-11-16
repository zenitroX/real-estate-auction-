-- DDL Migration: 001_create_auction_properties.sql
-- Production Schema for Indian Bank Auction Discovery Platform (SKANDX)
-- Aligned with PROJECT.md Section 3.1 & backend/ingestion/database/supabase_client.py

CREATE TABLE IF NOT EXISTS auction_properties (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    property_title TEXT DEFAULT 'Bank Foreclosure Asset',
    bank_name TEXT NOT NULL,
    branch_name TEXT,
    borrower_name TEXT,
    asset_category TEXT DEFAULT 'OTHER',
    possession_type TEXT NOT NULL DEFAULT 'PHYSICAL',
    survey_numbers JSONB DEFAULT '[]'::JSONB,
    patta_or_door_no TEXT,
    village_or_locality TEXT NOT NULL,
    taluk TEXT,
    district TEXT,
    state TEXT NOT NULL DEFAULT 'Tamil Nadu',
    pincode TEXT,
    area_description TEXT,
    area_sqft NUMERIC(10,2),
    boundaries JSONB,
    reserve_price_inr NUMERIC(14,2) NOT NULL,
    previous_reserve_price_inr NUMERIC(14,2),
    price_drop_percentage NUMERIC(5,2) DEFAULT 0.0,
    emd_amount_inr NUMERIC(14,2) NOT NULL,
    bid_increment_inr NUMERIC(14,2),
    emd_last_date TIMESTAMPTZ,
    inspection_date_info TEXT,
    auction_date TIMESTAMPTZ NOT NULL,
    authorized_officer_name TEXT,
    contact_phone TEXT,
    source_portal TEXT,
    source_pdf_url TEXT,
    bidding_portal_url TEXT,
    auction_event_hash TEXT UNIQUE,
    asset_fingerprint TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'NEEDS_MANUAL_REVIEW',
    review_notes TEXT,
    raw_extracted_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance Indexes for Query Filtering & Deduplication
CREATE INDEX IF NOT EXISTS idx_auction_properties_status ON auction_properties (review_status);
CREATE INDEX IF NOT EXISTS idx_auction_properties_fingerprint ON auction_properties (asset_fingerprint);
CREATE INDEX IF NOT EXISTS idx_auction_properties_event_hash ON auction_properties (auction_event_hash);

-- Row Level Security (RLS) Configuration
ALTER TABLE auction_properties ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public Read Published" ON auction_properties;
CREATE POLICY "Public Read Published" ON auction_properties 
    FOR SELECT USING (review_status = 'PUBLISHED');

DROP POLICY IF EXISTS "Service Role Full Access" ON auction_properties;
CREATE POLICY "Service Role Full Access" ON auction_properties 
    FOR ALL USING (auth.role() = 'service_role');
