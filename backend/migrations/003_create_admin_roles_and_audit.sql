-- DDL Migration: 003_create_admin_roles_and_audit.sql
-- Production Schema for Admin Users, Role-Based Access Control (RBAC), and Audit Trail
-- Aligned with Project Proposal Section 7 (Primary User Roles) and Section 4 (Phase 1 Database Structure)

-- 1. Enum for Admin Roles matching Project Proposal Section 7
DO $$ BEGIN
    CREATE TYPE admin_role_type AS ENUM (
        'SUPER_ADMIN',
        'ACQUISITION_TEAM',
        'VERIFICATION_OFFICER',
        'LEGAL_REVIEWER',
        'FIELD_EXECUTIVE',
        'RELATIONSHIP_TEAM'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Table: admin_users
CREATE TABLE IF NOT EXISTS admin_users (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role admin_role_type NOT NULL DEFAULT 'VERIFICATION_OFFICER',
    phone TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index on email & role for high-speed authentication
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users (email);
CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users (role);

-- 3. Table: property_audit_logs
-- Immutable audit ledger tracking every status change (NEEDS_REVIEW -> PUBLISHED / REJECTED)
CREATE TABLE IF NOT EXISTS property_audit_logs (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    property_id TEXT NOT NULL REFERENCES auction_properties(id) ON DELETE CASCADE,
    admin_id TEXT REFERENCES admin_users(id) ON DELETE SET NULL,
    admin_email TEXT NOT NULL,
    action TEXT NOT NULL, -- 'VERIFY_AND_PUBLISH', 'REJECT', 'UPDATE_FIELDS', 'LEGAL_NOTE_ADDED'
    changes JSONB,        -- Previous and updated field diffs
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for property audit lookup
CREATE INDEX IF NOT EXISTS idx_audit_logs_property ON property_audit_logs (property_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON property_audit_logs (created_at DESC);

-- 4. Seed Default Production Administrative Accounts
INSERT INTO admin_users (email, full_name, role, phone, is_active)
VALUES
    ('admin@skandx.com', 'Chief Auction Officer', 'SUPER_ADMIN', '+91 98400 00001', true),
    ('verifier@skandx.com', 'Senior Recovery Verifier', 'VERIFICATION_OFFICER', '+91 98400 00002', true),
    ('legal@skandx.com', 'SARFAESI Legal Reviewer', 'LEGAL_REVIEWER', '+91 98400 00003', true),
    ('field@skandx.com', 'Field Inspection Officer', 'FIELD_EXECUTIVE', '+91 98400 00004', true),
    ('concierge@skandx.com', 'Buyer Relationship Lead', 'RELATIONSHIP_TEAM', '+91 98400 00005', true)
ON CONFLICT (email) DO NOTHING;

-- 5. Row Level Security (RLS) Configuration
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_audit_logs ENABLE ROW LEVEL SECURITY;

-- Service Role maintains administrative access
DROP POLICY IF EXISTS "Service Role Admin Access" ON admin_users;
CREATE POLICY "Service Role Admin Access" ON admin_users
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service Role Audit Access" ON property_audit_logs;
CREATE POLICY "Service Role Audit Access" ON property_audit_logs
    FOR ALL USING (auth.role() = 'service_role');
