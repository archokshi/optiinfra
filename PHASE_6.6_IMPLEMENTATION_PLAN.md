# Phase 6.6: Multi-Cloud Generic Collector - Implementation Plan

**Status:** 🔄 In Progress  
**Start Date:** October 30, 2025  
**Estimated Duration:** 15 days  
**Goal:** Universal cloud provider support (15+ providers)

---

## 📋 Overview

Implement a Generic Collector that supports any cloud provider or infrastructure with Prometheus metrics, eliminating the need for provider-specific collectors for non-Big-3 clouds.

---

## 🎯 Phase 6.6.1: Generic Collector Core (Days 1-2)

### Objective
Create the foundational Generic Collector class with universal Prometheus and DCGM support.

### Tasks

#### 1.1 Create Base Structure
- [ ] Create `services/data-collector/src/collectors/generic_collector.py`
- [ ] Extend `BaseCollector` class
- [ ] Define initialization with config dict
- [ ] Add logging and error handling

#### 1.2 Implement Prometheus Scraping
- [ ] `scrape_prometheus()` method
- [ ] Support for PromQL queries
- [ ] Parse Prometheus response format
- [ ] Handle connection errors and timeouts
- [ ] Retry logic with exponential backoff

#### 1.3 Implement DCGM GPU Metrics
- [ ] `scrape_dcgm()` method
- [ ] Parse DCGM exporter metrics
- [ ] Extract GPU utilization, memory, power, temperature
- [ ] Handle missing DCGM endpoint gracefully

#### 1.4 Metric Normalization
- [ ] `normalize_metrics()` method
- [ ] Convert provider-specific formats to standard schema
- [ ] Validate metric values
- [ ] Add timestamps and metadata

#### 1.5 Collection Workflow
- [ ] `collect_all_metrics()` orchestration method
- [ ] Parallel collection (Prometheus + DCGM)
- [ ] Error aggregation
- [ ] Return standardized result

### Deliverables
- ✅ `generic_collector.py` (~400 lines)
- ✅ Works in Prometheus-only mode
- ✅ Handles errors gracefully
- ✅ Returns normalized metrics

### Testing
- [ ] Unit tests for each method
- [ ] Test with mock Prometheus endpoint
- [ ] Test with/without DCGM
- [ ] Test error scenarios

---

## 🎯 Phase 6.6.2: Provider API Integration (Days 3-5)

### Objective
Add provider-specific API adapters for billing and cost data.

### Tasks

#### 2.1 Create API Adapter Interface
- [ ] Create `services/data-collector/src/collectors/providers/__init__.py`
- [ ] Define `BaseProviderAPI` abstract class
- [ ] Standard methods: `get_billing_info()`, `get_instance_info()`

#### 2.2 Implement Provider Adapters (12 total)

**Priority 1 (Demo/Common):**
- [ ] `vultr_api.py` - Vultr API adapter
- [ ] `runpod_api.py` - RunPod GraphQL API
- [ ] `digitalocean_api.py` - DigitalOcean API

**Priority 2 (GPU Clouds):**
- [ ] `lambda_api.py` - Lambda Labs API
- [ ] `coreweave_api.py` - CoreWeave API
- [ ] `paperspace_api.py` - Paperspace API

**Priority 3 (General Compute):**
- [ ] `linode_api.py` - Linode/Akamai API
- [ ] `hetzner_api.py` - Hetzner API
- [ ] `ovh_api.py` - OVHcloud API

**Priority 4 (Container/Self-Hosted):**
- [ ] `kubernetes_api.py` - Kubernetes API
- [ ] `docker_api.py` - Docker API

#### 2.3 Integrate with Generic Collector
- [ ] Add `call_provider_api()` method to Generic Collector
- [ ] Dynamic adapter loading based on provider name
- [ ] Graceful fallback if API unavailable
- [ ] Cache API responses (5-min TTL)

### Deliverables
- ✅ 12 provider API adapters (~100 lines each)
- ✅ Billing/cost data collection
- ✅ Fallback to Prometheus-only mode

### Testing
- [ ] Unit tests for each adapter
- [ ] Integration tests with real APIs (using test accounts)
- [ ] Test fallback behavior

---

## 🎯 Phase 6.6.3: Configuration Management (Day 6)

### Objective
Create comprehensive configuration system for all providers.

### Tasks

#### 3.1 Provider Configuration Schema
- [ ] Create `services/data-collector/config/providers.yaml`
- [ ] Define schema for each provider
- [ ] Include API URLs, ports, requirements
- [ ] Add documentation/comments

