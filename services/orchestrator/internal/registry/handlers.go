package registry

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// Handler provides HTTP handlers for the registry
type Handler struct {
	registry *Registry
}

// NewHandler creates a new handler
func NewHandler(registry *Registry) *Handler {
	return &Handler{
		registry: registry,
	}
}

// RegisterRoutes registers all registry routes
func (h *Handler) RegisterRoutes(router *gin.Engine) {
	agents := router.Group("/agents")
	{
		agents.POST("/register", h.Register)
		agents.POST("/:id/heartbeat", h.Heartbeat)
		agents.POST("/:id/unregister", h.Unregister)
		agents.GET("", h.List)
		agents.GET("/:id", h.Get)
		agents.GET("/type/:type", h.ListByType)
	}
}

// Register handles agent registration
func (h *Handler) Register(c *gin.Context) {
	var req RegistrationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	resp, err := h.registry.Register(&req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, resp)
}

// Heartbeat handles agent heartbeat
func (h *Handler) Heartbeat(c *gin.Context) {
	agentID := c.Param("id")

	var req HeartbeatRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	resp, err := h.registry.Heartbeat(agentID, &req)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, resp)
}

// Unregister handles agent unregistration
func (h *Handler) Unregister(c *gin.Context) {
	agentID := c.Param("id")

	if err := h.registry.Unregister(agentID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Agent unregistered successfully"})
}

// List returns all registered agents
func (h *Handler) List(c *gin.Context) {
	agents, err := h.registry.GetAllAgents()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, AgentListResponse{
		Agents: convertToAgentSlice(agents),
		Count:  len(agents),
	})
}

// Get returns a specific agent
func (h *Handler) Get(c *gin.Context) {
	agentID := c.Param("id")

	agent, err := h.registry.GetAgent(agentID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Agent not found"})
		return
	}

	c.JSON(http.StatusOK, agent)
}

// ListByType returns agents of a specific type
func (h *Handler) ListByType(c *gin.Context) {
	agentType := AgentType(c.Param("type"))

	agents, err := h.registry.GetAgentsByType(agentType)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, AgentListResponse{
		Agents: convertToAgentSlice(agents),
		Count:  len(agents),
	})
}

func convertToAgentSlice(agents []*Agent) []Agent {
	result := make([]Agent, len(agents))
	for i, agent := range agents {
		result[i] = *agent
	}
	return result
}
