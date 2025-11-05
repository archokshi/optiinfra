"""
Recommendation Engine API Routes.

FastAPI endpoints for recommendation generation and management.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from shared.database.connections import get_postgres_cursor
from .dashboard_routes import (
    RecommendationPayload,
    DEFAULT_CUSTOMER_ID as DASHBOARD_DEFAULT_CUSTOMER,
)
from src.recommendations.engine import RecommendationEngine
from src.models.recommendation_engine import RecommendationEngineRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["recommendations"])

DEFAULT_CUSTOMER_ID = DASHBOARD_DEFAULT_CUSTOMER
recommendation_engine = RecommendationEngine()


def _decimal_to_float(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _load_recommendations(  # pragma: no cover - exercised in integration routes
    customer_id: str,
    status: Optional[str] = None,
    recommendation_type: Optional[str] = None,
    min_savings: Optional[float] = None,
) -> List[RecommendationPayload]:
    query = """
        SELECT
            r.id,
            a.type AS agent_type,
            r.type,
            r.title,
            r.description,
            r.estimated_savings,
            r.estimated_improvement,
            r.priority,
            r.status,
            r.created_at,
            r.updated_at,
            r.data
        FROM recommendations r
        JOIN agents a ON r.agent_id = a.id
        WHERE r.customer_id = %s
    """
    filters = [customer_id]
    if status:
        query += " AND LOWER(r.status::text) = LOWER(%s)"
        filters.append(status)
    if recommendation_type:
        query += " AND r.type = %s"
        filters.append(recommendation_type)
    if min_savings is not None:
        query += " AND COALESCE(r.estimated_savings, 0) >= %s"
        filters.append(min_savings)
    query += " ORDER BY r.created_at DESC"

    with get_postgres_cursor(commit=False) as cursor:
        cursor.execute(query, tuple(filters))
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

    risk_map = {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "critical": "high",
    }

    payloads: List[RecommendationPayload] = []
    for row in rows:
        data = dict(zip(columns, row))
        metadata = data.get("data") or {}
        risk = metadata.get("risk_level") or risk_map.get(
            str(data.get("priority") or "").lower(),
            "medium",
        )
        payloads.append(
            RecommendationPayload(
                id=str(data.get("id")),
                agent_type=str(data.get("agent_type") or "").lower(),
                type=data.get("type") or "unknown",
                title=data.get("title") or "",
                description=data.get("description"),
                estimated_savings=_decimal_to_float(data.get("estimated_savings")),
                estimated_improvement=_decimal_to_float(
                    data.get("estimated_improvement")
                ),
                risk_level=risk,
                status=str(data.get("status") or "pending").lower(),
                created_at=(
                    data.get("created_at").isoformat()
                    if data.get("created_at")
                    else datetime.utcnow().isoformat()
                ),
                updated_at=(
                    data.get("updated_at").isoformat()
                    if data.get("updated_at")
                    else None
                ),
            )
        )
    return payloads


def _update_recommendation_status(  # pragma: no cover - exercised in integration routes
    recommendation_id: str,
    new_status: str,
) -> RecommendationPayload:
    query = """
        WITH updated AS (
            UPDATE recommendations
            SET status = %s,
                approved_at = CASE WHEN %s = 'approved' THEN NOW() ELSE NULL END,
                updated_at = NOW()
            WHERE id = %s
            RETURNING *
        )
        SELECT
            u.id,
            a.type AS agent_type,
            u.type,
            u.title,
            u.description,
            u.estimated_savings,
            u.estimated_improvement,
            u.priority,
            u.status,
            u.created_at,
            u.updated_at,
            u.data
        FROM updated u
        JOIN agents a ON u.agent_id = a.id
    """
    with get_postgres_cursor() as cursor:
        cursor.execute(query, (new_status, new_status, recommendation_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()

    data = dict(zip(columns, row))
    metadata = data.get("data") or {}
    risk_map = {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "critical": "high",
    }
    risk = metadata.get("risk_level") or risk_map.get(
        str(data.get("priority") or "").lower(),
        "medium",
    )
    return RecommendationPayload(
        id=str(data.get("id")),
        agent_type=str(data.get("agent_type") or "").lower(),
        type=data.get("type") or "unknown",
        title=data.get("title") or "",
        description=data.get("description"),
        estimated_savings=_decimal_to_float(data.get("estimated_savings")),
        estimated_improvement=_decimal_to_float(data.get("estimated_improvement")),
        risk_level=risk,
        status=str(data.get("status") or new_status).lower(),
        created_at=(
            data.get("created_at").isoformat()
            if data.get("created_at")
            else datetime.utcnow().isoformat()
        ),
        updated_at=(
            data.get("updated_at").isoformat()
            if data.get("updated_at")
            else None
        ),
    )


def _fetch_recommendation_detail(recommendation_id: str) -> RecommendationPayload:
    query = """
        SELECT
            r.id,
            a.type AS agent_type,
            r.type,
            r.title,
            r.description,
            r.estimated_savings,
            r.estimated_improvement,
            r.priority,
            r.status,
            r.created_at,
            r.updated_at,
            r.data
        FROM recommendations r
        JOIN agents a ON r.agent_id = a.id
        WHERE r.id = %s
    """
    with get_postgres_cursor(commit=False) as cursor:
        cursor.execute(query, (recommendation_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()

    data = dict(zip(columns, row))
    metadata = data.get("data") or {}
    risk_map = {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "critical": "high",
    }
    risk = metadata.get("risk_level") or risk_map.get(
        str(data.get("priority") or "").lower(),
        "medium",
    )
    return RecommendationPayload(
        id=str(data.get("id")),
        agent_type=str(data.get("agent_type") or "").lower(),
        type=data.get("type") or "unknown",
        title=data.get("title") or "",
        description=data.get("description"),
        estimated_savings=_decimal_to_float(data.get("estimated_savings")),
        estimated_improvement=_decimal_to_float(data.get("estimated_improvement")),
        risk_level=risk,
        status=str(data.get("status") or "pending").lower(),
        created_at=(
            data.get("created_at").isoformat()
            if data.get("created_at")
            else datetime.utcnow().isoformat()
        ),
        updated_at=(
            data.get("updated_at").isoformat()
            if data.get("updated_at")
            else None
        ),
    )


@router.post("/recommendations/generate", response_model=dict)
async def generate_recommendations(request: RecommendationEngineRequest):
    try:
        logger.info("Generating recommendations for customer %s", request.customer_id)
        request_dict = request.dict()
        response = await recommendation_engine.generate_recommendations(request_dict)
        if not response.get("success"):
            raise HTTPException(
                status_code=500,
                detail=response.get("error_message", "Failed to generate recommendations"),
            )
        return response
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Error generating recommendations: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/recommendations", response_model=List[RecommendationPayload])
async def list_recommendations(
    customer_id: Optional[str] = Query(None, description="Customer identifier"),
    status: Optional[str] = Query(None, description="Filter by status"),
    recommendation_type: Optional[str] = Query(None, description="Filter by type"),
    min_savings: Optional[float] = Query(None, description="Minimum monthly savings"),
):
    active_customer = customer_id or DEFAULT_CUSTOMER_ID
    payloads = await run_in_threadpool(
        _load_recommendations,
        active_customer,
        status,
        recommendation_type,
        min_savings,
    )
    return payloads


@router.get("/recommendations/{customer_id}", response_model=List[RecommendationPayload])
async def get_recommendations(
    customer_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    recommendation_type: Optional[str] = Query(None, description="Filter by type"),
    min_savings: Optional[float] = Query(None, description="Minimum monthly savings"),
):
    return await list_recommendations(
        customer_id=customer_id,
        status=status,
        recommendation_type=recommendation_type,
        min_savings=min_savings,
    )


@router.get("/recommendations/detail/{recommendation_id}", response_model=RecommendationPayload)
async def get_recommendation_detail(recommendation_id: str):
    try:
        return await run_in_threadpool(_fetch_recommendation_detail, recommendation_id)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Error fetching recommendation detail: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/recommendations/{recommendation_id}/approve", response_model=RecommendationPayload)
async def approve_recommendation(recommendation_id: str):
    return await run_in_threadpool(_update_recommendation_status, recommendation_id, "approved")


@router.post("/recommendations/{recommendation_id}/reject", response_model=RecommendationPayload)
async def reject_recommendation(recommendation_id: str):
    return await run_in_threadpool(_update_recommendation_status, recommendation_id, "rejected")


@router.post("/recommendations/{recommendation_id}/implement", response_model=RecommendationPayload)
async def implement_recommendation(
    recommendation_id: str,
    actual_savings: Optional[float] = None,
):
    payload = await run_in_threadpool(_update_recommendation_status, recommendation_id, "completed")
    if actual_savings is not None:
        query = """
            UPDATE recommendations
            SET actual_savings = %s,
                updated_at = NOW()
            WHERE id = %s
        """
        with get_postgres_cursor() as cursor:
            cursor.execute(query, (actual_savings, recommendation_id))
    return payload


@router.get("/recommendations/stats/{customer_id}")
async def get_recommendation_stats(customer_id: str):
    query = """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status = 'pending') AS pending,
            COUNT(*) FILTER (WHERE status = 'approved') AS approved,
            COUNT(*) FILTER (WHERE status = 'rejected') AS rejected,
            COUNT(*) FILTER (WHERE status = 'completed') AS completed,
            COALESCE(SUM(estimated_savings), 0) AS potential_savings,
            COALESCE(SUM(actual_savings), 0) AS realized_savings
        FROM recommendations
        WHERE customer_id = %s
    """
    with get_postgres_cursor(commit=False) as cursor:
        cursor.execute(query, (customer_id,))
        result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")

    total, pending, approved, rejected, completed, potential, realized = result
    implementation_rate = (completed / total * 100) if total else 0.0
    savings_accuracy = ((realized / potential) * 100) if potential else 0.0

    return {
        "customer_id": customer_id,
        "total_recommendations": total,
        "pending_recommendations": pending,
        "approved_recommendations": approved,
        "rejected_recommendations": rejected,
        "completed_recommendations": completed,
        "total_potential_savings": _decimal_to_float(potential) or 0.0,
        "total_realized_savings": _decimal_to_float(realized) or 0.0,
        "implementation_rate": implementation_rate,
        "savings_accuracy": savings_accuracy,
    }
