SELECT provider, credential_name, is_active, is_verified, created_at 
FROM cloud_credentials 
ORDER BY created_at DESC 
LIMIT 5;
