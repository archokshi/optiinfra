package registry

import (
	"time"
)

// AgentType represents the type of agent
type AgentType string

const (
	AgentTypeCost        AgentType = "cost"
	AgentTypePerformance AgentType = "performance"
	AgentTypeResource    AgentType = "resource"
	AgentTypeApplication AgentType = "application"
)

// AgentStatus represents the current status of an agent
type AgentStatus string

const (
	AgentStatusHealthy     AgentStatus = "healthy"
	AgentStatusDegraded    AgentStatus = "degraded"
	AgentStatusUnhealthy   AgentStatus = "unhealthy"
	AgentStatusUnreachable AgentStatus = "unreachable"
)

// Agent represents a registered agent
type Agent struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	Type         AgentType              `json:"type"`
	Host         string                 `json:"host"`
	Port         int                    `json:"port"`
	Capabilities []string               `json:"capabilities"`
	Status       AgentStatus            `json:"status"`
	Version      string                 `json:"version"`
	RegisteredAt time.Time              `json:"registered_at"`
	LastSeen     time.Time              `json:"last_seen"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// RegistrationRequest is sent by agents to register
type RegistrationRequest struct {
	Name         string                 `json:"name" binding:"required"`
	Type         AgentType              `json:"type" binding:"required"`
	Host         string                 `json:"host" binding:"required"`
	Port         int                    `json:"port" binding:"required"`
	Capabilities []string               `json:"capabilities"`
	Version      string                 `json:"version"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// RegistrationResponse is returned after successful registration
type RegistrationResponse struct {
	AgentID      string    `json:"agent_id"`
	RegisteredAt time.Time `json:"registered_at"`
	HeartbeatURL string    `json:"heartbeat_url"`
	Interval     int       `json:"heartbeat_interval_seconds"`
}

// HeartbeatRequest is sent by agents periodically
type HeartbeatRequest struct {
	Status   AgentStatus            `json:"status"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// HeartbeatResponse confirms heartbeat received
type HeartbeatResponse struct {
	Received     bool      `json:"received"`
	NextInterval int       `json:"next_interval_seconds"`
	Timestamp    time.Time `json:"timestamp"`
}

// AgentListResponse returns list of agents
type AgentListResponse struct {
	Agents []Agent `json:"agents"`
	Count  int     `json:"count"`
}
