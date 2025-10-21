package task

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"

	"optiinfra/services/orchestrator/internal/registry"
)

const (
	// Redis keys
	taskKeyPrefix     = "task:"
	taskPendingPrefix = "task:pending:"
	taskActivePrefix  = "task:active:"
	taskResultPrefix  = "task:result:"
	
	// Timeouts
	defaultTaskTimeout = 30 * time.Second
	maxTaskTimeout     = 5 * time.Minute
	taskResultTTL      = 1 * time.Hour
	
	// Retry settings
	defaultMaxRetries = 3
	retryDelay        = 5 * time.Second
)

// Router handles task routing and execution
type Router struct {
	redis    *redis.Client
	registry *registry.Registry
	client   *http.Client
	ctx      context.Context
	mu       sync.RWMutex
	tasks    map[string]*Task // in-memory task tracking
}

// NewRouter creates a new task router
func NewRouter(redisClient *redis.Client, reg *registry.Registry) *Router {
	return &Router{
		redis:    redisClient,
		registry: reg,
		client: &http.Client{
			Timeout: maxTaskTimeout,
		},
		ctx:   context.Background(),
		tasks: make(map[string]*Task),
	}
}

// SubmitTask submits a new task for execution
func (r *Router) SubmitTask(req *TaskSubmitRequest) (*TaskSubmitResponse, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	// Validate request
	if err := r.validateTaskRequest(req); err != nil {
		return nil, fmt.Errorf("invalid task request: %w", err)
	}

	// Create task
	task := &Task{
		ID:         uuid.New().String(),
		Type:       req.TaskType,
		AgentType:  req.AgentType,
		AgentID:    req.AgentID,
		Priority:   req.Priority,
		Parameters: req.Parameters,
		Status:     TaskStatusPending,
		CreatedAt:  time.Now(),
		Timeout:    time.Duration(req.Timeout) * time.Second,
		MaxRetries: req.MaxRetries,
		RetryCount: 0,
		Metadata:   req.Metadata,
	}

	// Set defaults
	if task.Priority == 0 {
		task.Priority = PriorityNormal
	}
	if task.Timeout == 0 {
		task.Timeout = defaultTaskTimeout
	}
	if task.MaxRetries == 0 {
		task.MaxRetries = defaultMaxRetries
	}

	// Find agent if not specified
	var agent *registry.Agent
	var err error
	
	if task.AgentID != "" {
		// Use specified agent
		agent, err = r.registry.GetAgent(task.AgentID)
		if err != nil {
			return nil, fmt.Errorf("agent not found: %w", err)
		}
	} else {
		// Find available agent of correct type
		agent, err = r.findAvailableAgent(task.AgentType, string(task.Type))
		if err != nil {
			return nil, fmt.Errorf("no available agent: %w", err)
		}
		task.AgentID = agent.ID
	}

	// Store task
	if err := r.storeTask(task); err != nil {
		return nil, fmt.Errorf("failed to store task: %w", err)
	}

	// Track in memory
	r.tasks[task.ID] = task

	// Send task to agent asynchronously
	go r.executeTask(task, agent)

	log.Printf("Task submitted: %s -> Agent: %s (%s)", task.ID, agent.Name, agent.ID)

	return &TaskSubmitResponse{
		TaskID:    task.ID,
		Status:    task.Status,
		AgentID:   task.AgentID,
		CreatedAt: task.CreatedAt,
		StatusURL: fmt.Sprintf("/tasks/%s", task.ID),
	}, nil
}

// GetTaskStatus retrieves the current status of a task
func (r *Router) GetTaskStatus(taskID string) (*TaskStatusResponse, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// Try in-memory first
	if task, ok := r.tasks[taskID]; ok {
		return r.taskToStatusResponse(task), nil
	}

	// Try Redis
	task, err := r.getTask(taskID)
	if err != nil {
		return nil, fmt.Errorf("task not found: %w", err)
	}

	return r.taskToStatusResponse(task), nil
}

// ListTasks returns all tasks (optionally filtered by status)
func (r *Router) ListTasks(status TaskStatus) ([]*Task, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	tasks := make([]*Task, 0)
	for _, task := range r.tasks {
		if status == "" || task.Status == status {
			tasks = append(tasks, task)
		}
	}

	return tasks, nil
}

// CancelTask cancels a pending or running task
func (r *Router) CancelTask(taskID string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	task, ok := r.tasks[taskID]
	if !ok {
		return fmt.Errorf("task not found")
	}

	if task.Status == TaskStatusCompleted || task.Status == TaskStatusFailed {
		return fmt.Errorf("cannot cancel completed task")
	}

	task.Status = TaskStatusFailed
	task.Error = "cancelled by user"
	now := time.Now()
	task.CompletedAt = &now

	if err := r.storeTask(task); err != nil {
		return fmt.Errorf("failed to update task: %w", err)
	}

	log.Printf("Task cancelled: %s", taskID)
	return nil
}

// ===================================================================
// INTERNAL METHODS
// ===================================================================

