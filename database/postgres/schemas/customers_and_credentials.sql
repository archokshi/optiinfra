-- ============================================================================
-- OptiInfra - Customers and Cloud Credentials Schema
-- ============================================================================
-- Purpose: Store customer information and their cloud provider credentials
-- Security: Credentials are encrypted at rest
-- ============================================================================

-- Enable pgcrypto extension for encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- CUSTOMERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    
    -- Account status
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'trial', 'cancelled')),
    subscription_tier VARCHAR(50) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'starter', 'professional', 'enterprise')),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes
    CONSTRAINT customers_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Indexes for customers
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);
CREATE INDEX IF NOT EXISTS idx_customers_created_at ON customers(created_at);

-- ============================================================================
-- CLOUD_CREDENTIALS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS cloud_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    
    -- Provider information
    provider VARCHAR(50) NOT NULL CHECK (provider IN (
        -- Big 3
        'aws', 'gcp', 'azure',
        -- GPU Providers
        'runpod', 'lambdalabs', 'paperspace', 'coreweave',
        -- General Cloud
        'vultr', 'digitalocean', 'linode', 'hetzner', 'ovh',
        -- Self-Hosted
        'kubernetes', 'proxmox', 'openstack'
    )),
    credential_name VARCHAR(255) NOT NULL, -- User-friendly name like "Production Vultr" or "Dev AWS"
    
    -- Encrypted credentials (stored as encrypted text)
    -- We'll use pgcrypto's PGP encryption
    encrypted_credentials BYTEA NOT NULL,
    
    -- Credential metadata (non-sensitive)
    credential_type VARCHAR(50) DEFAULT 'api_key' CHECK (credential_type IN ('api_key', 'service_account', 'access_key', 'oauth')),
    permissions VARCHAR(50) DEFAULT 'read_only' CHECK (permissions IN ('read_only', 'read_write', 'admin')),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false, -- Whether we've successfully tested the credentials
    last_verified_at TIMESTAMP WITH TIME ZONE,
    verification_error TEXT,
    
    -- Usage tracking
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE, -- Optional expiration date
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Constraints
    CONSTRAINT cloud_credentials_unique_name UNIQUE (customer_id, provider, credential_name)
);

-- Indexes for cloud_credentials
CREATE INDEX IF NOT EXISTS idx_cloud_credentials_customer_id ON cloud_credentials(customer_id);
CREATE INDEX IF NOT EXISTS idx_cloud_credentials_provider ON cloud_credentials(provider);
CREATE INDEX IF NOT EXISTS idx_cloud_credentials_active ON cloud_credentials(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_cloud_credentials_customer_provider ON cloud_credentials(customer_id, provider);

-- ============================================================================
-- CREDENTIAL_AUDIT_LOG TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS credential_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    credential_id UUID NOT NULL REFERENCES cloud_credentials(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    
    -- Action details
    action VARCHAR(50) NOT NULL CHECK (action IN ('created', 'updated', 'deleted', 'verified', 'used', 'failed')),
    action_details TEXT,
    
    -- Context
    ip_address INET,
    user_agent TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for credential_audit_log
CREATE INDEX IF NOT EXISTS idx_credential_audit_log_credential_id ON credential_audit_log(credential_id);
CREATE INDEX IF NOT EXISTS idx_credential_audit_log_customer_id ON credential_audit_log(customer_id);
CREATE INDEX IF NOT EXISTS idx_credential_audit_log_created_at ON credential_audit_log(created_at);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to encrypt credentials
CREATE OR REPLACE FUNCTION encrypt_credential(
    p_credential_data JSONB,
    p_encryption_key TEXT
) RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(p_credential_data::TEXT, p_encryption_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to decrypt credentials
CREATE OR REPLACE FUNCTION decrypt_credential(
    p_encrypted_data BYTEA,
    p_encryption_key TEXT
) RETURNS JSONB AS $$
BEGIN
    RETURN pgp_sym_decrypt(p_encrypted_data, p_encryption_key)::JSONB;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Failed to decrypt credentials: %', SQLERRM;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cloud_credentials_updated_at
    BEFORE UPDATE ON cloud_credentials
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SAMPLE DATA (for development only)
-- ============================================================================

-- Insert a sample customer
INSERT INTO customers (id, email, company_name, first_name, last_name, status, subscription_tier)
VALUES (
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::UUID,
    'alpesh@optiinfra.com',
    'OptiInfra',
    'Alpesh',
    'Chokshi',
    'active',
    'enterprise'
) ON CONFLICT (email) DO NOTHING;

-- Note: Actual credentials should be added through the API, not SQL
-- This is just to show the structure

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE customers IS 'OptiInfra customers and their account information';
COMMENT ON TABLE cloud_credentials IS 'Encrypted cloud provider credentials for each customer';
COMMENT ON TABLE credential_audit_log IS 'Audit log for all credential-related actions';

COMMENT ON COLUMN customers.status IS 'Customer account status: active, suspended, trial, cancelled';
COMMENT ON COLUMN customers.subscription_tier IS 'Subscription level: free, starter, professional, enterprise';

COMMENT ON COLUMN cloud_credentials.encrypted_credentials IS 'PGP-encrypted JSON containing provider-specific credentials';
COMMENT ON COLUMN cloud_credentials.is_verified IS 'Whether credentials have been successfully tested against the provider API';
COMMENT ON COLUMN cloud_credentials.permissions IS 'Permission level: read_only (recommended), read_write, admin';

-- ============================================================================
-- SECURITY NOTES
-- ============================================================================
-- 1. Credentials are encrypted using pgcrypto's PGP symmetric encryption
-- 2. The encryption key should be stored in environment variables, NOT in the database
-- 3. Only the data-collector service should have access to decrypt credentials
-- 4. All credential access is logged in credential_audit_log
-- 5. Customers should use read-only API keys whenever possible
-- ============================================================================
