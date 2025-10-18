# Windsurf AI-Assisted Development

This directory contains prompts and context for AI-assisted development of OptiInfra.

## Structure

```
.windsurf/
├── prompts/              # All development prompts
│   ├── pilot/            # Pilot phase (Week 0)
│   ├── 00-foundation/    # Foundation (Week 1)
│   ├── 01-cost-agent/    # Cost Agent (Week 2-3)
│   ├── 02-performance-agent/  # Performance Agent (Week 4-5)
│   ├── 03-resource-agent/     # Resource Agent (Week 6-7)
│   ├── 04-application-agent/  # Application Agent (Week 8-9)
│   └── 05-portal/        # Portal & Production (Week 10)
├── context/              # Project context and design docs
└── README.md
```

## Development Phases

### PILOT (Week 0) - 5 prompts
- Bootstrap project structure
- Create orchestrator skeleton
- Create agent skeleton
- Setup databases
- End-to-end smoke test

### Foundation (Week 1) - 15 prompts
- Database schemas
- Orchestrator core
- Agent registry
- Request routing
- Monitoring setup

### Cost Agent (Week 2-3) - 17 prompts
- Cost data collectors
- Analysis workflows
- Recommendation engine
- Execution engine
- Testing

### Performance Agent (Week 4-5) - 11 prompts
- Performance collectors
- Analysis workflows
- Optimization engine
- Testing

### Resource Agent (Week 6-7) - 10 prompts
- Resource collectors
- Analysis workflows
- Scaling engine
- Testing

### Application Agent (Week 8-9) - 9 prompts
- Quality collectors
- Baseline engine
- Validation engine
- Testing

### Portal & Production (Week 10) - 8 prompts
- Dashboard components
- Real-time updates
- Approval workflows
- Production deployment

## Usage

Each prompt file contains:
- Context and dependencies
- Objective and success criteria
- Technical specifications
- Implementation requirements
- Validation commands
- Troubleshooting guide

## Progress Tracking

Track progress in `progress.md` (to be created during development).
