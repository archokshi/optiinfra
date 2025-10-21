package task

import (
	"time"
)

// TaskType represents different types of tasks
type TaskType string

const (
	// Cost Agent Tasks
	TaskTypeAnalyzeCost     TaskType = "analyze_cost"
	TaskTypeMigrateToSpot   TaskType = "migrate_to_spot"
	TaskTypeRightSize       TaskType = "right_size"
	
	// Performance Agent Tasks
	TaskTypeOptimizeKVCache TaskType = "optimize_kv_cache"
	TaskTypeTuneInference   TaskType = "tune_inference"
	
	// Resource Agent Tasks
	TaskTypePredictScaling  TaskType = "predict_scaling"
	TaskTypeBalanceLoad     TaskType = "balance_load"
	
	// Application Agent Tasks
	TaskTypeValidateQuality  TaskType = "validate_quality"
	TaskTypeDetectRegression TaskType = "detect_regression"
)

// TaskStatus represents the current status of a task
type TaskStatus string

const (
	TaskStatusPending   TaskStatus = "pending"
	TaskStatusQueued    TaskStatus = "queued"
	TaskStatusSent      TaskStatus = "sent"
	TaskStatusRunning   TaskStatus = "running"
	TaskStatusCompleted TaskStatus = "completed"
	TaskStatusFailed    TaskStatus = "failed"
	TaskStatusTimeout   TaskStatus = "timeout"
	TaskStatusRetrying  TaskStatus = "retrying"
)

// TaskPriority represents task priority levels
type TaskPriority int

const (
	PriorityLow      TaskPriority = 1
	PriorityNormal   TaskPriority = 5
	PriorityHigh     TaskPriority = 10
	PriorityCritical TaskPriority = 15
)

// Task represents a task to be executed by an agent
type Task struct {
	ID          string                 `json:"task_id"`
	Type        TaskType               `json:"task_type"`
	AgentID     string                 `json:"agent_id,omitempty"`
	AgentType   string                 `json:"agent_type"`
	Priority    TaskPriority           `json:"priority"`
	Parameters  map[string]interface{} `json:"parameters"`
	Status      TaskStatus             `json:"status"`
	Result      map[string]interface{} `json:"result,omitempty"`
	Error       string                 `json:"error,omitempty"`
	CreatedAt   time.Time              `json:"created_at"`
	StartedAt   *time.Time             `json:"started_at,omitempty"`
	CompletedAt *time.Time             `json:"completed_at,omitempty"`
	Timeout     time.Duration          `json:"timeout"`
	RetryCount  int                    `json:"retry_count"`
	MaxRetries  int                    `json:"max_retries"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// TaskRequest is sent to an agent to execute a task
type TaskRequest struct {
	TaskID     string                 `json:"task_id"`
	TaskType   TaskType               `json:"task_type"`
	Parameters map[string]interface{} `json:"parameters"`
	Timeout    int                    `json:"timeout_seconds"`
	Priority   TaskPriority           `json:"priority"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
}

// TaskResponse is received from an agent after task execution
type TaskResponse struct {
	TaskID        string                 `json:"task_id"`
	Status        TaskStatus             `json:"status"`
	Result        map[string]interface{} `json:"result,omitempty"`
	Error         string                 `json:"error,omitempty"`
	ExecutionTime int                    `json:"execution_time_ms"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
}

// TaskSubmitRequest is used to submit a new task
type TaskSubmitRequest struct {
	TaskType   TaskType               `json:"task_type" binding:"required"`
	AgentType  string                 `json:"agent_type" binding:"required"`
	AgentID    string                 `json:"agent_id,omitempty"` // Optional: specific agent
	Parameters map[string]interface{} `json:"parameters"`
	Priority   TaskPriority           `json:"priority"`
	Timeout    int                    `json:"timeout_seconds"`
	MaxRetries int                    `json:"max_retries"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
}

// TaskSubmitResponse returns task details after submission
type TaskSubmitResponse struct {
	TaskID    string     `json:"task_id"`
	Status    TaskStatus `json:"status"`
	AgentID   string     `json:"agent_id"`
	CreatedAt time.Time  `json:"created_at"`
	StatusURL string     `json:"status_url"`
}

// TaskStatusResponse returns current task status
type TaskStatusResponse struct {
	TaskID      string                 `json:"task_id"`
	Status      TaskStatus             `json:"status"`
	AgentID     string                 `json:"agent_id"`
	Result      map[string]interface{} `json:"result,omitempty"`
	Error       string                 `json:"error,omitempty"`
	CreatedAt   time.Time              `json:"created_at"`
	StartedAt   *time.Time             `json:"started_at,omitempty"`
	CompletedAt *time.Time             `json:"completed_at,omitempty"`
	RetryCount  int                    `json:"retry_count"`
}

// TaskListResponse returns a list of tasks
type TaskListResponse struct {
	Tasks []Task `json:"tasks"`
	Count int    `json:"count"`
}
