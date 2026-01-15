# Bloom API Documentation

Complete API reference for Bloom's REST API and WebSocket protocol.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [API Endpoints](#api-endpoints)
  - [Evaluation Management](#evaluation-management)
  - [Peer Selection](#peer-selection)
  - [Feedback Submission](#feedback-submission)
  - [Manager Evaluation](#manager-evaluation)
  - [Agent Management](#agent-management)
  - [Metrics & Analytics](#metrics--analytics)
- [WebSocket Protocol](#websocket-protocol)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Webhooks](#webhooks)
- [SDKs & Examples](#sdks--examples)

## Overview

Bloom provides a RESTful API for programmatic access to the evaluation system. All responses are in JSON format.

**API Version**: v1
**Protocol**: HTTPS
**Content-Type**: `application/json`

## Authentication

Bloom uses JWT (JSON Web Tokens) for authentication.

### Obtaining a Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@company.com",
  "password": "your-password"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Using the Token

Include the token in the `Authorization` header:

```http
GET /api/v1/evaluations/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Refreshing Tokens

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

## Base URL

**Production**: `https://bloom.company.com/api/v1`
**Staging**: `https://bloom-staging.company.com/api/v1`
**Development**: `http://localhost:8000/api/v1`

## API Endpoints

### Evaluation Management

#### List Evaluations

Get evaluations for the authenticated user.

```http
GET /api/v1/evaluations
Authorization: Bearer {token}
```

**Query Parameters**:
- `cycle` (optional): Filter by cycle name
- `status` (optional): Filter by state (e.g., `peer_feedback_in_progress`)
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset

**Response**:
```json
{
  "evaluations": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "employee_id": "123e4567-e89b-12d3-a456-426614174000",
      "employee_name": "Jane Doe",
      "manager_id": "123e4567-e89b-12d3-a456-426614174001",
      "manager_name": "John Smith",
      "cycle_name": "Q4 2024",
      "current_phase": "data_gathering",
      "current_state": "peer_feedback_in_progress",
      "completion_percentage": 0.4,
      "deadlines": {
        "peer_feedback_deadline": "2024-12-15T17:00:00Z",
        "self_eval_deadline": "2024-12-15T17:00:00Z"
      },
      "created_at": "2024-11-01T09:00:00Z",
      "updated_at": "2024-11-15T14:30:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Get Evaluation by ID

```http
GET /api/v1/evaluations/{evaluation_id}
Authorization: Bearer {token}
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "employee_id": "123e4567-e89b-12d3-a456-426614174000",
  "employee": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Jane Doe",
    "email": "jane.doe@company.com",
    "title": "Senior Software Engineer",
    "level": "L3"
  },
  "manager_id": "123e4567-e89b-12d3-a456-426614174001",
  "manager": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "John Smith",
    "email": "john.smith@company.com"
  },
  "cycle_name": "Q4 2024",
  "current_phase": "data_gathering",
  "current_state": "peer_feedback_in_progress",
  "suggested_peers": ["uuid1", "uuid2", "uuid3"],
  "employee_selected_peers": ["uuid1", "uuid2", "uuid4"],
  "manager_approved_peers": ["uuid1", "uuid2"],
  "peer_feedbacks": [
    {
      "id": "fb-uuid-1",
      "peer_id": "uuid1",
      "peer_name": "Alice Johnson",
      "submitted_at": "2024-12-05T10:00:00Z",
      "is_synthesized": true
    }
  ],
  "self_evaluation": {
    "id": "se-uuid",
    "submitted_at": "2024-12-10T15:00:00Z"
  },
  "deadlines": {
    "peer_selection_deadline": "2024-12-01T17:00:00Z",
    "peer_feedback_deadline": "2024-12-15T17:00:00Z",
    "self_eval_deadline": "2024-12-15T17:00:00Z",
    "manager_eval_deadline": "2024-12-22T17:00:00Z"
  },
  "state_history": [
    {
      "from_state": "cycle_started",
      "to_state": "peer_suggestion_generated",
      "timestamp": "2024-11-01T09:30:00Z"
    }
  ],
  "created_at": "2024-11-01T09:00:00Z",
  "updated_at": "2024-12-10T15:00:00Z"
}
```

#### Start Evaluation Cycle

Create evaluations for a cohort of employees. (Admin only)

```http
POST /api/v1/evaluations/cycles
Authorization: Bearer {token}
Content-Type: application/json

{
  "cycle_name": "Q4 2024",
  "employee_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "123e4567-e89b-12d3-a456-426614174002"
  ],
  "start_date": "2024-11-01T00:00:00Z"
}
```

**Response**:
```json
{
  "cycle_name": "Q4 2024",
  "evaluations_created": 2,
  "evaluation_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ],
  "deadlines": {
    "peer_selection": "2024-11-08T17:00:00Z",
    "peer_feedback": "2024-11-22T17:00:00Z"
  }
}
```

### Peer Selection

#### Get Peer Suggestions

Get AI-suggested peer reviewers.

```http
GET /api/v1/evaluations/{evaluation_id}/peers/suggestions
Authorization: Bearer {token}
```

**Response**:
```json
{
  "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
  "suggestions": [
    {
      "peer_id": "uuid1",
      "peer_name": "Alice Johnson",
      "peer_title": "Staff Engineer",
      "score": 0.92,
      "justification": "Strong collaboration: 28 shared meetings, 45 Jira collaborations, 12 code collaborations",
      "breakdown": {
        "calendar_meetings": 28,
        "jira_interactions": 45,
        "git_collaborations": 12,
        "slack_messages": 156
      }
    },
    {
      "peer_id": "uuid2",
      "peer_name": "Bob Chen",
      "peer_title": "Senior Engineer",
      "score": 0.85,
      "justification": "Strong collaboration: frequent meeting collaboration (22 meetings), 38 Jira collaborations",
      "breakdown": {
        "calendar_meetings": 22,
        "jira_interactions": 38,
        "git_collaborations": 8,
        "slack_messages": 98
      }
    }
  ],
  "total_candidates_analyzed": 45,
  "time_window_days": 180
}
```

#### Submit Peer Selection

Employee submits their peer selection.

```http
POST /api/v1/evaluations/{evaluation_id}/peers/select
Authorization: Bearer {token}
Content-Type: application/json

{
  "selected_peer_ids": ["uuid1", "uuid2", "uuid3", "uuid4", "uuid5"]
}
```

**Response**:
```json
{
  "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
  "selected_peers": [
    {
      "peer_id": "uuid1",
      "peer_name": "Alice Johnson",
      "peer_title": "Staff Engineer"
    }
  ],
  "status": "pending_manager_approval",
  "next_deadline": "2024-11-08T17:00:00Z"
}
```

#### Approve Peer Selection

Manager approves the peer list.

```http
POST /api/v1/evaluations/{evaluation_id}/peers/approve
Authorization: Bearer {token}
Content-Type: application/json

{
  "approved_peer_ids": ["uuid1", "uuid2", "uuid3"],
  "notes": "Approved selection with minor modifications"
}
```

**Response**:
```json
{
  "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
  "approved_peers": [
    {
      "peer_id": "uuid1",
      "peer_name": "Alice Johnson"
    }
  ],
  "status": "peer_list_locked",
  "next_phase": "data_gathering"
}
```

### Feedback Submission

#### Submit Peer Feedback

Submit feedback for a peer.

```http
POST /api/v1/evaluations/{evaluation_id}/feedback/peer
Authorization: Bearer {token}
Content-Type: application/json

{
  "raw_feedback": "Jane did exceptional work on the API migration project. She handled complex database issues with expertise and mentored junior team members throughout the process. Her communication during incidents was clear and calm.",
  "input_method": "voice",
  "technical_rating": "exceeds",
  "leadership_rating": "meets",
  "communication_rating": "exceeds",
  "collaboration_rating": "exceeds"
}
```

**Response**:
```json
{
  "id": "fb-uuid-1",
  "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
  "peer_id": "uuid1",
  "submitted_at": "2024-12-05T10:00:00Z",
  "synthesized_feedback": "Jane demonstrated exceptional technical expertise during the API migration project, handling complex database challenges effectively. She provided valuable mentorship to junior engineers and maintained clear, professional communication during critical incidents.",
  "themes": ["technical_excellence", "leadership", "collaboration"],
  "status": "synthesized"
}
```

#### Submit Self-Evaluation

```http
POST /api/v1/evaluations/{evaluation_id}/self-evaluation
Authorization: Bearer {token}
Content-Type: application/json

{
  "raw_achievements": "This year I led the API migration from v1 to v2, resulting in 40% performance improvement. I also mentored 3 junior engineers and contributed to 5 major releases.",
  "raw_challenges": "Balancing project work with mentorship responsibilities was challenging during peak periods.",
  "raw_growth_areas": "I want to improve my skills in distributed systems design and strategic planning.",
  "raw_goals": "Lead a major architecture initiative and grow into a staff engineer role.",
  "uploaded_docs": [
    {
      "name": "API_Migration_Deck.pdf",
      "url": "https://storage.company.com/docs/abc123.pdf"
    }
  ],
  "project_links": [
    "https://github.com/company/api/pull/1234",
    "https://company.atlassian.net/browse/ENG-5678"
  ]
}
```

**Response**:
```json
{
  "id": "se-uuid",
  "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
  "submitted_at": "2024-12-10T15:00:00Z",
  "synthesized_achievements": "Led the successful API migration from v1 to v2, achieving a 40% performance improvement. Provided mentorship to three junior engineers while contributing to five major product releases.",
  "status": "synthesized"
}
```

### Manager Evaluation

#### Generate AI Draft

Trigger AI draft generation for manager evaluation.

```http
POST /api/v1/evaluations/{evaluation_id}/manager-evaluation/generate-draft
Authorization: Bearer {token}
```

**Response**:
```json
{
  "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
  "draft": {
    "summary": "Based on analysis of 5 peer reviews and self-evaluation, Jane demonstrated exceptional performance across multiple dimensions. Her technical leadership on the API migration project and mentorship of junior engineers highlight significant impact beyond individual contributions.",
    "sections": {
      "technical": "Demonstrated strong technical excellence through successful API migration project, achieving measurable performance improvements. [Supported by: 4 peer feedback(s)]",
      "leadership": "Provided effective mentorship to junior engineers and demonstrated calm leadership during incident response. [Supported by: 3 peer feedback(s)]",
      "communication": "Maintained clear and professional communication across teams, particularly during critical incidents. [Supported by: 4 peer feedback(s)]"
    }
  },
  "clarifying_questions": [
    {
      "question": "Can you provide specific examples of Jane's strategic thinking during the API migration?",
      "category": "technical",
      "priority": "high"
    }
  ],
  "peer_feedbacks_analyzed": 5,
  "themes_identified": 12,
  "evidence_citations": 18,
  "generated_at": "2024-12-18T10:00:00Z"
}
```

#### Submit Manager Evaluation

```http
POST /api/v1/evaluations/{evaluation_id}/manager-evaluation
Authorization: Bearer {token}
Content-Type: application/json

{
  "final_summary": "Jane has exceeded expectations this year through her technical leadership and mentorship contributions...",
  "technical_assessment": "Exceptional technical skills demonstrated through successful API migration...",
  "leadership_assessment": "Strong mentorship and incident leadership...",
  "growth_opportunities": "Focus on strategic planning and architecture design...",
  "overall_rating": "exceeds",
  "technical_rating": "exceeds",
  "leadership_rating": "meets",
  "communication_rating": "exceeds",
  "promotion_eligibility": "ready_next_cycle",
  "promotion_justification": "Jane is developing the strategic thinking and architecture skills needed for staff level...",
  "manager_responses": [
    {
      "question_id": "q1",
      "response": "Jane led the architecture design for the API migration, considering scalability, performance, and backward compatibility."
    }
  ]
}
```

**Response**:
```json
{
  "id": "me-uuid",
  "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
  "submitted_at": "2024-12-20T16:00:00Z",
  "status": "manager_eval_complete",
  "next_phase": "calibration"
}
```

### Agent Management

#### Get Swarm Status

Get status of all agents in the system. (Admin only)

```http
GET /api/v1/agents/status
Authorization: Bearer {token}
```

**Response**:
```json
{
  "orchestrator_id": "orch-uuid",
  "is_running": true,
  "uptime_seconds": 86400,
  "agents": {
    "watchkeeper": {
      "id": "agent-uuid-1",
      "status": "IDLE",
      "workload": 0.1,
      "tasks_completed": 150,
      "uptime_seconds": 86400
    },
    "context_miners": [
      {
        "id": "agent-uuid-2",
        "status": "EXECUTING",
        "workload": 0.6,
        "current_task": "Generating peer suggestions for eval-uuid-123"
      }
    ],
    "scribes": [
      {
        "id": "agent-uuid-3",
        "status": "IDLE",
        "workload": 0.2,
        "rag_generations_today": 45
      },
      {
        "id": "agent-uuid-4",
        "status": "EXECUTING",
        "workload": 0.8,
        "current_task": "Synthesizing peer feedback fb-uuid-789"
      }
    ],
    "chasers": [
      {
        "id": "agent-uuid-5",
        "status": "IDLE",
        "reminders_sent_today": 28,
        "upcoming_deadlines": 15
      }
    ],
    "gatekeeper": {
      "id": "agent-uuid-6",
      "status": "IDLE",
      "access_checks_today": 1250
    },
    "analyst": {
      "id": "agent-uuid-7",
      "status": "IDLE",
      "reports_generated_today": 5
    }
  },
  "active_evaluations": 87,
  "background_tasks": 6,
  "database_stats": {
    "document_store": {
      "collections": 5,
      "total_documents": 1523
    },
    "vector_store": {
      "total_vectors": 4589
    }
  }
}
```

#### Get Agent Metrics

```http
GET /api/v1/agents/{agent_id}/metrics
Authorization: Bearer {token}
```

**Query Parameters**:
- `start_time`: ISO 8601 timestamp
- `end_time`: ISO 8601 timestamp
- `metric`: Specific metric name (optional)

**Response**:
```json
{
  "agent_id": "agent-uuid-3",
  "agent_type": "Scribe",
  "metrics": [
    {
      "timestamp": "2024-12-01T10:00:00Z",
      "metric": "task_execution_time",
      "value": 28.5,
      "unit": "seconds"
    },
    {
      "timestamp": "2024-12-01T10:15:00Z",
      "metric": "workload",
      "value": 0.65,
      "unit": "ratio"
    }
  ],
  "summary": {
    "avg_execution_time": 25.3,
    "avg_workload": 0.45,
    "tasks_completed": 245,
    "success_rate": 0.98
  }
}
```

### Metrics & Analytics

#### Get Evaluation Metrics

```http
GET /api/v1/metrics/evaluations
Authorization: Bearer {token}
```

**Query Parameters**:
- `cycle` (optional): Filter by cycle name
- `start_date` (optional): Start date for metrics
- `end_date` (optional): End date for metrics

**Response**:
```json
{
  "cycle_name": "Q4 2024",
  "total_evaluations": 250,
  "by_phase": {
    "context_peer_selection": 10,
    "data_gathering": 45,
    "manager_evaluation": 120,
    "calibration": 50,
    "release_discussion": 20,
    "completed": 5
  },
  "completion_rate": 0.02,
  "avg_completion_time_days": 42,
  "deadline_compliance": {
    "peer_selection": 0.95,
    "peer_feedback": 0.88,
    "self_eval": 0.92,
    "manager_eval": 0.85
  },
  "rating_distribution": {
    "exceptional": 15,
    "exceeds": 75,
    "meets": 140,
    "developing": 15,
    "not_meeting": 5
  }
}
```

#### Get System Health

```http
GET /api/v1/health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 86400,
  "health_score": 0.98,
  "databases": {
    "postgres": "connected",
    "redis": "connected",
    "neo4j": "connected",
    "influxdb": "connected",
    "vector_db": "connected"
  },
  "checks": {
    "agents_running": true,
    "database_connectivity": true,
    "external_apis": true
  }
}
```

## WebSocket Protocol

Bloom provides real-time updates via WebSocket connections.

### Connection

```javascript
const ws = new WebSocket('wss://bloom.company.com/api/v1/ws');

// Authenticate
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your-jwt-token'
}));

