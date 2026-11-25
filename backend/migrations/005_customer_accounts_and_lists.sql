-- DDL Migration: 005_customer_accounts_and_lists.sql
-- Phase 2: Customer profiles, saved properties, and recently viewed history with strict RLS.

CREATE TABLE IF NOT EXISTS customer_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    phone TEXT,
    preferred_contact TEXT DEFAULT 'PHONE',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS saved_properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL REFERENCES auction_properties(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, property_id)
);

CREATE TABLE IF NOT EXISTS recently_viewed (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL REFERENCES auction_properties(id) ON DELETE CASCADE,
    viewed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, property_id)
);

CREATE INDEX IF NOT EXISTS idx_saved_properties_user ON saved_properties (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_recently_viewed_user ON recently_viewed (user_id, viewed_at DESC);

ALTER TABLE customer_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE recently_viewed ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Customer Own Profile" ON customer_profiles;
CREATE POLICY "Customer Own Profile" ON customer_profiles
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Customer Own Saved" ON saved_properties;
CREATE POLICY "Customer Own Saved" ON saved_properties
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Customer Own Recently Viewed" ON recently_viewed;
CREATE POLICY "Customer Own Recently Viewed" ON recently_viewed
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