#### 3.2 Environment Variables
- [ ] Update `.env.example` with all provider configs
- [ ] Add enable/disable flags per provider
- [ ] API keys for each provider
- [ ] Default endpoints

#### 3.3 Configuration Validation
- [ ] Create `validate_provider_config()` function
- [ ] Check required fields
- [ ] Validate URLs and ports
- [ ] Warn about missing optional fields
- [ ] Run validation on startup

#### 3.4 Update Settings
- [ ] Update `services/data-collector/src/config.py`
- [ ] Add provider settings classes
- [ ] Load from environment + YAML
- [ ] Provide sensible defaults

### Deliverables
- ✅ `providers.yaml` configuration file
- ✅ Updated `.env.example`
- ✅ Configuration validation
- ✅ Updated `config.py`

### Testing
- [ ] Test configuration loading
- [ ] Test validation (valid/invalid configs)
- [ ] Test defaults

---

## 🎯 Phase 6.6.4: Workflow Integration (Days 7-8)

### Objective
Integrate Generic Collector into existing collection workflows.

### Tasks

#### 4.1 Update Collection API
- [ ] Update `services/data-collector/src/main.py`
- [ ] Add generic provider support to `/api/v1/collect/trigger`
- [ ] Route to Generic Collector for non-Big-3 providers
- [ ] Support batch collection (multiple providers)

#### 4.2 Celery Task Integration
- [ ] Update `services/data-collector/src/tasks.py`
- [ ] Add `collect_generic_provider` task
- [ ] Support scheduled collection
- [ ] Handle task retries and failures

#### 4.3 Orchestrator Updates
- [ ] Update `services/orchestrator/internal/router/router.go`
- [ ] Add generic provider routing
- [ ] Update agent registry
- [ ] Handle multi-provider requests

#### 4.4 Collection Workflow
- [ ] Create `services/data-collector/src/workflows/generic_collection.py`
- [ ] End-to-end collection orchestration
- [ ] Error handling and logging
- [ ] Metrics storage in ClickHouse

### Deliverables
- ✅ Updated collection API
- ✅ Celery tasks for generic providers
- ✅ Orchestrator routing
- ✅ Complete workflow

### Testing
- [ ] Test collection trigger API
- [ ] Test Celery tasks
- [ ] Test end-to-end workflow
- [ ] Test with multiple providers

---

## 🎯 Phase 6.6.5: ClickHouse Schema Updates (Day 9)

### Objective
Ensure database schemas support all providers.

### Tasks

#### 5.1 Schema Verification
- [ ] Review existing ClickHouse schemas
- [ ] Verify `provider` field supports all provider names
- [ ] Check metric columns support all metric types
- [ ] Optimize indexes for multi-provider queries

#### 5.2 Provider Metadata Table
- [ ] Create `provider_metadata` table
- [ ] Store provider capabilities
- [ ] Store API endpoints per customer
- [ ] Store collection status

#### 5.3 Migration Scripts
- [ ] Create `services/data-collector/clickhouse/migrations/006_generic_providers.sql`
- [ ] Add new provider names to enums (if needed)
- [ ] Create provider metadata table
- [ ] Add indexes for performance

#### 5.4 Query Optimization
- [ ] Update queries for multi-provider support
- [ ] Add provider filtering
- [ ] Optimize aggregations

### Deliverables
- ✅ Verified schema compatibility
- ✅ Provider metadata table
- ✅ Migration scripts
- ✅ Optimized queries

### Testing
- [ ] Test schema migrations
- [ ] Test data insertion for all providers
- [ ] Test query performance
- [ ] Test with large datasets

---

## 🎯 Phase 6.6.6: Testing & Validation (Days 10-11)

### Objective
Comprehensive testing and documentation.

### Tasks

#### 6.1 Unit Tests
- [ ] Create `services/data-collector/tests/test_generic_collector.py`
- [ ] Test all Generic Collector methods
- [ ] Test provider API adapters
- [ ] Test configuration loading
- [ ] Target: 90%+ code coverage

#### 6.2 Integration Tests
- [ ] Create `services/data-collector/tests/test_integration.py`
- [ ] Test end-to-end collection for each provider
- [ ] Test with Vultr demo instance
- [ ] Test Prometheus-only mode
- [ ] Test API + Prometheus mode

#### 6.3 Load Testing
- [ ] Test concurrent collection from 10+ providers
- [ ] Test with 100+ customers
- [ ] Verify performance meets SLA (<5 sec per collection)
- [ ] Check memory usage and resource consumption

