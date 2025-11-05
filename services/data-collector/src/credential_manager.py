"""
Credential Manager - Secure storage and retrieval of cloud credentials
Phase 6.2+: Customer API Key Management
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class CredentialManager:
    """
    Manages encrypted cloud credentials stored in PostgreSQL
    
    Security Features:
    - Credentials encrypted using pgcrypto
    - Encryption key from environment variable
    - Audit logging for all access
    - Support for credential verification
    """
    
    def __init__(self):
        self.encryption_key = os.getenv("CREDENTIAL_ENCRYPTION_KEY", "optiinfra_dev_key_change_in_production")
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "optiinfra"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "postgres")
        }
        
        if self.encryption_key == "optiinfra_dev_key_change_in_production":
            logger.warning("⚠️  Using default encryption key! Change CREDENTIAL_ENCRYPTION_KEY in production!")
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def store_credential(
        self,
        customer_id: str,
        provider: str,
        credential_name: str,
        credentials: Dict[str, Any],
        credential_type: str = "api_key",
        permissions: str = "read_only"
    ) -> str:
        """
        Store encrypted credentials for a customer
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider (vultr, aws, gcp, azure)
            credential_name: User-friendly name
            credentials: Dict containing provider-specific credentials
            credential_type: Type of credential (api_key, service_account, etc.)
            permissions: Permission level (read_only, read_write, admin)
        
        Returns:
            credential_id: UUID of the stored credential
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Encrypt credentials
                credentials_json = json.dumps(credentials)
                
                cur.execute("""
                    INSERT INTO cloud_credentials (
                        customer_id,
                        provider,
                        credential_name,
                        encrypted_credentials,
                        credential_type,
                        permissions,
                        is_active
                    ) VALUES (
                        %s, %s, %s,
                        encrypt_credential(%s::jsonb, %s),
                        %s, %s, true
                    )
                    RETURNING id
                """, (
                    customer_id,
                    provider,
                    credential_name,
                    credentials_json,
                    self.encryption_key,
                    credential_type,
                    permissions
                ))
                
                result = cur.fetchone()
                credential_id = str(result['id'])
                
                # Log the action
                self._log_audit(
                    conn,
                    credential_id,
                    customer_id,
                    "created",
                    f"Credential '{credential_name}' created for {provider}"
                )
                
                conn.commit()
                logger.info(f"Stored credential {credential_id} for customer {customer_id}, provider {provider}")
                return credential_id
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to store credential: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def get_credential(
        self,
        customer_id: str,
        provider: str,
        credential_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt credentials for a customer
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider
            credential_name: Optional specific credential name
        
        Returns:
            Dict containing decrypted credentials, or None if not found
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if credential_name:
                    cur.execute("""
                        SELECT 
                            id,
                            decrypt_credential(encrypted_credentials, %s) as credentials,
                            credential_type,
                            permissions,
                            is_verified,
                            last_verified_at
                        FROM cloud_credentials
                        WHERE customer_id = %s
                          AND provider = %s
                          AND credential_name = %s
                          AND is_active = true
                        LIMIT 1
                    """, (self.encryption_key, customer_id, provider, credential_name))
                else:
                    # Get the most recently created active credential
                    cur.execute("""
                        SELECT 
                            id,
                            decrypt_credential(encrypted_credentials, %s) as credentials,
                            credential_type,
                            permissions,
                            is_verified,
                            last_verified_at
                        FROM cloud_credentials
                        WHERE customer_id = %s
                          AND provider = %s
                          AND is_active = true
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (self.encryption_key, customer_id, provider))
                
                result = cur.fetchone()
                
                if result:
                    credential_id = str(result['id'])
                    
                    # Update usage tracking
                    cur.execute("""
                        UPDATE cloud_credentials
                        SET last_used_at = CURRENT_TIMESTAMP,
                            usage_count = usage_count + 1
                        WHERE id = %s
                    """, (credential_id,))
                    
                    # Log the access
                    self._log_audit(
                        conn,
                        credential_id,
                        customer_id,
                        "used",
                        f"Credential accessed for {provider}"
                    )
                    
                    conn.commit()
                    
                    logger.info(f"Retrieved credential for customer {customer_id}, provider {provider}")
                    return dict(result['credentials'])
                else:
                    logger.warning(f"No credential found for customer {customer_id}, provider {provider}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to retrieve credential: {e}", exc_info=True)
            return None
        finally:
            conn.close()
    
    def list_credentials(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        List all credentials for a customer (without decrypting)
        
        Args:
            customer_id: Customer UUID
        
        Returns:
            List of credential metadata (no sensitive data)
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        id,
                        provider,
                        credential_name,
                        credential_type,
                        permissions,
                        is_active,
                        is_verified,
                        last_verified_at,
                        last_used_at,
                        usage_count,
                        created_at,
                        updated_at
                    FROM cloud_credentials
                    WHERE customer_id = %s
                    ORDER BY created_at DESC
                """, (customer_id,))
                
                results = cur.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to list credentials: {e}", exc_info=True)
            return []
        finally:
            conn.close()
    
    def verify_credential(
        self,
        credential_id: str,
        customer_id: str,
        success: bool,
        error_message: Optional[str] = None
    ):
        """
        Update credential verification status
        
        Args:
            credential_id: Credential UUID
            customer_id: Customer UUID
            success: Whether verification succeeded
            error_message: Optional error message if failed
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE cloud_credentials
                    SET is_verified = %s,
                        last_verified_at = CURRENT_TIMESTAMP,
                        verification_error = %s
                    WHERE id = %s AND customer_id = %s
                """, (success, error_message, credential_id, customer_id))
                
                # Log the verification
                action = "verified" if success else "failed"
                self._log_audit(
                    conn,
                    credential_id,
                    customer_id,
                    action,
                    error_message or "Credential verified successfully"
                )
                
                conn.commit()
                logger.info(f"Credential {credential_id} verification: {success}")
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update verification status: {e}", exc_info=True)
        finally:
            conn.close()
    
    def delete_credential(self, credential_id: str, customer_id: str):
        """
        Soft delete a credential (mark as inactive)
        
        Args:
            credential_id: Credential UUID
            customer_id: Customer UUID
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE cloud_credentials
                    SET is_active = false
                    WHERE id = %s AND customer_id = %s
                """, (credential_id, customer_id))
                
                # Log the deletion
                self._log_audit(
                    conn,
                    credential_id,
                    customer_id,
                    "deleted",
                    "Credential marked as inactive"
                )
                
                conn.commit()
                logger.info(f"Credential {credential_id} deleted")
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to delete credential: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def _log_audit(
        self,
        conn,
        credential_id: str,
        customer_id: str,
        action: str,
        details: str
    ):
        """Log credential access to audit log"""
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO credential_audit_log (
                        credential_id,
                        customer_id,
                        action,
                        action_details
                    ) VALUES (%s, %s, %s, %s)
                """, (credential_id, customer_id, action, details))
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")
