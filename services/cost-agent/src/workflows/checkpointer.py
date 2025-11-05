"""
PostgreSQL Checkpointer for LangGraph

Provides state persistence and workflow resume capability using PostgreSQL.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Try to import psycopg2, but make it optional for validation
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

# Import LangGraph checkpointing (compatible with installed version)
try:
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.checkpoint.base import Checkpoint
    CheckpointMetadata = Dict[str, Any]  # Use dict for metadata
except ImportError:
    # Fallback for older versions
    BaseCheckpointSaver = object
    Checkpoint = Dict[str, Any]
    CheckpointMetadata = Dict[str, Any]


class PostgreSQLCheckpointer(BaseCheckpointSaver):
    """
    PostgreSQL-based checkpoint saver for LangGraph workflows
    
    Stores workflow state in PostgreSQL for persistence and resume capability.
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize PostgreSQL checkpointer
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string
        self.logger = logging.getLogger(__name__)
        self._ensure_table_exists()
    
    def _get_connection(self):
        """Get PostgreSQL connection"""
        return psycopg2.connect(self.connection_string)
    
    def _ensure_table_exists(self):
        """Create checkpoints table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS workflow_checkpoints (
            id SERIAL PRIMARY KEY,
            workflow_id VARCHAR(255) NOT NULL,
            checkpoint_id VARCHAR(255) NOT NULL,
            parent_checkpoint_id VARCHAR(255),
            state JSONB NOT NULL,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(workflow_id, checkpoint_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_workflow_checkpoints_workflow_id 
        ON workflow_checkpoints(workflow_id);
        
        CREATE INDEX IF NOT EXISTS idx_workflow_checkpoints_checkpoint_id 
        ON workflow_checkpoints(checkpoint_id);
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(create_table_sql)
                    conn.commit()
            self.logger.info("Checkpoint table ensured")
        except Exception as e:
            self.logger.error(f"Failed to create checkpoint table: {str(e)}")
            raise
    
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata
    ) -> None:
        """
        Save a checkpoint to PostgreSQL
        
        Args:
            config: Configuration dict with workflow_id
            checkpoint: Checkpoint data to save
            metadata: Checkpoint metadata
        """
        workflow_id = config.get('configurable', {}).get('thread_id', 'unknown')
        checkpoint_id = checkpoint.get('id', str(datetime.utcnow().timestamp()))
        parent_checkpoint_id = checkpoint.get('parent_id')
        
        state_json = json.dumps(checkpoint.get('channel_values', {}))
        metadata_json = json.dumps(metadata or {})
        
        insert_sql = """
        INSERT INTO workflow_checkpoints 
        (workflow_id, checkpoint_id, parent_checkpoint_id, state, metadata)
        VALUES (%s, %s, %s, %s::jsonb, %s::jsonb)
        ON CONFLICT (workflow_id, checkpoint_id) 
        DO UPDATE SET 
            state = EXCLUDED.state,
            metadata = EXCLUDED.metadata,
            created_at = CURRENT_TIMESTAMP
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        insert_sql,
                        (workflow_id, checkpoint_id, parent_checkpoint_id, state_json, metadata_json)
                    )
                    conn.commit()
            self.logger.debug(f"Saved checkpoint {checkpoint_id} for workflow {workflow_id}")
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {str(e)}")
            raise
    
    def get(
        self,
        config: Dict[str, Any]
    ) -> Optional[Checkpoint]:
        """
        Retrieve the latest checkpoint for a workflow
        
        Args:
            config: Configuration dict with workflow_id
            
        Returns:
            Latest checkpoint or None
        """
        workflow_id = config.get('configurable', {}).get('thread_id')
        
        if not workflow_id:
            return None
        
        select_sql = """
        SELECT checkpoint_id, parent_checkpoint_id, state, metadata, created_at
        FROM workflow_checkpoints
        WHERE workflow_id = %s
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(select_sql, (workflow_id,))
                    row = cur.fetchone()
                    
                    if row:
                        return Checkpoint(
                            id=row['checkpoint_id'],
                            parent_id=row['parent_checkpoint_id'],
                            channel_values=json.loads(row['state']),
                            metadata=json.loads(row['metadata']) if row['metadata'] else {}
                        )
                    return None
        except Exception as e:
            self.logger.error(f"Failed to retrieve checkpoint: {str(e)}")
            return None
    
    def list(
        self,
        config: Dict[str, Any],
        limit: int = 10
    ) -> list:
        """
        List checkpoints for a workflow
        
        Args:
            config: Configuration dict with workflow_id
            limit: Maximum number of checkpoints to return
            
        Returns:
            List of checkpoints
        """
        workflow_id = config.get('configurable', {}).get('thread_id')
        
        if not workflow_id:
            return []
        
        select_sql = """
        SELECT checkpoint_id, parent_checkpoint_id, state, metadata, created_at
        FROM workflow_checkpoints
        WHERE workflow_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(select_sql, (workflow_id, limit))
                    rows = cur.fetchall()
                    
                    return [
                        Checkpoint(
                            id=row['checkpoint_id'],
                            parent_id=row['parent_checkpoint_id'],
                            channel_values=json.loads(row['state']),
                            metadata=json.loads(row['metadata']) if row['metadata'] else {}
                        )
                        for row in rows
                    ]
        except Exception as e:
            self.logger.error(f"Failed to list checkpoints: {str(e)}")
            return []
    
    def delete(self, config: Dict[str, Any]) -> None:
        """
        Delete all checkpoints for a workflow
        
        Args:
            config: Configuration dict with workflow_id
        """
        workflow_id = config.get('configurable', {}).get('thread_id')
        
        if not workflow_id:
            return
        
        delete_sql = "DELETE FROM workflow_checkpoints WHERE workflow_id = %s"
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(delete_sql, (workflow_id,))
                    conn.commit()
            self.logger.info(f"Deleted checkpoints for workflow {workflow_id}")
        except Exception as e:
            self.logger.error(f"Failed to delete checkpoints: {str(e)}")
            raise


def create_checkpointer(connection_string: str) -> PostgreSQLCheckpointer:
    """
    Factory function to create a PostgreSQL checkpointer
    
    Args:
        connection_string: PostgreSQL connection string
        
    Returns:
        PostgreSQLCheckpointer instance
    """
    return PostgreSQLCheckpointer(connection_string)
