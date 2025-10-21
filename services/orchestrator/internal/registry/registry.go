package registry

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
)

const (
	// Redis keys
	agentKeyPrefix     = "agent:"
	activeAgentsSetKey = "agents:active"

	// TTL for agent entries in Redis
	agentTTL = 60 * time.Second

	// Health check interval
	healthCheckInterval = 30 * time.Second

	// Heartbeat timeout (if no heartbeat for this long, mark unhealthy)
	heartbeatTimeout = 45 * time.Second
)

// Registry manages agent registration and discovery
type Registry struct {
	redis  *redis.Client
	ctx    context.Context
	mu     sync.RWMutex
	stopCh chan struct{}
}

// NewRegistry creates a new agent registry
func NewRegistry(redisClient *redis.Client) *Registry {
	return &Registry{
		redis:  redisClient,
		ctx:    context.Background(),
		stopCh: make(chan struct{}),
	}
}

// Start begins the health monitoring goroutine
func (r *Registry) Start() {
	go r.healthMonitor()
	log.Println("Agent registry started")
}

// Stop stops the health monitoring
func (r *Registry) Stop() {
	close(r.stopCh)
	log.Println("Agent registry stopped")
}

// Register registers a new agent
func (r *Registry) Register(req *RegistrationRequest) (*RegistrationResponse, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	// Generate agent ID
	agentID := uuid.New().String()

	// Create agent
	agent := &Agent{
		ID:           agentID,
		Name:         req.Name,
		Type:         req.Type,
		Host:         req.Host,
		Port:         req.Port,
		Capabilities: req.Capabilities,
		Status:       AgentStatusHealthy,
		Version:      req.Version,
		RegisteredAt: time.Now(),
		LastSeen:     time.Now(),
		Metadata:     req.Metadata,
	}

	// Store in Redis
	if err := r.storeAgent(agent); err != nil {
		return nil, fmt.Errorf("failed to store agent: %w", err)
	}

	// Add to active agents set
	if err := r.redis.SAdd(r.ctx, activeAgentsSetKey, agentID).Err(); err != nil {
		return nil, fmt.Errorf("failed to add to active set: %w", err)
	}

	log.Printf("Agent registered: %s (%s) - %s", agent.Name, agent.Type, agent.ID)

	return &RegistrationResponse{
		AgentID:      agentID,
		RegisteredAt: agent.RegisteredAt,
		HeartbeatURL: fmt.Sprintf("/agents/%s/heartbeat", agentID),
		Interval:     30, // heartbeat every 30 seconds
	}, nil
}

// Heartbeat updates agent's last seen time and status
func (r *Registry) Heartbeat(agentID string, req *HeartbeatRequest) (*HeartbeatResponse, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	// Get existing agent
	agent, err := r.getAgent(agentID)
	if err != nil {
		return nil, fmt.Errorf("agent not found: %w", err)
	}

	// Update status and last seen
	agent.LastSeen = time.Now()
	agent.Status = req.Status

	// Merge metadata
	if req.Metadata != nil {
		if agent.Metadata == nil {
			agent.Metadata = make(map[string]interface{})
		}
		for k, v := range req.Metadata {
			agent.Metadata[k] = v
		}
	}

	// Store updated agent
	if err := r.storeAgent(agent); err != nil {
		return nil, fmt.Errorf("failed to update agent: %w", err)
	}

	return &HeartbeatResponse{
		Received:     true,
		NextInterval: 30,
		Timestamp:    time.Now(),
	}, nil
}

// Unregister removes an agent from the registry
func (r *Registry) Unregister(agentID string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	// Remove from active set
	if err := r.redis.SRem(r.ctx, activeAgentsSetKey, agentID).Err(); err != nil {
		return fmt.Errorf("failed to remove from active set: %w", err)
	}

	// Delete agent key
	if err := r.redis.Del(r.ctx, agentKey(agentID)).Err(); err != nil {
		return fmt.Errorf("failed to delete agent: %w", err)
	}

	log.Printf("Agent unregistered: %s", agentID)
	return nil
}

// GetAgent retrieves a specific agent by ID
func (r *Registry) GetAgent(agentID string) (*Agent, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	return r.getAgent(agentID)
}

