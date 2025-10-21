package coordination

import (
	"fmt"
	"log"
	"time"

	"github.com/google/uuid"
)

// ExecutionOrchestrator orchestrates multi-step executions
type ExecutionOrchestrator struct {
	plans map[string]*ExecutionPlan // In-memory storage
}

// NewExecutionOrchestrator creates a new execution orchestrator
func NewExecutionOrchestrator() *ExecutionOrchestrator {
	return &ExecutionOrchestrator{
		plans: make(map[string]*ExecutionPlan),
	}
}

// CreateExecutionPlan creates an execution plan from a recommendation
func (eo *ExecutionOrchestrator) CreateExecutionPlan(rec *Recommendation) *ExecutionPlan {
	plan := &ExecutionPlan{
		ID:               uuid.New().String(),
		RecommendationID: rec.ID,
		CustomerID:       rec.CustomerID,
		Steps:            eo.generateSteps(rec),
		Status:           ExecutionStatusPending,
		CurrentStep:      0,
		CreatedAt:        time.Now(),
	}

	eo.plans[plan.ID] = plan

	log.Printf("Created execution plan %s for recommendation %s with %d steps",
		plan.ID, rec.ID, len(plan.Steps))

	return plan
}

// ExecutePlan executes an execution plan
func (eo *ExecutionOrchestrator) ExecutePlan(planID string) error {
	plan, ok := eo.plans[planID]
	if !ok {
		return fmt.Errorf("plan not found: %s", planID)
	}

	// Check if already running or completed
	if plan.Status == ExecutionStatusRunning {
		return fmt.Errorf("plan already running: %s", planID)
	}
	if plan.Status == ExecutionStatusCompleted {
		return fmt.Errorf("plan already completed: %s", planID)
	}

	log.Printf("Executing plan %s (%d steps)", planID, len(plan.Steps))

	// Update plan status
	plan.Status = ExecutionStatusRunning
	now := time.Now()
	plan.StartedAt = &now

	// Execute each step
	for i := 0; i < len(plan.Steps); i++ {
		step := &plan.Steps[i]
		plan.CurrentStep = i

		log.Printf("Executing step %d/%d: %s", i+1, len(plan.Steps), step.Action)

		// Execute step
		if err := eo.executeStep(step); err != nil {
			log.Printf("Step %d failed: %v", i+1, err)

			// If critical step failed, rollback
			if step.Critical {
				log.Printf("Critical step failed, rolling back...")
				eo.rollbackPlan(plan, i)
				plan.Status = ExecutionStatusRolledBack
				return fmt.Errorf("critical step failed: %w", err)
			}

			// Non-critical step: log and continue
			log.Printf("Non-critical step failed, continuing...")
			step.Status = ExecutionStatusFailed
			step.Error = err.Error()
			continue
		}

		step.Status = ExecutionStatusCompleted
	}

	// All steps completed
	plan.Status = ExecutionStatusCompleted
	completedAt := time.Now()
	plan.CompletedAt = &completedAt
	plan.TotalDuration = int(completedAt.Sub(*plan.StartedAt).Milliseconds())

	log.Printf("Plan %s completed successfully (duration: %dms)", planID, plan.TotalDuration)

	return nil
}

// executeStep executes a single step
func (eo *ExecutionOrchestrator) executeStep(step *ExecutionStep) error {
	startTime := time.Now()
	step.Status = ExecutionStatusRunning
	step.StartedAt = &startTime

	// Simulate execution (in production, this would call agent APIs)
	// For now, we'll simulate with a simple action-based logic
	switch step.Action {
	case "take_snapshot":
		// Simulate snapshot creation
		time.Sleep(500 * time.Millisecond)
		step.Result = map[string]interface{}{
			"snapshot_id": fmt.Sprintf("snap-%s", uuid.New().String()[:8]),
			"size_gb":     100,
		}
		step.RollbackData = map[string]interface{}{
			"snapshot_id": step.Result["snapshot_id"],
		}

	case "scale_resources":
		// Simulate scaling
		time.Sleep(1 * time.Second)
		step.Result = map[string]interface{}{
			"previous_count": 5,
			"new_count":      3,
			"scaled_down":    2,
		}
		step.RollbackData = map[string]interface{}{
			"restore_count": 5,
		}

	case "migrate_workload":
		// Simulate migration
		time.Sleep(2 * time.Second)
		step.Result = map[string]interface{}{
			"migrated_instances": 3,
			"status":             "completed",
		}

	case "validate_quality":
		// Simulate validation
		time.Sleep(500 * time.Millisecond)
		step.Result = map[string]interface{}{
			"quality_score": 0.95,
			"passed":        true,
		}

	default:
		return fmt.Errorf("unknown action: %s", step.Action)
	}

	// Update step timing
	completedAt := time.Now()
	step.CompletedAt = &completedAt
	step.Duration = int(completedAt.Sub(startTime).Milliseconds())

	log.Printf("Step completed: %s (duration: %dms)", step.Action, step.Duration)

	return nil
}

