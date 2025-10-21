package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// Metrics holds all Prometheus metrics for the orchestrator
type Metrics struct {
	// Agent request metrics
	AgentRequestsTotal *prometheus.CounterVec
	AgentRequestDuration *prometheus.HistogramVec
	AgentHealthStatus *prometheus.GaugeVec
	
	// Coordination metrics
	CoordinationConflictsTotal prometheus.Counter
	ApprovalWorkflowDuration *prometheus.HistogramVec
	ActiveOptimizations prometheus.Gauge
	
	// Task routing metrics
	TasksRoutedTotal *prometheus.CounterVec
	TaskQueueDepth *prometheus.GaugeVec
	TaskProcessingDuration *prometheus.HistogramVec
	
	// HTTP metrics
	HTTPRequestsTotal *prometheus.CounterVec
	HTTPRequestDuration *prometheus.HistogramVec
	
	// System metrics
	ActiveAgents *prometheus.GaugeVec
	AgentRegistrations prometheus.Counter
	AgentDeregistrations prometheus.Counter
}

// NewMetrics creates and registers all orchestrator metrics
func NewMetrics() *Metrics {
	m := &Metrics{
		// Agent request metrics
		AgentRequestsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "agent_requests_total",
				Help: "Total number of requests to agents",
			},
			[]string{"agent", "status"},
		),
		
		AgentRequestDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name: "agent_request_duration_seconds",
				Help: "Duration of agent requests in seconds",
				Buckets: []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10},
			},
			[]string{"agent"},
		),
		
		AgentHealthStatus: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "agent_health_status",
				Help: "Health status of agents (1=healthy, 0=unhealthy)",
			},
			[]string{"agent", "agent_type"},
		),
		
		// Coordination metrics
		CoordinationConflictsTotal: promauto.NewCounter(
			prometheus.CounterOpts{
				Name: "coordination_conflicts_total",
				Help: "Total number of coordination conflicts detected",
			},
		),
		
		ApprovalWorkflowDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name: "approval_workflow_duration_seconds",
				Help: "Duration of approval workflows in seconds",
				Buckets: []float64{0.1, 0.5, 1, 2, 5, 10, 30, 60},
			},
			[]string{"workflow_type"},
		),
		
		ActiveOptimizations: promauto.NewGauge(
			prometheus.GaugeOpts{
				Name: "active_optimizations",
				Help: "Number of currently active optimizations",
			},
		),
		
		// Task routing metrics
		TasksRoutedTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "tasks_routed_total",
				Help: "Total number of tasks routed to agents",
			},
			[]string{"agent", "task_type", "status"},
		),
		
		TaskQueueDepth: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "task_queue_depth",
				Help: "Current depth of task queues",
			},
			[]string{"agent"},
		),
		
		TaskProcessingDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name: "task_processing_duration_seconds",
				Help: "Duration of task processing in seconds",
				Buckets: []float64{0.1, 0.5, 1, 5, 10, 30, 60, 300},
			},
			[]string{"agent", "task_type"},
		),
		
		// HTTP metrics
		HTTPRequestsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "http_requests_total",
				Help: "Total number of HTTP requests",
			},
			[]string{"method", "endpoint", "status"},
		),
		
		HTTPRequestDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name: "http_request_duration_seconds",
				Help: "Duration of HTTP requests in seconds",
				Buckets: []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1},
			},
			[]string{"method", "endpoint"},
		),
		
		// System metrics
		ActiveAgents: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "active_agents",
				Help: "Number of active agents",
			},
			[]string{"agent_type"},
		),
		
		AgentRegistrations: promauto.NewCounter(
			prometheus.CounterOpts{
				Name: "agent_registrations_total",
				Help: "Total number of agent registrations",
			},
		),
		
		AgentDeregistrations: promauto.NewCounter(
			prometheus.CounterOpts{
				Name: "agent_deregistrations_total",
				Help: "Total number of agent deregistrations",
			},
		),
	}
	
	return m
}

// RecordAgentRequest records metrics for an agent request
func (m *Metrics) RecordAgentRequest(agent, status string, duration float64) {
	m.AgentRequestsTotal.WithLabelValues(agent, status).Inc()
	m.AgentRequestDuration.WithLabelValues(agent).Observe(duration)
}

// UpdateAgentHealth updates the health status of an agent
func (m *Metrics) UpdateAgentHealth(agent, agentType string, healthy bool) {
	value := 0.0
	if healthy {
		value = 1.0
	}
	m.AgentHealthStatus.WithLabelValues(agent, agentType).Set(value)
}

// RecordCoordinationConflict records a coordination conflict
func (m *Metrics) RecordCoordinationConflict() {
	m.CoordinationConflictsTotal.Inc()
}

// RecordApprovalWorkflow records an approval workflow execution
func (m *Metrics) RecordApprovalWorkflow(workflowType string, duration float64) {
	m.ApprovalWorkflowDuration.WithLabelValues(workflowType).Observe(duration)
}

// UpdateActiveOptimizations updates the count of active optimizations
func (m *Metrics) UpdateActiveOptimizations(count float64) {
	m.ActiveOptimizations.Set(count)
}

// RecordTaskRouted records a task being routed to an agent
func (m *Metrics) RecordTaskRouted(agent, taskType, status string) {
	m.TasksRoutedTotal.WithLabelValues(agent, taskType, status).Inc()
}

// UpdateTaskQueueDepth updates the task queue depth for an agent
func (m *Metrics) UpdateTaskQueueDepth(agent string, depth float64) {
	m.TaskQueueDepth.WithLabelValues(agent).Set(depth)
}

// RecordTaskProcessing records task processing duration
func (m *Metrics) RecordTaskProcessing(agent, taskType string, duration float64) {
	m.TaskProcessingDuration.WithLabelValues(agent, taskType).Observe(duration)
}

// RecordHTTPRequest records an HTTP request
func (m *Metrics) RecordHTTPRequest(method, endpoint, status string, duration float64) {
	m.HTTPRequestsTotal.WithLabelValues(method, endpoint, status).Inc()
	m.HTTPRequestDuration.WithLabelValues(method, endpoint).Observe(duration)
}

// UpdateActiveAgents updates the count of active agents by type
func (m *Metrics) UpdateActiveAgents(agentType string, count float64) {
	m.ActiveAgents.WithLabelValues(agentType).Set(count)
}

// RecordAgentRegistration records an agent registration
func (m *Metrics) RecordAgentRegistration() {
	m.AgentRegistrations.Inc()
}

// RecordAgentDeregistration records an agent deregistration
func (m *Metrics) RecordAgentDeregistration() {
	m.AgentDeregistrations.Inc()
}