// Subscribe to evaluation updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'evaluations',
  filters: {
    evaluation_id: '550e8400-e29b-41d4-a716-446655440000'
  }
}));
```

### Message Types

#### State Change Event

```json
{
  "type": "state_change",
  "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
  "from_state": "peer_feedback_in_progress",
  "to_state": "self_eval_requested",
  "timestamp": "2024-12-10T14:00:00Z",
  "actor": {
    "id": "system",
    "type": "agent",
    "name": "Watchkeeper"
  }
}
```

#### Feedback Submitted Event

```json
{
  "type": "feedback_submitted",
  "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
  "feedback_id": "fb-uuid-1",
  "peer_id": "uuid1",
  "peer_name": "Alice Johnson",
  "timestamp": "2024-12-05T10:00:00Z"
}
```

#### Deadline Approaching Event

```json
{
  "type": "deadline_approaching",
  "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
  "deadline_type": "peer_feedback",
  "due_date": "2024-12-15T17:00:00Z",
  "time_remaining_hours": 48,
  "status": "approaching"
}
```

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| 1000 | 400 Bad Request | Invalid request parameters |
| 1001 | 401 Unauthorized | Authentication required |
| 1002 | 403 Forbidden | Insufficient permissions |
| 1003 | 404 Not Found | Resource not found |
| 1004 | 409 Conflict | State transition conflict |
| 1005 | 422 Unprocessable Entity | Validation error |
| 1006 | 429 Too Many Requests | Rate limit exceeded |
| 2000 | 500 Internal Server Error | Server error |
| 2001 | 503 Service Unavailable | Service temporarily unavailable |

**Error Response Format**:

```json
{
  "error": {
    "code": 1005,
    "message": "Validation error: selected_peer_ids is required",
    "details": {
      "field": "selected_peer_ids",
      "constraint": "required"
    },
    "request_id": "req-uuid-123"
  }
}
```

## Rate Limiting

API requests are rate-limited per user:

- **Standard Users**: 1000 requests/hour
- **Managers**: 2000 requests/hour
- **Admins**: 5000 requests/hour

**Rate Limit Headers**:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 997
X-RateLimit-Reset: 1638360000
```