#### 6.4 Documentation
- [ ] Create `docs/GENERIC_COLLECTOR.md` (architecture)
- [ ] Create `docs/ADDING_PROVIDERS.md` (how-to guide)
- [ ] Update API documentation
- [ ] Add code comments and docstrings

### Deliverables
- ✅ 90%+ test coverage
- ✅ All integration tests passing
- ✅ Load tests meet performance targets
- ✅ Complete documentation

### Testing
- [ ] Run full test suite
- [ ] Generate coverage report
- [ ] Review and fix any failures

---

## 🎯 Phase 6.6.7: Portal UI for Multi-Cloud (Days 12-15)

### Objective
Build complete UI for managing cloud providers.

### Tasks

#### 7.1 Cloud Provider Settings Page
- [ ] Create `services/portal/src/pages/settings/cloud-providers.tsx`
- [ ] List of connected providers
- [ ] Provider status indicators
- [ ] Add/configure/disconnect actions
- [ ] Last sync timestamps

#### 7.2 Provider Selector Modal
- [ ] Create `services/portal/src/components/providers/ProviderSelector.tsx`
- [ ] Grid of all supported providers
- [ ] Search and filter
- [ ] Categorization (Big 3, GPU Cloud, General, Self-Hosted)
- [ ] Provider logos

#### 7.3 Provider Configuration Forms
- [ ] Create `services/portal/src/components/providers/ProviderConfigForm.tsx`
- [ ] Dynamic forms based on provider type
- [ ] API key/credentials input
- [ ] Endpoint configuration
- [ ] Collection settings
- [ ] Connection testing
- [ ] Real-time validation

#### 7.4 Provider Components
- [ ] Create `services/portal/src/components/providers/ProviderCard.tsx`
- [ ] Create `services/portal/src/components/providers/ConnectionStatus.tsx`
- [ ] Create `services/portal/src/components/providers/ProviderLogo.tsx`

#### 7.5 Multi-Cloud Dashboard
- [ ] Create `services/portal/src/components/dashboard/MultiCloudOverview.tsx`
- [ ] Aggregated view across providers
- [ ] Cost breakdown by provider
- [ ] Performance comparison
- [ ] Provider-specific recommendations

#### 7.6 API Integration
- [ ] Create `services/portal/src/hooks/useProviders.ts`
- [ ] Create `services/portal/src/hooks/useProviderConnection.ts`
- [ ] Create `services/portal/src/types/providers.ts`
- [ ] API endpoints for provider management

#### 7.7 Provider Logos
- [ ] Add logos to `services/portal/public/logos/`
- [ ] AWS, GCP, Azure, Vultr, RunPod, DigitalOcean
- [ ] Linode, Hetzner, Lambda, CoreWeave, Paperspace
- [ ] Kubernetes, Docker, On-Premises icons

### Deliverables
- ✅ Complete provider management UI
- ✅ Provider configuration forms
- ✅ Multi-cloud dashboard
- ✅ All provider logos
- ✅ Mobile-responsive design

### Testing
- [ ] Test all UI components
- [ ] Test provider add/edit/delete flows
- [ ] Test connection testing
- [ ] Test on mobile devices
- [ ] User acceptance testing

---

## 📊 Progress Tracking

| Phase | Status | Progress | Completion Date |
|-------|--------|----------|-----------------|
| 6.6.1 | 🔄 In Progress | 0% | - |
| 6.6.2 | ⏳ Pending | 0% | - |
| 6.6.3 | ⏳ Pending | 0% | - |
| 6.6.4 | ⏳ Pending | 0% | - |
| 6.6.5 | ⏳ Pending | 0% | - |
| 6.6.6 | ⏳ Pending | 0% | - |
| 6.6.7 | ⏳ Pending | 0% | - |

---

## 🎯 Success Criteria

After Phase 6.6 completion:

- [x] Architecture documented in ARCHITECTURE_OVERVIEW.md
- [ ] Generic Collector supports 15+ providers
- [ ] Single codebase handles all non-Big-3 providers
- [ ] Add new provider in <1 hour (configuration only)
- [ ] Prometheus-only mode works universally
- [ ] Optional API integration for billing data
- [ ] Complete Portal UI for provider management
- [ ] 90%+ test coverage
- [ ] Production-ready documentation
- [ ] Vultr demo working end-to-end

---

## 📝 Notes

- Focus on Vultr first (for demo)
- RunPod second (common GPU cloud)
- Other providers can be added incrementally
- Prometheus-only mode is the minimum viable product
- API integration is optional enhancement

---

**Last Updated:** October 30, 2025  
**Next Update:** After Phase 6.6.1 completion
