-- ==============================================================================
-- Bank Auction & SARFAESI Legal Notice Schema (PostgreSQL + PostGIS for Supabase)
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Enums
DO $$ BEGIN
    CREATE TYPE asset_category_enum AS ENUM (
        'LAND_PLOT', 'HOUSE_VILLA', 'FLAT_APARTMENT', 'COMMERCIAL', 'AGRICULTURAL', 'INDUSTRIAL', 'OTHER'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE possession_type_enum AS ENUM (
        'PHYSICAL', 'SYMBOLIC', 'UNKNOWN'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE review_status_enum AS ENUM (
        'PUBLISHED', 'NEEDS_MANUAL_REVIEW', 'EXPIRED', 'SOLD'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Core Auction Properties Table
CREATE TABLE IF NOT EXISTS auction_properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_fingerprint TEXT NOT NULL,          -- SHA-256 of (bank + district + normalized_survey_numbers)
    auction_event_hash TEXT UNIQUE NOT NULL,  -- SHA-256 of (asset_fingerprint + auction_date)
    
    bank_name TEXT NOT NULL,
    branch_name TEXT,
    borrower_name TEXT,
    asset_category asset_category_enum NOT NULL DEFAULT 'OTHER',
    possession_type possession_type_enum NOT NULL DEFAULT 'UNKNOWN',
    
    survey_numbers TEXT[] NOT NULL DEFAULT '{}',
    patta_or_door_no TEXT,
    village_or_locality TEXT NOT NULL,
    taluk TEXT,
    district TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'Tamil Nadu',
    pincode TEXT,
    area_description TEXT NOT NULL,
    area_sqft NUMERIC,
    boundaries JSONB,                         -- {"north": "...", "south": "...", "east": "...", "west": "..."}
    
    reserve_price_inr BIGINT NOT NULL,
    previous_reserve_price_inr BIGINT,        -- Populated automatically if asset_fingerprint existed before
    price_drop_percentage NUMERIC(5,2),
    emd_amount_inr BIGINT NOT NULL,
    bid_increment_inr BIGINT,
    
    emd_last_date TIMESTAMPTZ,
    inspection_date_info TEXT,
    auction_date TIMESTAMPTZ NOT NULL,
    
    authorized_officer_name TEXT,
    contact_phone TEXT,
    source_portal TEXT NOT NULL,
    source_pdf_url TEXT,
    bidding_portal_url TEXT,
    
    review_status review_status_enum NOT NULL DEFAULT 'PUBLISHED',
    review_notes TEXT,
    raw_extracted_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Indexes for high-throughput queries & deduplication
CREATE INDEX IF NOT EXISTS idx_auction_district_status ON auction_properties (district, review_status, auction_date);
CREATE INDEX IF NOT EXISTS idx_asset_fingerprint ON auction_properties (asset_fingerprint);
CREATE INDEX IF NOT EXISTS idx_auction_date ON auction_properties (auction_date DESC);

-- 4. Trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS trigger_auction_properties_updated_at ON auction_properties;
CREATE TRIGGER trigger_auction_properties_updated_at
    BEFORE UPDATE ON auction_properties
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 5. Row Level Security (RLS) policies
ALTER TABLE auction_properties ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    CREATE POLICY "Public read access for published auction properties"
        ON auction_properties FOR SELECT
        USING (review_status = 'PUBLISHED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE POLICY "Service role full access"
        ON auction_properties FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

