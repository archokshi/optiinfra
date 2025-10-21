package coordination

import (
	"fmt"
	"log"
	"time"

	"github.com/google/uuid"
)

// ConflictDetector detects conflicts between recommendations
type ConflictDetector struct{}

// NewConflictDetector creates a new conflict detector
func NewConflictDetector() *ConflictDetector {
	return &ConflictDetector{}
}

// DetectConflicts finds conflicts between recommendations
func (cd *ConflictDetector) DetectConflicts(recommendations []*Recommendation) []Conflict {
	conflicts := make([]Conflict, 0)

	// Check each pair of recommendations
	for i := 0; i < len(recommendations); i++ {
		for j := i + 1; j < len(recommendations); j++ {
			rec1 := recommendations[i]
			rec2 := recommendations[j]

			// Check for resource conflicts
			if resourceConflict := cd.checkResourceConflict(rec1, rec2); resourceConflict != nil {
				conflicts = append(conflicts, *resourceConflict)
			}

			// Check for action conflicts
			if actionConflict := cd.checkActionConflict(rec1, rec2); actionConflict != nil {
				conflicts = append(conflicts, *actionConflict)
			}

			// Check for dependency conflicts
			if depConflict := cd.checkDependencyConflict(rec1, rec2); depConflict != nil {
				conflicts = append(conflicts, *depConflict)
			}
		}
	}

	log.Printf("Detected %d conflicts among %d recommendations", len(conflicts), len(recommendations))
	return conflicts
}

// checkResourceConflict checks if two recommendations affect the same resources
func (cd *ConflictDetector) checkResourceConflict(rec1, rec2 *Recommendation) *Conflict {
	commonResources := cd.findCommonResources(rec1.AffectedResources, rec2.AffectedResources)
	
	if len(commonResources) > 0 {
		return &Conflict{
			ID:               uuid.New().String(),
			Type:             ConflictTypeResource,
			Recommendations:  []string{rec1.ID, rec2.ID},
			Description:      fmt.Sprintf("Both recommendations affect resources: %v", commonResources),
			Severity:         cd.calculateSeverity(rec1, rec2),
			ConflictingField: "affected_resources",
			DetectedAt:       time.Now(),
			Resolved:         false,
		}
	}

	return nil
}

// checkActionConflict checks if two recommendations have contradictory actions
func (cd *ConflictDetector) checkActionConflict(rec1, rec2 *Recommendation) *Conflict {
	// Define contradictory action pairs
	contradictory := map[string][]string{
		"scale_up":            {"scale_down", "terminate"},
		"scale_down":          {"scale_up", "add_capacity"},
		"migrate_to_spot":     {"migrate_to_on_demand", "reserve_instances"},
		"increase_batch_size": {"decrease_batch_size"},
		"enable_caching":      {"disable_caching"},
	}

	if conflicts, ok := contradictory[rec1.Action]; ok {
		for _, conflictAction := range conflicts {
			if rec2.Action == conflictAction {
				return &Conflict{
					ID:               uuid.New().String(),
					Type:             ConflictTypeAction,
					Recommendations:  []string{rec1.ID, rec2.ID},
					Description:      fmt.Sprintf("Contradictory actions: %s vs %s", rec1.Action, rec2.Action),
					Severity:         "high",
					ConflictingField: "action",
					DetectedAt:       time.Now(),
					Resolved:         false,
				}
			}
		}
	}

	return nil
}

// checkDependencyConflict checks for circular or violated dependencies
func (cd *ConflictDetector) checkDependencyConflict(rec1, rec2 *Recommendation) *Conflict {
	// Check if rec1 depends on rec2 AND rec2 depends on rec1 (circular)
	rec1DependsOnRec2 := cd.contains(rec1.Dependencies, rec2.ID)
	rec2DependsOnRec1 := cd.contains(rec2.Dependencies, rec1.ID)

	if rec1DependsOnRec2 && rec2DependsOnRec1 {
		return &Conflict{
			ID:               uuid.New().String(),
			Type:             ConflictTypeDependency,
			Recommendations:  []string{rec1.ID, rec2.ID},
			Description:      "Circular dependency detected",
			Severity:         "high",
			ConflictingField: "dependencies",
			DetectedAt:       time.Now(),
			Resolved:         false,
		}
	}

	return nil
}

// ConflictResolver resolves conflicts between recommendations
type ConflictResolver struct{}

// NewConflictResolver creates a new conflict resolver
func NewConflictResolver() *ConflictResolver {
	return &ConflictResolver{}
}