func (r *Router) executeTask(task *Task, agent *registry.Agent) {
	// Update status to sent
	task.Status = TaskStatusSent
	now := time.Now()
	task.StartedAt = &now
	r.storeTask(task)

	// Prepare request
	taskReq := &TaskRequest{
		TaskID:     task.ID,
		TaskType:   task.Type,
		Parameters: task.Parameters,
		Timeout:    int(task.Timeout.Seconds()),
		Priority:   task.Priority,
		Metadata:   task.Metadata,
	}

	// Send to agent with retries
	var lastErr error
	for attempt := 0; attempt <= task.MaxRetries; attempt++ {
		if attempt > 0 {
			log.Printf("Retrying task %s (attempt %d/%d)", task.ID, attempt, task.MaxRetries)
			task.Status = TaskStatusRetrying
			task.RetryCount = attempt
			r.storeTask(task)
			time.Sleep(retryDelay)
		}

		// Send task
		response, err := r.sendTaskToAgent(agent, taskReq)
		if err == nil {
			// Success
			r.handleTaskSuccess(task, response)
			return
		}

		lastErr = err
		log.Printf("Task %s failed: %v", task.ID, err)
	}

	// All retries exhausted
	r.handleTaskFailure(task, lastErr)
}

func (r *Router) sendTaskToAgent(agent *registry.Agent, taskReq *TaskRequest) (*TaskResponse, error) {
	// Build URL
	url := fmt.Sprintf("http://%s:%d/task", agent.Host, agent.Port)

	// Marshal request
	body, err := json.Marshal(taskReq)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Create HTTP request
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	// Send request
	resp, err := r.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	// Check status code
	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("agent returned error: %d - %s", resp.StatusCode, string(bodyBytes))
	}

	// Parse response
	var taskResp TaskResponse
	if err := json.NewDecoder(resp.Body).Decode(&taskResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &taskResp, nil
}

func (r *Router) handleTaskSuccess(task *Task, response *TaskResponse) {
	r.mu.Lock()
	defer r.mu.Unlock()

	task.Status = TaskStatusCompleted
	task.Result = response.Result
	now := time.Now()
	task.CompletedAt = &now

	if err := r.storeTask(task); err != nil {
		log.Printf("Failed to store task result: %v", err)
	}

	// Store result with TTL
	r.storeTaskResult(task.ID, response)

	log.Printf("Task completed: %s (execution time: %dms)", task.ID, response.ExecutionTime)
}

func (r *Router) handleTaskFailure(task *Task, err error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	task.Status = TaskStatusFailed
	task.Error = err.Error()
	now := time.Now()
	task.CompletedAt = &now

	if storeErr := r.storeTask(task); storeErr != nil {
		log.Printf("Failed to store task failure: %v", storeErr)
	}

	log.Printf("Task failed permanently: %s - %v", task.ID, err)
}

func (r *Router) findAvailableAgent(agentType string, capability string) (*registry.Agent, error) {
	// Get agents of correct type
	agents, err := r.registry.GetAgentsByType(registry.AgentType(agentType))
	if err != nil {
		return nil, err
	}

	// Filter by capability and health
	var availableAgents []*registry.Agent
	for _, agent := range agents {
		if agent.Status == registry.AgentStatusHealthy {
			// Check if agent has required capability
			if capability != "" {
				hasCapability := false
				for _, cap := range agent.Capabilities {
					if cap == capability {
						hasCapability = true
						break
					}
				}
				if !hasCapability {
					continue
				}
			}
			availableAgents = append(availableAgents, agent)
		}
	}

	if len(availableAgents) == 0 {
		return nil, fmt.Errorf("no healthy agents available")
	}

	// Simple round-robin: return first available
	// TODO: Implement proper load balancing
	return availableAgents[0], nil
}

func (r *Router) validateTaskRequest(req *TaskSubmitRequest) error {
	if req.TaskType == "" {
		return fmt.Errorf("task_type is required")
	}
	if req.AgentType == "" {
		return fmt.Errorf("agent_type is required")
	}
	if req.Timeout < 0 {
		return fmt.Errorf("timeout cannot be negative")
	}
	if req.Timeout > int(maxTaskTimeout.Seconds()) {
		return fmt.Errorf("timeout exceeds maximum allowed")
	}
	return nil
}

func (r *Router) storeTask(task *Task) error {
	data, err := json.Marshal(task)
	if err != nil {
		return fmt.Errorf("failed to marshal task: %w", err)
	}

	key := taskKeyPrefix + task.ID
	if err := r.redis.Set(r.ctx, key, data, taskResultTTL).Err(); err != nil {
		return fmt.Errorf("failed to store in redis: %w", err)
	}

	return nil
}

func (r *Router) getTask(taskID string) (*Task, error) {
	key := taskKeyPrefix + taskID
	data, err := r.redis.Get(r.ctx, key).Result()
	if err == redis.Nil {
		return nil, fmt.Errorf("task not found")
	} else if err != nil {
		return nil, fmt.Errorf("failed to get from redis: %w", err)
	}

	var task Task
	if err := json.Unmarshal([]byte(data), &task); err != nil {
		return nil, fmt.Errorf("failed to unmarshal task: %w", err)
	}

	return &task, nil
}

func (r *Router) storeTaskResult(taskID string, response *TaskResponse) error {
	data, err := json.Marshal(response)
	if err != nil {
		return err
	}

	key := taskResultPrefix + taskID
	return r.redis.Set(r.ctx, key, data, taskResultTTL).Err()
}

func (r *Router) taskToStatusResponse(task *Task) *TaskStatusResponse {
	return &TaskStatusResponse{
		TaskID:      task.ID,
		Status:      task.Status,
		AgentID:     task.AgentID,
		Result:      task.Result,
		Error:       task.Error,
		CreatedAt:   task.CreatedAt,
		StartedAt:   task.StartedAt,
		CompletedAt: task.CompletedAt,
		RetryCount:  task.RetryCount,
	}
}
