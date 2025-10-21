package coordination

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// Handler provides HTTP handlers for coordination
type Handler struct {
	coordinator *Coordinator
}

// NewHandler creates a new coordination handler
func NewHandler(coordinator *Coordinator) *Handler {
	return &Handler{
		coordinator: coordinator,
	}
}

// RegisterRoutes registers all coordination routes
func (h *Handler) RegisterRoutes(r *gin.Engine) {
	coord := r.Group("/coordination")
	{
		coord.POST("/coordinate", h.Coordinate)
		coord.GET("/approvals", h.ListApprovals)
		coord.POST("/approvals/:id/approve", h.ApproveRecommendation)
		coord.POST("/approvals/:id/reject", h.RejectRecommendation)
		coord.GET("/plans/:id", h.GetExecutionPlan)
		coord.POST("/plans/:id/execute", h.ExecutePlan)
	}
}

// Coordinate handles coordination requests
func (h *Handler) Coordinate(c *gin.Context) {
	var req CoordinationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	response, err := h.coordinator.Coordinate(&req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, response)
}

// ListApprovals lists pending approvals for a customer
func (h *Handler) ListApprovals(c *gin.Context) {
	customerID := c.Query("customer_id")
	if customerID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "customer_id required"})
		return
	}

	approvals := h.coordinator.GetPendingApprovals(customerID)

	c.JSON(http.StatusOK, gin.H{
		"approvals": approvals,
		"count":     len(approvals),
	})
}

// ApproveRecommendation approves a recommendation
func (h *Handler) ApproveRecommendation(c *gin.Context) {
	approvalID := c.Param("id")
	
	var req struct {
		UserID string `json:"user_id" binding:"required"`
	}
	
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := h.coordinator.ApproveRecommendation(approvalID, req.UserID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Recommendation approved"})
}

// RejectRecommendation rejects a recommendation
func (h *Handler) RejectRecommendation(c *gin.Context) {
	approvalID := c.Param("id")
	
	var req struct {
		UserID string `json:"user_id" binding:"required"`
		Reason string `json:"reason" binding:"required"`
	}
	
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := h.coordinator.RejectRecommendation(approvalID, req.UserID, req.Reason); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Recommendation rejected"})
}

// GetExecutionPlan gets an execution plan
func (h *Handler) GetExecutionPlan(c *gin.Context) {
	planID := c.Param("id")

	plan, err := h.coordinator.GetExecutionPlan(planID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Plan not found"})
		return
	}

	c.JSON(http.StatusOK, plan)
}

// ExecutePlan executes an execution plan
func (h *Handler) ExecutePlan(c *gin.Context) {
	planID := c.Param("id")

	// Execute asynchronously
	go func() {
		if err := h.coordinator.ExecutePlan(planID); err != nil {
			// Log error (in production, notify customer)
			return
		}
	}()

	c.JSON(http.StatusAccepted, gin.H{
		"message": "Execution started",
		"plan_id": planID,
	})
}
