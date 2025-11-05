"""
Vultr billing data collector.
Collects invoices, pending charges, and cost breakdowns.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from .client import VultrClient

logger = logging.getLogger(__name__)


class VultrBillingCollector:
    """
    Collects billing data from Vultr API.
    """
    
    def __init__(self, client: VultrClient):
        """
        Initialize billing collector.
        
        Args:
            client: Configured VultrClient instance
        """
        self.client = client
    
    def collect_account_info(self) -> Dict[str, Any]:
        """
        Collect account information including balance.
        
        Returns:
            Account information dict
        """
        try:
            account = self.client.get_account_info()
            
            return {
                "account_id": account.get("account", {}).get("name", "unknown"),
                "email": account.get("account", {}).get("email"),
                "balance": float(account.get("account", {}).get("balance", 0)),
                "pending_charges": float(
                    account.get("account", {}).get("pending_charges", 0)
                ),
                "last_payment_date": account.get("account", {}).get(
                    "last_payment_date"
                ),
                "last_payment_amount": float(
                    account.get("account", {}).get("last_payment_amount", 0)
                ),
            }
            
        except Exception as e:
            logger.error(f"Failed to collect account info: {e}")
            raise
    
    def collect_pending_charges(self) -> Dict[str, Any]:
        """
        Collect current month's pending charges.
        
        Returns:
            Pending charges breakdown
        """
        try:
            charges = self.client.get_pending_charges()
            
            billing_info = charges.get("billing", {})
            
            return {
                "pending_charges": float(
                    billing_info.get("pending_charges", 0)
                ),
                "currency": "USD",  # Vultr bills in USD
                "billing_period_start": billing_info.get("billing_period_start"),
                "billing_period_end": billing_info.get("billing_period_end"),
            }
            
        except Exception as e:
            logger.error(f"Failed to collect pending charges: {e}")
            raise
    
    def collect_invoices(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Collect invoices within date range.
        
        Args:
            start_date: Start date (default: 90 days ago)
            end_date: End date (default: now)
        
        Returns:
            List of invoice summaries
        """
        if not start_date:
            from datetime import timezone
            start_date = datetime.now(timezone.utc) - timedelta(days=90)
        if not end_date:
            from datetime import timezone
            end_date = datetime.now(timezone.utc)
        
        try:
            invoices = self.client.list_invoices()
            
            # Filter by date
            filtered_invoices = []
            for invoice in invoices:
                invoice_date = datetime.fromisoformat(
                    invoice.get("date", "").replace("Z", "+00:00")
                )
                if start_date <= invoice_date <= end_date:
                    filtered_invoices.append({
                        "invoice_id": invoice.get("id"),
                        "date": invoice.get("date"),
                        "description": invoice.get("description"),
                        "amount": float(invoice.get("amount", 0)),
                        "balance": float(invoice.get("balance", 0)),
                    })
            
            logger.info(
                f"Collected {len(filtered_invoices)} invoices "
                f"from {start_date} to {end_date}"
            )
            return filtered_invoices
            
        except Exception as e:
            logger.error(f"Failed to collect invoices: {e}")
            raise
    
    def collect_invoice_details(
        self,
        invoice_id: str
    ) -> Dict[str, Any]:
        """
        Collect detailed line items for a specific invoice.
        
        Args:
            invoice_id: Invoice ID
        
        Returns:
            Invoice details with line items
        """
        try:
            # Get invoice overview
            invoice = self.client.get_invoice(invoice_id)
            
            # Get line items
            items = self.client.get_invoice_items(invoice_id)
            
            # Group by product type
            product_costs = {}
            for item in items:
                product = item.get("product", "unknown")
                amount = float(item.get("total", 0))
                
                if product not in product_costs:
                    product_costs[product] = {
                        "product": product,
                        "total_cost": 0,
                        "items": []
                    }
                
                product_costs[product]["total_cost"] += amount
                product_costs[product]["items"].append({
                    "description": item.get("description"),
                    "start_date": item.get("start_date"),
                    "end_date": item.get("end_date"),
                    "units": item.get("units"),
                    "unit_type": item.get("unit_type"),
                    "unit_price": float(item.get("unit_price", 0)),
                    "total": amount
                })
            
            return {
                "invoice_id": invoice_id,
                "date": invoice.get("invoice", {}).get("date"),
                "total_amount": float(
                    invoice.get("invoice", {}).get("amount", 0)
                ),
                "product_breakdown": list(product_costs.values()),
            }
            
        except Exception as e:
            logger.error(f"Failed to collect invoice details: {e}")
            raise
    
    def analyze_spending_patterns(
        self,
        invoices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze spending patterns from invoices.
        
        Args:
            invoices: List of invoice summaries
        
        Returns:
            Spending analysis
        """
        if not invoices:
            return {
                "total_spend": 0,
                "average_monthly": 0,
                "trend": "unknown"
            }
        
        # Calculate totals
        total_spend = sum(inv["amount"] for inv in invoices)
        
        # Calculate monthly average
        date_range_days = (
            datetime.fromisoformat(invoices[0]["date"].replace("Z", "+00:00")) -
            datetime.fromisoformat(invoices[-1]["date"].replace("Z", "+00:00"))
        ).days
        months = max(date_range_days / 30, 1)
        average_monthly = total_spend / months
        
        # Determine trend (simple: compare first half vs second half)
        mid_point = len(invoices) // 2
        first_half_avg = sum(
            inv["amount"] for inv in invoices[:mid_point]
        ) / max(mid_point, 1)
        second_half_avg = sum(
            inv["amount"] for inv in invoices[mid_point:]
        ) / max(len(invoices) - mid_point, 1)
        
        if second_half_avg > first_half_avg * 1.1:
            trend = "increasing"
        elif second_half_avg < first_half_avg * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "total_spend": total_spend,
            "average_monthly": average_monthly,
            "invoice_count": len(invoices),
            "trend": trend,
            "trend_percentage": (
                (second_half_avg - first_half_avg) / first_half_avg * 100
                if first_half_avg > 0 else 0
            )
        }