When rate limit is exceeded:

```json
{
  "error": {
    "code": 1006,
    "message": "Rate limit exceeded",
    "retry_after_seconds": 3600
  }
}
```

## Webhooks

Bloom can send webhooks to external systems for key events.

### Configuration

```http
POST /api/v1/webhooks
Authorization: Bearer {token}
Content-Type: application/json

{
  "url": "https://company.com/webhooks/bloom",
  "events": ["evaluation.state_changed", "evaluation.completed"],
  "secret": "webhook-secret-for-signature"
}
```

### Webhook Payload

```json
{
  "event": "evaluation.state_changed",
  "timestamp": "2024-12-10T14:00:00Z",
  "data": {
    "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
    "from_state": "peer_feedback_in_progress",
    "to_state": "self_eval_requested"
  },
  "signature": "sha256=abc123..."
}
```

**Signature Verification**:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    computed = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={computed}" == signature
```

## SDKs & Examples

### Python SDK

```python
from bloom_sdk import BloomClient

# Initialize client
client = BloomClient(
    base_url="https://bloom.company.com/api/v1",
    api_key="your-api-key"
)

# List evaluations
evaluations = client.evaluations.list(cycle="Q4 2024")

# Get peer suggestions
suggestions = client.evaluations.get_peer_suggestions(
    evaluation_id="550e8400-e29b-41d4-a716-446655440000"
)

