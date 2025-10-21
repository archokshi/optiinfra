package coordination

import (
	"fmt"
	"log"
	"time"

	"github.com/google/uuid"
)

// Coordinator is the main coordination engine
type Coordinator struct {
	conflictDetector *ConflictDetector
	conflictResolver *ConflictResolver
	approvalManager  *ApprovalManager
	executionOrch    *ExecutionOrchestrator
}

// NewCoordinator creates a new coordinator
func NewCoordinator() *Coordinator {
	return &Coordinator{
		conflictDetector: NewConflictDetector(),
		conflictResolver: NewConflictResolver(),
		approvalManager:  NewApprovalManager(),
		executionOrch:    NewExecutionOrchestrator(),
	}
}

// Coordinate coordinates multiple recommendations
func (c *Coordinator) Coordinate(req *CoordinationRequest) (*CoordinationResponse, error) {
	log.Printf("Coordinating %d recommendations for customer %s",
		len(req.Recommendations), req.CustomerID)

	startTime := time.Now()

	// Step 1: Detect conflicts
	conflicts := c.conflictDetector.DetectConflicts(req.Recommendations)

	// Step 2: Resolve conflicts
	resolvedRecs, resolvedConflicts := c.conflictResolver.ResolveConflicts(
		req.Recommendations,
		conflicts,
	)

	// Step 3: Request approvals
	approvals := make([]Approval, 0)
	autoApprovedCount := 0

	for _, rec := range resolvedRecs {
		if req.AutoApprove && c.approvalManager.AutoApprove(rec) {
			autoApprovedCount++
			rec.Status = "approved"
		} else {
			approval := c.approvalManager.RequestApproval(rec)
			if approval != nil {
				approvals = append(approvals, *approval)
				rec.Status = "pending_approval"
			} else {
				// No approval needed (low risk)
				autoApprovedCount++
				rec.Status = "approved"
			}
		}
	}

	// Step 4: Create execution plans (if execute_now flag is set)
	executionPlans := make([]ExecutionPlan, 0)
	
	if req.ExecuteNow {
		for _, rec := range resolvedRecs {
			if rec.Status == "approved" {
				plan := c.executionOrch.CreateExecutionPlan(rec)
				executionPlans = append(executionPlans, *plan)
				
				// Execute asynchronously
				go func(planID string) {
					if err := c.executionOrch.ExecutePlan(planID); err != nil {
						log.Printf("Execution failed for plan %s: %v", planID, err)
					}
				}(plan.ID)
			}
		}
	}

	// Build response
	response := &CoordinationResponse{
		ID:                   uuid.New().String(),
		TotalRecommendations: len(req.Recommendations),
		ConflictsDetected:    len(conflicts),
		ConflictsResolved:    len(resolvedConflicts),
		RecommendationsKept:  len(resolvedRecs),
		ApprovalsRequired:    len(approvals),
		AutoApproved:         autoApprovedCount,
		Conflicts:            resolvedConflicts,
		Recommendations:      resolvedRecs,
		Approvals:            approvals,
		ExecutionPlans:       executionPlans,
		CreatedAt:            time.Now(),
	}

	duration := time.Since(startTime)
	log.Printf("Coordination completed in %dms: %d recommendations → %d kept, %d conflicts resolved, %d approvals needed",
		duration.Milliseconds(),
		response.TotalRecommendations,
		response.RecommendationsKept,
		response.ConflictsResolved,
		response.ApprovalsRequired)

	return response, nil
}

// ApproveRecommendation approves a pending recommendation
func (c *Coordinator) ApproveRecommendation(approvalID string, userID string) error {
	// Process approval
	if err := c.approvalManager.ProcessApproval(
		approvalID,
		ApprovalStatusApproved,
		userID,
		"",
	); err != nil {
		return fmt.Errorf("failed to approve: %w", err)
	}

	// Get approval to find recommendation
	approval, err := c.approvalManager.GetApproval(approvalID)
	if err != nil {
		return fmt.Errorf("failed to get approval: %w", err)
	}

	log.Printf("Recommendation %s approved, creating execution plan", approval.RecommendationID)

	// TODO: Get recommendation and create execution plan
	// For now, just log
	log.Printf("Execution plan creation triggered for recommendation %s", approval.RecommendationID)

	return nil
}

// RejectRecommendation rejects a pending recommendation
func (c *Coordinator) RejectRecommendation(approvalID string, userID string, reason string) error {
	return c.approvalManager.ProcessApproval(
		approvalID,
		ApprovalStatusRejected,
		userID,
		reason,
	)
}

// GetPendingApprovals returns pending approvals for a customer
func (c *Coordinator) GetPendingApprovals(customerID string) []*Approval {
	return c.approvalManager.ListPendingApprovals(customerID)
}

// GetExecutionPlan returns an execution plan
func (c *Coordinator) GetExecutionPlan(planID string) (*ExecutionPlan, error) {
	return c.executionOrch.GetPlan(planID)
}

// ExecutePlan executes an approved execution plan
func (c *Coordinator) ExecutePlan(planID string) error {
	return c.executionOrch.ExecutePlan(planID)
}
