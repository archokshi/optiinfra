package task

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// Handler provides HTTP handlers for task routing
type Handler struct {
	router *Router
}

// NewHandler creates a new handler
func NewHandler(router *Router) *Handler {
	return &Handler{
		router: router,
	}
}

// RegisterRoutes registers all task routes
func (h *Handler) RegisterRoutes(r *gin.Engine) {
	tasks := r.Group("/tasks")
	{
		tasks.POST("", h.SubmitTask)
		tasks.GET("/:id", h.GetTaskStatus)
		tasks.GET("", h.ListTasks)
		tasks.DELETE("/:id", h.CancelTask)
	}
}

// SubmitTask handles task submission
func (h *Handler) SubmitTask(c *gin.Context) {
	var req TaskSubmitRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	resp, err := h.router.SubmitTask(&req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, resp)
}

// GetTaskStatus retrieves task status
func (h *Handler) GetTaskStatus(c *gin.Context) {
	taskID := c.Param("id")

	status, err := h.router.GetTaskStatus(taskID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Task not found"})
		return
	}

	c.JSON(http.StatusOK, status)
}

// ListTasks lists all tasks
func (h *Handler) ListTasks(c *gin.Context) {
	statusFilter := TaskStatus(c.Query("status"))

	tasks, err := h.router.ListTasks(statusFilter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, TaskListResponse{
		Tasks: convertToTaskSlice(tasks),
		Count: len(tasks),
	})
}

// CancelTask cancels a task
func (h *Handler) CancelTask(c *gin.Context) {
	taskID := c.Param("id")

	if err := h.router.CancelTask(taskID); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Task cancelled successfully"})
}

func convertToTaskSlice(tasks []*Task) []Task {
	result := make([]Task, len(tasks))
	for i, task := range tasks {
		result[i] = *task
	}
	return result
}