// GetAllAgents retrieves all registered agents
func (r *Registry) GetAllAgents() ([]*Agent, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// Get all active agent IDs
	agentIDs, err := r.redis.SMembers(r.ctx, activeAgentsSetKey).Result()
	if err != nil {
		return nil, fmt.Errorf("failed to get active agents: %w", err)
	}

	agents := make([]*Agent, 0, len(agentIDs))
	for _, id := range agentIDs {
		agent, err := r.getAgent(id)
		if err != nil {
			log.Printf("Warning: failed to get agent %s: %v", id, err)
			continue
		}
		agents = append(agents, agent)
	}

	return agents, nil
}

// GetAgentsByType retrieves all agents of a specific type
func (r *Registry) GetAgentsByType(agentType AgentType) ([]*Agent, error) {
	allAgents, err := r.GetAllAgents()
	if err != nil {
		return nil, err
	}

	filtered := make([]*Agent, 0)
	for _, agent := range allAgents {
		if agent.Type == agentType {
			filtered = append(filtered, agent)
		}
	}

	return filtered, nil
}

// GetAgentWithCapability finds an agent with specific capability
func (r *Registry) GetAgentWithCapability(agentType AgentType, capability string) (*Agent, error) {
	agents, err := r.GetAgentsByType(agentType)
	if err != nil {
		return nil, err
	}

	// Filter by capability and status
	for _, agent := range agents {
		if agent.Status == AgentStatusHealthy {
			for _, cap := range agent.Capabilities {
				if cap == capability {
					return agent, nil
				}
			}
		}
	}

	return nil, fmt.Errorf("no healthy %s agent found with capability: %s", agentType, capability)
}

// GetHealthyAgents returns only healthy agents
func (r *Registry) GetHealthyAgents() ([]*Agent, error) {
	allAgents, err := r.GetAllAgents()
	if err != nil {
		return nil, err
	}

	healthy := make([]*Agent, 0)
	for _, agent := range allAgents {
		if agent.Status == AgentStatusHealthy {
			healthy = append(healthy, agent)
		}
	}

	return healthy, nil
}

// ===================================================================
// INTERNAL HELPERS
// ===================================================================

func (r *Registry) storeAgent(agent *Agent) error {
	data, err := json.Marshal(agent)
	if err != nil {
		return fmt.Errorf("failed to marshal agent: %w", err)
	}

	// Store with TTL
	if err := r.redis.Set(r.ctx, agentKey(agent.ID), data, agentTTL).Err(); err != nil {
		return fmt.Errorf("failed to store in redis: %w", err)
	}

	return nil
}

func (r *Registry) getAgent(agentID string) (*Agent, error) {
	data, err := r.redis.Get(r.ctx, agentKey(agentID)).Result()
	if err == redis.Nil {
		return nil, fmt.Errorf("agent not found")
	} else if err != nil {
		return nil, fmt.Errorf("failed to get from redis: %w", err)
	}

	var agent Agent
	if err := json.Unmarshal([]byte(data), &agent); err != nil {
		return nil, fmt.Errorf("failed to unmarshal agent: %w", err)
	}

	return &agent, nil
}

func agentKey(agentID string) string {
	return agentKeyPrefix + agentID
}

// ===================================================================
// HEALTH MONITORING
// ===================================================================

func (r *Registry) healthMonitor() {
	ticker := time.NewTicker(healthCheckInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			r.checkAgentHealth()
		case <-r.stopCh:
			return
		}
	}
}

func (r *Registry) checkAgentHealth() {
	r.mu.Lock()
	defer r.mu.Unlock()

	agents, err := r.GetAllAgents()
	if err != nil {
		log.Printf("Error checking agent health: %v", err)
		return
	}

	now := time.Now()
	for _, agent := range agents {
		timeSinceLastSeen := now.Sub(agent.LastSeen)

		// Mark unhealthy if no heartbeat for too long
		if timeSinceLastSeen > heartbeatTimeout {
			if agent.Status != AgentStatusUnreachable {
				log.Printf("Agent %s (%s) is unreachable - last seen %v ago",
					agent.Name, agent.ID, timeSinceLastSeen)
				agent.Status = AgentStatusUnreachable
				if err := r.storeAgent(agent); err != nil {
					log.Printf("Failed to update agent status: %v", err)
				}
			}
		}
	}
}
