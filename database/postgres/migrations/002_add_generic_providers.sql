-- Migration: Add support for Generic Collector providers
-- Date: 2025-10-31
-- Description: Update cloud_credentials provider CHECK constraint to include all 15+ providers

-- Drop the old constraint
ALTER TABLE cloud_credentials DROP CONSTRAINT IF EXISTS cloud_credentials_provider_check;

-- Add the new constraint with all providers
ALTER TABLE cloud_credentials ADD CONSTRAINT cloud_credentials_provider_check 
CHECK (provider IN (
    -- Big 3
    'aws', 'gcp', 'azure',
    -- GPU Providers
    'runpod', 'lambdalabs', 'paperspace', 'coreweave',
    -- General Cloud
    'vultr', 'digitalocean', 'linode', 'hetzner', 'ovh',
    -- Self-Hosted
    'kubernetes', 'proxmox', 'openstack'
));

-- Verify the constraint
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conname = 'cloud_credentials_provider_check';