# Submit peer feedback
feedback = client.evaluations.submit_peer_feedback(
    evaluation_id="550e8400-e29b-41d4-a716-446655440000",
    raw_feedback="Jane did exceptional work...",
    input_method="voice"
)
```

### JavaScript SDK

```javascript
import { BloomClient } from '@company/bloom-sdk';

const client = new BloomClient({
  baseUrl: 'https://bloom.company.com/api/v1',
  apiKey: 'your-api-key'
});

// List evaluations
const evaluations = await client.evaluations.list({ cycle: 'Q4 2024' });

// Submit self-evaluation
const selfEval = await client.evaluations.submitSelfEvaluation(
  evaluationId,
  {
    raw_achievements: 'This year I led the API migration...',
    raw_goals: 'Lead a major architecture initiative...'
  }
);
```

### cURL Examples

**Get peer suggestions**:

```bash
curl -X GET \
  https://bloom.company.com/api/v1/evaluations/{id}/peers/suggestions \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIs...'
```

**Submit peer feedback**:

```bash
curl -X POST \
  https://bloom.company.com/api/v1/evaluations/{id}/feedback/peer \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIs...' \
  -H 'Content-Type: application/json' \
  -d '{
    "raw_feedback": "Jane did exceptional work on the API migration...",
    "input_method": "voice",
    "technical_rating": "exceeds"
  }'
```

---

For deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md).
For architecture details, see [ARCHITECTURE.md](./ARCHITECTURE.md).
For development guide, see [DEVELOPMENT.md](./DEVELOPMENT.md).
