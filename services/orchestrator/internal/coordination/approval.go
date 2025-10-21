package coordination

import (
	"fmt"
	"log"
	"time"

	"github.com/google/uuid"
)

const (
	// Approval expiration times
	approvalExpirationLow      = 7 * 24 * time.Hour // 7 days
	approvalExpirationMedium   = 48 * time.Hour     // 2 days
	approvalExpirationHigh     = 24 * time.Hour     // 1 day
	approvalExpirationCritical = 4 * time.Hour      // 4 hours
)

// ApprovalManager manages approval workflows
type ApprovalManager struct {
	approvals map[string]*Approval // In-memory storage (should be PostgreSQL in production)
}

// NewApprovalManager creates a new approval manager
func NewApprovalManager() *ApprovalManager {
	return &ApprovalManager{
		approvals: make(map[string]*Approval),
	}
}

// RequestApproval creates an approval request for a recommendation
func (am *ApprovalManager) RequestApproval(rec *Recommendation) *Approval {
	// Determine if approval is needed based on risk level
	if !am.requiresApproval(rec.RiskLevel) {
		log.Printf("Recommendation %s does not require approval (risk: %s)", rec.ID, rec.RiskLevel)
		return nil
	}

	// Create approval
	approval := &Approval{
		ID:               uuid.New().String(),
		RecommendationID: rec.ID,
		CustomerID:       rec.CustomerID,
		RiskLevel:        rec.RiskLevel,
		Status:           ApprovalStatusPending,
		RequestedBy:      rec.AgentID,
		RequestedAt:      time.Now(),
		ExpiresAt:        am.calculateExpiration(rec.RiskLevel),
	}

	// Store approval
	am.approvals[approval.ID] = approval

	log.Printf("Approval requested: %s for recommendation %s (risk: %s, expires: %s)",
		approval.ID, rec.ID, rec.RiskLevel, approval.ExpiresAt.Format(time.RFC3339))

	return approval
}

// ProcessApproval processes an approval decision
func (am *ApprovalManager) ProcessApproval(approvalID string, status ApprovalStatus, userID string, reason string) error {
	approval, ok := am.approvals[approvalID]
	if !ok {
		return fmt.Errorf("approval not found: %s", approvalID)
	}

	// Check if already processed
	if approval.Status != ApprovalStatusPending {
		return fmt.Errorf("approval already processed: %s (status: %s)", approvalID, approval.Status)
	}

	// Check if expired
	if time.Now().After(approval.ExpiresAt) {
		approval.Status = ApprovalStatusExpired
		return fmt.Errorf("approval expired: %s", approvalID)
	}

	// Update approval
	now := time.Now()
	approval.Status = status

	if status == ApprovalStatusApproved {
		approval.ApprovedBy = userID
		approval.ApprovedAt = &now
		log.Printf("Approval APPROVED: %s by %s", approvalID, userID)
	} else if status == ApprovalStatusRejected {
		approval.RejectedBy = userID
		approval.RejectedAt = &now
		approval.RejectionReason = reason
		log.Printf("Approval REJECTED: %s by %s (reason: %s)", approvalID, userID, reason)
	}

	return nil
}

// GetApproval retrieves an approval by ID
func (am *ApprovalManager) GetApproval(approvalID string) (*Approval, error) {
	approval, ok := am.approvals[approvalID]
	if !ok {
		return nil, fmt.Errorf("approval not found: %s", approvalID)
	}
	return approval, nil
}

// ListPendingApprovals returns all pending approvals for a customer
func (am *ApprovalManager) ListPendingApprovals(customerID string) []*Approval {
	pending := make([]*Approval, 0)
	
	for _, approval := range am.approvals {
		if approval.CustomerID == customerID && approval.Status == ApprovalStatusPending {
			// Check if not expired
			if time.Now().Before(approval.ExpiresAt) {
				pending = append(pending, approval)
			} else {
				// Mark as expired
				approval.Status = ApprovalStatusExpired
			}
		}
	}

	return pending
}

// AutoApprove automatically approves low-risk recommendations
func (am *ApprovalManager) AutoApprove(rec *Recommendation) bool {
	// Only auto-approve low-risk items
	if rec.RiskLevel != RiskLevelLow {
		return false
	}

	log.Printf("Auto-approved recommendation %s (risk: %s)", rec.ID, rec.RiskLevel)
	return true
}

// Helper methods
func (am *ApprovalManager) requiresApproval(riskLevel RiskLevel) bool {
	// Low risk: No approval needed
	// Medium: Approval needed
	// High: Approval needed
	// Critical: Multi-approval needed (future enhancement)
	return riskLevel != RiskLevelLow
}

func (am *ApprovalManager) calculateExpiration(riskLevel RiskLevel) time.Time {
	now := time.Now()
	
	switch riskLevel {
	case RiskLevelLow:
		return now.Add(approvalExpirationLow)
	case RiskLevelMedium:
		return now.Add(approvalExpirationMedium)
	case RiskLevelHigh:
		return now.Add(approvalExpirationHigh)
	case RiskLevelCritical:
		return now.Add(approvalExpirationCritical)
	default:
		return now.Add(approvalExpirationMedium)
	}
}
