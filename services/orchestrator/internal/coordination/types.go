package coordination

import (
	"time"
)

// RecommendationType represents the type of optimization recommendation
type RecommendationType string

const (
	RecommendationTypeCost        RecommendationType = "cost"
	RecommendationTypePerformance RecommendationType = "performance"
	RecommendationTypeResource    RecommendationType = "resource"
	RecommendationTypeApplication RecommendationType = "application"
)

// RiskLevel represents the risk level of a recommendation
type RiskLevel string

const (
	RiskLevelLow      RiskLevel = "low"
	RiskLevelMedium   RiskLevel = "medium"
	RiskLevelHigh     RiskLevel = "high"
	RiskLevelCritical RiskLevel = "critical"
)

// ApprovalStatus represents the approval state
type ApprovalStatus string

const (
	ApprovalStatusPending  ApprovalStatus = "pending"
	ApprovalStatusApproved ApprovalStatus = "approved"
	ApprovalStatusRejected ApprovalStatus = "rejected"
	ApprovalStatusExpired  ApprovalStatus = "expired"
)

// ExecutionStatus represents the execution state
type ExecutionStatus string

const (
	ExecutionStatusPending    ExecutionStatus = "pending"
	ExecutionStatusRunning    ExecutionStatus = "running"
	ExecutionStatusCompleted  ExecutionStatus = "completed"
	ExecutionStatusFailed     ExecutionStatus = "failed"
	ExecutionStatusRolledBack ExecutionStatus = "rolled_back"
)

// ConflictType represents the type of conflict
type ConflictType string

const (
	ConflictTypeResource   ConflictType = "resource"    // Same resource affected
	ConflictTypeAction     ConflictType = "action"      // Contradictory actions
	ConflictTypeDependency ConflictType = "dependency"  // Dependency violation
	ConflictTypeTiming     ConflictType = "timing"      // Timing conflict
)

// Recommendation represents an optimization recommendation from an agent
type Recommendation struct {
	ID                string                 `json:"id"`
	AgentID           string                 `json:"agent_id"`
	AgentType         string                 `json:"agent_type"`
	CustomerID        string                 `json:"customer_id"`
	Type              RecommendationType     `json:"type"`
	Title             string                 `json:"title"`
	Description       string                 `json:"description"`
	Action            string                 `json:"action"`
	RiskLevel         RiskLevel              `json:"risk_level"`
	EstimatedSavings  float64                `json:"estimated_savings"`
	EstimatedImpact   string                 `json:"estimated_impact"`
	AffectedResources []string               `json:"affected_resources"`
	Parameters        map[string]interface{} `json:"parameters"`
	Dependencies      []string               `json:"dependencies"` // IDs of recommendations that must execute first
	Priority          int                    `json:"priority"`     // Higher = more important
	Confidence        float64                `json:"confidence"`   // 0-1 score
	CreatedAt         time.Time              `json:"created_at"`
	ExpiresAt         *time.Time             `json:"expires_at,omitempty"`
	Status            string                 `json:"status"`
	Metadata          map[string]interface{} `json:"metadata,omitempty"`
}

// Conflict represents a conflict between recommendations
type Conflict struct {
	ID               string       `json:"id"`
	Type             ConflictType `json:"type"`
	Recommendations  []string     `json:"recommendation_ids"` // IDs of conflicting recommendations
	Description      string       `json:"description"`
	Severity         string       `json:"severity"` // low, medium, high
	ConflictingField string       `json:"conflicting_field"`
	DetectedAt       time.Time    `json:"detected_at"`
	Resolved         bool         `json:"resolved"`
	Resolution       string       `json:"resolution,omitempty"`
	ResolvedAt       *time.Time   `json:"resolved_at,omitempty"`
}

// Approval represents an approval request for a recommendation
type Approval struct {
	ID               string         `json:"id"`
	RecommendationID string         `json:"recommendation_id"`
	CustomerID       string         `json:"customer_id"`
	RiskLevel        RiskLevel      `json:"risk_level"`
	Status           ApprovalStatus `json:"status"`
	RequestedBy      string         `json:"requested_by"` // Agent ID
	RequestedAt      time.Time      `json:"requested_at"`
	ApprovedBy       string         `json:"approved_by,omitempty"`
	ApprovedAt       *time.Time     `json:"approved_at,omitempty"`
	RejectedBy       string         `json:"rejected_by,omitempty"`
	RejectedAt       *time.Time     `json:"rejected_at,omitempty"`
	RejectionReason  string         `json:"rejection_reason,omitempty"`
	ExpiresAt        time.Time      `json:"expires_at"`
	Notes            string         `json:"notes,omitempty"`
}

// ExecutionStep represents a single step in an execution plan
type ExecutionStep struct {
	ID           string                 `json:"id"`
	Action       string                 `json:"action"`
	AgentID      string                 `json:"agent_id"`
	Parameters   map[string]interface{} `json:"parameters"`
	Critical     bool                   `json:"critical"`      // If true, failure causes rollback
	Reversible   bool                   `json:"reversible"`    // Can this step be rolled back?
	Status       ExecutionStatus        `json:"status"`
	Result       map[string]interface{} `json:"result,omitempty"`
	Error        string                 `json:"error,omitempty"`
	StartedAt    *time.Time             `json:"started_at,omitempty"`
	CompletedAt  *time.Time             `json:"completed_at,omitempty"`
	Duration     int                    `json:"duration_ms"`
	RollbackData map[string]interface{} `json:"rollback_data,omitempty"` // Data needed for rollback
}

// ExecutionPlan represents a multi-step execution plan
type ExecutionPlan struct {
	ID               string                 `json:"id"`
	RecommendationID string                 `json:"recommendation_id"`
	CustomerID       string                 `json:"customer_id"`
	Steps            []ExecutionStep        `json:"steps"`
	Status           ExecutionStatus        `json:"status"`
	CurrentStep      int                    `json:"current_step"`
	CreatedAt        time.Time              `json:"created_at"`
	StartedAt        *time.Time             `json:"started_at,omitempty"`
	CompletedAt      *time.Time             `json:"completed_at,omitempty"`
	RolledBackAt     *time.Time             `json:"rolled_back_at,omitempty"`
	TotalDuration    int                    `json:"total_duration_ms"`
	Metadata         map[string]interface{} `json:"metadata,omitempty"`
}

// CoordinationRequest represents a request to coordinate multiple recommendations
type CoordinationRequest struct {
	CustomerID      string            `json:"customer_id" binding:"required"`
	Recommendations []*Recommendation `json:"recommendations" binding:"required"`
	AutoApprove     bool              `json:"auto_approve"`      // Auto-approve low-risk items
	ExecuteNow      bool              `json:"execute_now"`       // Execute immediately after approval
}

// CoordinationResponse represents the result of coordination
type CoordinationResponse struct {
	ID                   string            `json:"id"`
	TotalRecommendations int               `json:"total_recommendations"`
	ConflictsDetected    int               `json:"conflicts_detected"`
	ConflictsResolved    int               `json:"conflicts_resolved"`
	RecommendationsKept  int               `json:"recommendations_kept"`
	ApprovalsRequired    int               `json:"approvals_required"`
	AutoApproved         int               `json:"auto_approved"`
	Conflicts            []Conflict        `json:"conflicts,omitempty"`
	Recommendations      []*Recommendation `json:"recommendations"`
	Approvals            []Approval        `json:"approvals"`
	ExecutionPlans       []ExecutionPlan   `json:"execution_plans,omitempty"`
	CreatedAt            time.Time         `json:"created_at"`
}
