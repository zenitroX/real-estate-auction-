-- DDL Migration: 006_leads_upgrade_and_service_agreements.sql
-- Phase 3: Upgrade customer_leads (UUID PK, deduplication, advisor assignment),
-- revoke direct anon/authenticated access, add service_agreements, and atomic RPC.

ALTER TABLE customer_leads
    ALTER COLUMN id SET DEFAULT gen_random_uuid()::TEXT,
    ADD COLUMN IF NOT EXISTS lead_code TEXT UNIQUE,
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS preferred_contact TEXT DEFAULT 'PHONE',
    ADD COLUMN IF NOT EXISTS consent_to_contact BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS consent_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS assigned_advisor_id TEXT REFERENCES admin_users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

UPDATE customer_leads
SET status = 'REQUEST_RECEIVED'
WHERE status IN ('NEW', 'IN_REVIEW', 'SCHEDULED');

ALTER TABLE customer_leads
    ALTER COLUMN status SET DEFAULT 'REQUEST_RECEIVED';

DO $$ BEGIN
    ALTER TABLE customer_leads
        ADD CONSTRAINT chk_lead_status CHECK (status IN ('REQUEST_RECEIVED', 'CONTACTED', 'IN_PROGRESS', 'CLOSED'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_dedup_user
    ON customer_leads (user_id, property_id)
    WHERE user_id IS NOT NULL AND status <> 'CLOSED';

-- Revoke direct customer writes/reads so internal admin notes cannot leak via PostgREST
DROP POLICY IF EXISTS "Public Insert Leads" ON customer_leads;
REVOKE ALL ON customer_leads FROM anon, authenticated;

-- Proposed 5% Service Agreements (legal/tax review required before commercial launch)
CREATE TABLE IF NOT EXISTS service_agreements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
    property_id TEXT NOT NULL REFERENCES auction_properties(id),
    lead_id TEXT NOT NULL REFERENCES customer_leads(id),
    commission_rate_pct NUMERIC(4,2) NOT NULL DEFAULT 5.00,
    calculation_basis TEXT NOT NULL,
    agreement_version TEXT NOT NULL,
    accepted_name TEXT NOT NULL,
    accepted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address TEXT,
    user_agent TEXT
);

ALTER TABLE service_agreements ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Customer Own Agreements" ON service_agreements;
CREATE POLICY "Customer Own Agreements" ON service_agreements
    FOR SELECT USING (auth.uid() = user_id);

-- Atomic RPC for lead + optional service agreement creation
CREATE OR REPLACE FUNCTION create_lead_with_agreement(
    p_user_id UUID,
    p_property_id TEXT,
    p_property_title TEXT,
    p_customer_name TEXT,
    p_phone TEXT,
    p_email TEXT,
    p_preferred_contact TEXT,
    p_inquiry_type TEXT,
    p_notes TEXT,
    p_require_agreement BOOLEAN,
    p_commission_rate NUMERIC,
    p_calculation_basis TEXT,
    p_agreement_version TEXT,
    p_accepted_name TEXT,
    p_ip TEXT,
    p_ua TEXT
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_lead_id TEXT;
    v_lead_code TEXT;
    v_agreement_id UUID;
BEGIN
    v_lead_code := 'SK-' || to_char(NOW(), 'YYMMDD') || '-' || substr(gen_random_uuid()::TEXT, 1, 6);

    INSERT INTO customer_leads (
        lead_code, user_id, customer_name, phone, email, preferred_contact,
        property_id, property_title, inquiry_type, notes, status,
        consent_to_contact, consent_at
    )
    VALUES (
        v_lead_code, p_user_id, p_customer_name, p_phone, p_email, coalesce(p_preferred_contact, 'PHONE'),
        p_property_id, p_property_title, p_inquiry_type, p_notes, 'REQUEST_RECEIVED',
        true, NOW()
    )
    RETURNING id INTO v_lead_id;

    IF p_require_agreement THEN
        INSERT INTO service_agreements (
            user_id, property_id, lead_id, commission_rate_pct,
            calculation_basis, agreement_version, accepted_name, ip_address, user_agent
        )
        VALUES (
            p_user_id, p_property_id, v_lead_id, p_commission_rate,
            p_calculation_basis, p_agreement_version, p_accepted_name, p_ip, p_ua
        )
        RETURNING id INTO v_agreement_id;
    END IF;

    RETURN jsonb_build_object(
        'lead_id', v_lead_id,
        'lead_code', v_lead_code,
        'agreement_id', v_agreement_id
    );
END;
$$;