// ResolveConflicts resolves conflicts and returns filtered recommendations
func (cr *ConflictResolver) ResolveConflicts(
	recommendations []*Recommendation,
	conflicts []Conflict,
) ([]*Recommendation, []Conflict) {
	
	if len(conflicts) == 0 {
		return recommendations, conflicts
	}

	log.Printf("Resolving %d conflicts...", len(conflicts))

	resolvedConflicts := make([]Conflict, 0)
	keptRecommendations := make(map[string]bool)
	
	// Initialize all recommendations as kept
	for _, rec := range recommendations {
		keptRecommendations[rec.ID] = true
	}

	// Resolve each conflict
	for _, conflict := range conflicts {
		if len(conflict.Recommendations) < 2 {
			continue
		}

		// Get the conflicting recommendations
		rec1 := cr.findRecommendation(recommendations, conflict.Recommendations[0])
		rec2 := cr.findRecommendation(recommendations, conflict.Recommendations[1])

		if rec1 == nil || rec2 == nil {
			continue
		}

		// Decide which to keep based on priority, impact, confidence
		winner := cr.selectWinner(rec1, rec2)
		loser := rec1
		if winner.ID == rec1.ID {
			loser = rec2
		}

		// Mark loser as not kept
		keptRecommendations[loser.ID] = false

		// Update conflict as resolved
		conflict.Resolved = true
		now := time.Now()
		conflict.ResolvedAt = &now
		conflict.Resolution = fmt.Sprintf("Kept recommendation %s (priority: %d, savings: %.2f), discarded %s",
			winner.ID, winner.Priority, winner.EstimatedSavings, loser.ID)

		resolvedConflicts = append(resolvedConflicts, conflict)

		log.Printf("Resolved conflict: Kept %s (type: %s, priority: %d), Discarded %s (type: %s, priority: %d)",
			winner.ID, winner.Type, winner.Priority,
			loser.ID, loser.Type, loser.Priority)
	}

	// Filter recommendations to only include kept ones
	filteredRecs := make([]*Recommendation, 0)
	for _, rec := range recommendations {
		if keptRecommendations[rec.ID] {
			filteredRecs = append(filteredRecs, rec)
		}
	}

	log.Printf("After conflict resolution: %d recommendations kept (from %d)", len(filteredRecs), len(recommendations))

	return filteredRecs, resolvedConflicts
}

// selectWinner chooses which recommendation to keep in a conflict
func (cr *ConflictResolver) selectWinner(rec1, rec2 *Recommendation) *Recommendation {
	// Priority 1: Higher priority wins
	if rec1.Priority != rec2.Priority {
		if rec1.Priority > rec2.Priority {
			return rec1
		}
		return rec2
	}

	// Priority 2: Higher savings wins
	if rec1.EstimatedSavings != rec2.EstimatedSavings {
		if rec1.EstimatedSavings > rec2.EstimatedSavings {
			return rec1
		}
		return rec2
	}

	// Priority 3: Higher confidence wins
	if rec1.Confidence != rec2.Confidence {
		if rec1.Confidence > rec2.Confidence {
			return rec1
		}
		return rec2
	}

	// Priority 4: Lower risk wins (safer)
	riskScores := map[RiskLevel]int{
		RiskLevelLow:      1,
		RiskLevelMedium:   2,
		RiskLevelHigh:     3,
		RiskLevelCritical: 4,
	}

	if riskScores[rec1.RiskLevel] < riskScores[rec2.RiskLevel] {
		return rec1
	}

	// Default: return first one
	return rec1
}

// Helper methods
func (cd *ConflictDetector) findCommonResources(list1, list2 []string) []string {
	common := make([]string, 0)
	resourceMap := make(map[string]bool)

	for _, r := range list1 {
		resourceMap[r] = true
	}

	for _, r := range list2 {
		if resourceMap[r] {
			common = append(common, r)
		}
	}

	return common
}

func (cd *ConflictDetector) calculateSeverity(rec1, rec2 *Recommendation) string {
	// High severity if both are high-risk
	if rec1.RiskLevel == RiskLevelHigh && rec2.RiskLevel == RiskLevelHigh {
		return "high"
	}

	// Medium severity if one is high-risk
	if rec1.RiskLevel == RiskLevelHigh || rec2.RiskLevel == RiskLevelHigh {
		return "medium"
	}

	return "low"
}

func (cd *ConflictDetector) contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

func (cr *ConflictResolver) findRecommendation(recommendations []*Recommendation, id string) *Recommendation {
	for _, rec := range recommendations {
		if rec.ID == id {
			return rec
		}
	}
	return nil
}