// rollbackPlan rolls back executed steps
func (eo *ExecutionOrchestrator) rollbackPlan(plan *ExecutionPlan, failedStepIndex int) {
	log.Printf("Rolling back plan %s (failed at step %d)", plan.ID, failedStepIndex)

	// Roll back in reverse order
	for i := failedStepIndex - 1; i >= 0; i-- {
		step := &plan.Steps[i]

		// Only roll back reversible steps
		if !step.Reversible {
			log.Printf("Step %d (%s) is not reversible, skipping", i+1, step.Action)
			continue
		}

		// Skip steps that didn't complete
		if step.Status != ExecutionStatusCompleted {
			continue
		}

		log.Printf("Rolling back step %d: %s", i+1, step.Action)

		if err := eo.rollbackStep(step); err != nil {
			log.Printf("Failed to rollback step %d: %v", i+1, err)
			// Continue rolling back other steps
		}
	}

	now := time.Now()
	plan.RolledBackAt = &now
}

// rollbackStep rolls back a single step
func (eo *ExecutionOrchestrator) rollbackStep(step *ExecutionStep) error {
	// Simulate rollback (in production, this would call agent APIs)
	switch step.Action {
	case "take_snapshot":
		// Delete snapshot
		log.Printf("Deleting snapshot: %v", step.RollbackData["snapshot_id"])
		time.Sleep(200 * time.Millisecond)

	case "scale_resources":
		// Restore original scale
		log.Printf("Restoring scale to: %v", step.RollbackData["restore_count"])
		time.Sleep(500 * time.Millisecond)

	case "migrate_workload":
		// Migrate back
		log.Printf("Migrating workload back to original location")
		time.Sleep(1 * time.Second)

	default:
		log.Printf("No rollback action defined for: %s", step.Action)
	}

	return nil
}

// GetPlan retrieves an execution plan
func (eo *ExecutionOrchestrator) GetPlan(planID string) (*ExecutionPlan, error) {
	plan, ok := eo.plans[planID]
	if !ok {
		return nil, fmt.Errorf("plan not found: %s", planID)
	}
	return plan, nil
}

// generateSteps generates execution steps based on recommendation type
func (eo *ExecutionOrchestrator) generateSteps(rec *Recommendation) []ExecutionStep {
	steps := make([]ExecutionStep, 0)

	// Generate steps based on action type
	switch rec.Action {
	case "migrate_to_spot":
		steps = []ExecutionStep{
			{
				ID:         uuid.New().String(),
				Action:     "take_snapshot",
				AgentID:    rec.AgentID,
				Critical:   true,
				Reversible: true,
				Status:     ExecutionStatusPending,
			},
			{
				ID:         uuid.New().String(),
				Action:     "migrate_workload",
				AgentID:    rec.AgentID,
				Critical:   true,
				Reversible: true,
				Status:     ExecutionStatusPending,
			},
			{
				ID:         uuid.New().String(),
				Action:     "validate_quality",
				AgentID:    "application-agent",
				Critical:   true,
				Reversible: false,
				Status:     ExecutionStatusPending,
			},
		}

	case "scale_down":
		steps = []ExecutionStep{
			{
				ID:         uuid.New().String(),
				Action:     "validate_quality",
				AgentID:    "application-agent",
				Critical:   true,
				Reversible: false,
				Status:     ExecutionStatusPending,
			},
			{
				ID:         uuid.New().String(),
				Action:     "scale_resources",
				AgentID:    rec.AgentID,
				Critical:   true,
				Reversible: true,
				Status:     ExecutionStatusPending,
			},
			{
				ID:         uuid.New().String(),
				Action:     "validate_quality",
				AgentID:    "application-agent",
				Critical:   true,
				Reversible: false,
				Status:     ExecutionStatusPending,
			},
		}

	default:
		// Simple single-step execution
		steps = []ExecutionStep{
			{
				ID:         uuid.New().String(),
				Action:     rec.Action,
				AgentID:    rec.AgentID,
				Parameters: rec.Parameters,
				Critical:   true,
				Reversible: false,
				Status:     ExecutionStatusPending,
			},
		}
	}

	return steps
}
