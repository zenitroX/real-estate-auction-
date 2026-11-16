-- DDL Migration: 002_create_customer_leads.sql
-- Production Schema for Customer Leads & Inquiries
-- Aligned with PROJECT.md Section 3.2

CREATE TABLE IF NOT EXISTS customer_leads (
    id TEXT PRIMARY KEY DEFAULT ('#SK-' || LPAD(FLOOR(RANDOM() * 10000)::TEXT, 4, '0')),
    customer_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    property_id TEXT NOT NULL,
    property_title TEXT,
    inquiry_type TEXT NOT NULL,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'NEW',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Operational Query Index
CREATE INDEX IF NOT EXISTS idx_customer_leads_created ON customer_leads (created_at DESC);

-- Row Level Security (RLS) Configuration
ALTER TABLE customer_leads ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public Insert Leads" ON customer_leads;
CREATE POLICY "Public Insert Leads" ON customer_leads 
    FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Service Role Leads Access" ON customer_leads;
CREATE POLICY "Service Role Leads Access" ON customer_leads 
    FOR ALL USING (auth.role() = 'service_role');
