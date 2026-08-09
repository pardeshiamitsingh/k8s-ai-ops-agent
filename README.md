# Kubernetes AI Ops Agent
An enterprise-grade **Agentic AI platform for Kubernetes incident investigation and remediation**, built with **LangGraph, LangChain, Azure OpenAI, RAG, MCP, and Kubernetes**.

The goal of this project is to demonstrate how an AI agent can move beyond simple chatbot interactions and perform a controlled, observable, and evaluable incident-response workflow.

---

## 🚀 Project Overview
Kubernetes incidents often require engineers to inspect multiple sources of information:

- Pod and container status
- Kubernetes events
- Logs
- Deployments
- Services
- ConfigMaps and Secrets
- Resource utilization
- Application documentation
- Historical incidents

This project provides an AI-powered incident investigation workflow that can:

1. Receive a Kubernetes incident.
2. Triage the incident using an LLM.
3. Retrieve relevant operational documentation using RAG.
4. Investigate the Kubernetes cluster using tools.
5. Coordinate multiple agentic steps using LangGraph.
6. Ask for human approval before performing risky operations.
7. Execute approved Kubernetes remediation actions.
8. Evaluate the quality and reliability of the AI response.
9. Provide observability into the agent workflow.

---

## 🏗️ Architecture

```
                         ┌──────────────────────┐
                         │      Client/API      │
                         │      FastAPI         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      LangGraph      │
                         │   Agent Workflow    │
                         └──────────┬───────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
          ┌────────────┐     ┌────────────┐     ┌─────────────┐
          │   Triage   │     │    RAG     │     │Investigation│
          │   Agent    │     │   Agent    │     │    Agent     │
          └─────┬──────┘     └─────┬──────┘     └──────┬──────┘
                │                  │                   │
                │                  ▼                   │
                │           ┌──────────────┐           │
                │           │ Vector Store │           │
                │           │ Azure Search │           │
                │           └──────────────┘           │
                │                                      │
                └──────────────────┬───────────────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │   MCP Gateway    │
                          │                  │
                          │ Tools / Context  │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │ Kubernetes Tools │
                          │                  │
                          │ Pods             │
                          │ Events           │
                          │ Logs             │
                          │ Deployments      │
                          └────────┬─────────┘
                                   │
                                   ▼
                             ┌───────────┐
                             │    AKS    │
                             └───────────┘

                         Human Approval
                              ▲
                              │
                       ┌──────┴──────┐
                       │     HITL     │
                       │  Guardrails  │
                       └─────────────┘
```

---

## ✨ Key Capabilities

### Agentic AI
The system uses **LangGraph** to orchestrate stateful agent workflows.

The workflow supports:

- Agent state management
- Conditional routing
- Tool calling
- Structured LLM output
- Retry and recovery
- Human-in-the-loop decisions
- Multi-step reasoning workflows
- Controlled remediation

---

### LLM Abstraction
The project uses an LLM factory pattern to allow the same agent implementation to work with multiple providers.

Supported providers include:

- Azure OpenAI
- Ollama
- AWS Bedrock
- Fake/Test LLM

Example:

```
                    LLMFactory
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       Azure          Ollama        Bedrock
       OpenAI
```

This allows local development with Ollama while supporting Azure OpenAI for production deployment.

---

## 🔎 Retrieval-Augmented Generation
The RAG pipeline provides the agent with operational knowledge that may not be available from the LLM itself.

Potential knowledge sources include:

- Kubernetes runbooks
- Service documentation
- Troubleshooting guides
- Previous incidents
- Architecture documentation
- Operational policies

The pipeline will support:

```
Documents
    │
    ▼
Chunking
    │
    ▼
Embeddings
    │
    ▼
Vector Database
    │
    ▼
Semantic Search
    │
    ▼
Reranking
    │
    ▼
Agent Context
```

---

## 🔌 MCP Integration
The project uses **Model Context Protocol (MCP)** to provide a standardized interface between AI agents and enterprise tools.

Potential MCP tools include:

```
get_pod_status
get_pod_logs
get_kubernetes_events
get_deployment
get_service
describe_resource
restart_deployment
scale_deployment
```

MCP provides a modular boundary between the AI agent and operational systems.

---

## ☸️ Kubernetes Integration
The agent can investigate Kubernetes resources such as:

- Pods
- Deployments
- Services
- Events
- Nodes
- ReplicaSets
- ConfigMaps

Example investigation:

```
Incident:
"payment-service pods are repeatedly being OOMKilled"

        ↓

Triage Agent

        ↓

Hypothesis:
Memory exhaustion

        ↓

Kubernetes Investigation

        ↓

Pod status
Container restart count
OOMKilled reason
Resource limits
Recent events
Logs

        ↓

Root Cause Analysis

        ↓

Recommended remediation
```

---

## 🧑‍⚖️ Human-in-the-Loop
The system does not allow an AI agent to blindly execute potentially destructive Kubernetes operations.

Actions are classified by risk.

Example:

```
READ OPERATIONS
    │
    ├── get pods
    ├── get events
    ├── get logs
    └── describe deployment

        ↓

Automatic execution

WRITE OPERATIONS
    │
    ├── restart deployment
    ├── scale deployment
    └── modify configuration

        ↓

Human Approval Required
```

The human can:

```
APPROVE
REJECT
MODIFY
```

before the operation is executed.

---

## 🛡️ Guardrails
The agent is designed with multiple safety boundaries:

- Structured LLM outputs
- Tool allowlists
- Input validation
- Output validation
- Kubernetes RBAC
- Human approval for risky operations
- Prompt injection protection
- Audit logging
- Rate limiting
- Timeout and retry policies

---

## 📊 Evaluation
Agentic systems require more than traditional unit tests.

The project includes evaluation for:

### RAG

- Context Recall
- Context Precision
- Faithfulness
- Groundedness

### Agent

- Tool selection accuracy
- Tool execution success
- Task completion rate
- Reasoning consistency
- Hallucination rate

### Production

- Latency
- Token usage
- Cost
- Failure rate
- Human intervention rate

Evaluation frameworks such as **Ragas** can be integrated into the evaluation pipeline.

---

## 🧪 Testing
The project uses `pytest` for automated testing.

Run all tests:

```
python -m pytest
```

Run with verbose output:

```
python -m pytest -v
```

Run a specific test:

```
python -m pytest tests/unit/test_triage.py -v
```

The architecture supports dependency injection so LLMs can be mocked during tests.

Example:

```
Test
 │
 ▼
Mock LLM
 │
 ▼
Triage Agent
 │
 ▼
Structured IncidentAnalysis
```

This allows tests to run without requiring Azure OpenAI or Ollama.

---

## 🧰 Technology Stack

| Area | Technology |
|------|-----------|
| Language | Python |
| Agent Framework | LangGraph |
| LLM Framework | LangChain |
| LLM | Azure OpenAI |
| Local LLM | Ollama |
| RAG | LangChain |
| Vector Search | Azure AI Search |
| MCP | Model Context Protocol |
| API | FastAPI |
| Containerization | Docker |
| Orchestration | Kubernetes |
| Cloud | Microsoft Azure |
| Kubernetes Platform | AKS |
| Testing | pytest |
| Observability | Prometheus / Grafana |
| CI/CD | GitHub Actions |
| Evaluation | Ragas / Custom Evaluations |

---

## 📁 Project Structure

```
k8s-ai-ops-agent/
│
├── src/
│   └── k8s_ai_ops/
│       │
│       ├── agents/
│       │   └── triage.py
│       │
│       ├── graph/
│       │   ├── state.py
│       │   └── workflow.py
│       │
│       ├── llm/
│       │   ├── factory.py
│       │   ├── settings.py
│       │   └── providers/
│       │       ├── azure.py
│       │       ├── bedrock.py
│       │       ├── ollama.py
│       │       └── fake.py
│       │
│       ├── models/
│       │   └── incident.py
│       │
│       ├── config/
│       │   └── settings.py
│       │
│       ├── rag/
│       │   └── (future)
│       │
│       ├── mcp/
│       │   └── (future)
│       │
│       ├── tools/
│       │   └── (future)
│       │
│       └── api/
│           └── main.py
│
├── tests/
│   └── unit/
│       ├── test_triage.py
│       └── test_llm_factory.py
│
├── .env.example
├── .env
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## ⚙️ Local Development

### Prerequisites

- Python 3.12+
- Git
- Docker
- Kubernetes / Kind or Minikube
- Ollama

For Azure deployment:

- Azure subscription
- Azure OpenAI
- Azure AI Search
- Azure Kubernetes Service (AKS)

---

### Setup

Clone the repository:

```bash
git clone <your-repository-url>
cd k8s-ai-ops-agent
```

Create a virtual environment:

```bash
python3.12 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -e .
```

Install development dependencies:

```bash
pip install -e ".[dev]"
```

---

## 🤖 Local LLM with Ollama

Start Ollama:

```bash
ollama serve
```

Pull the model:

```bash
ollama pull llama3.1:8b
```

Configure `.env`:

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
LLM_TEMPERATURE=0.0
```

---

## ☁️ Azure OpenAI

For Azure development:

```bash
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_API_VERSION=<api-version>
AZURE_OPENAI_DEPLOYMENT=<deployment-name>
```

Secrets should never be committed to Git.

---

## 🚀 Running the API

Start the FastAPI application:

```bash
PYTHONPATH=src uvicorn k8s_ai_ops.api.main:app --reload
```

- **API**: http://localhost:8000
- **Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🐳 Docker

Build the image:

```bash
docker build -t k8s-ai-ops-agent .
```

Run:

```bash
docker run -p 8000:8000 k8s-ai-ops-agent
```

---

## ☸️ AKS Deployment

The production architecture targets Azure Kubernetes Service:

```
                  Azure
                    │
          ┌─────────┴─────────┐
          │                   │
      Azure OpenAI       Azure AI Search
          │                   │
          └─────────┬─────────┘
                    │
                    ▼
                 AKS
                    │
          ┌─────────┴─────────┐
          │                   │
       AI Agent           MCP Server
          │                   │
          └─────────┬─────────┘
                    │
                    ▼
              Kubernetes APIs
```

Deployment manifests and Helm configuration will be added as the project progresses.

---

## 🔐 Security Considerations

The project follows enterprise AI security principles:

- Secrets stored outside source control
- Kubernetes RBAC
- Least-privilege service accounts
- Tool-level authorization
- Human approval for destructive operations
- Input/output validation
- Audit trails
- Prompt injection defenses
- Network isolation
- Secure API authentication

---

## 🗺️ Roadmap

### Phase 1 — Foundation ✅

- Python project setup
- LLM configuration
- LLM factory
- Ollama integration
- Incident models
- Initial triage agent
- Unit tests

### Phase 2 — LangGraph

- Agent state
- Triage node
- Investigation node
- RAG node
- Remediation node
- Conditional routing
- Retry/recovery

### Phase 3 — RAG

- Document ingestion
- Chunking
- Embeddings
- Vector search
- Hybrid retrieval
- Reranking
- Citation/grounding

### Phase 4 — MCP

- MCP server
- Kubernetes tools
- Tool schemas
- Tool authorization
- Tool error handling

### Phase 5 — Human-in-the-Loop

- Risk classification
- Approval workflow
- Approval/rejection
- Audit trail

### Phase 6 — Evaluation

- RAG evaluation
- Agent evaluation
- Tool-call evaluation
- LLM-as-a-Judge
- Regression dataset
- Automated evaluation pipeline

### Phase 7 — Production

- Docker
- Kubernetes manifests
- AKS deployment
- CI/CD
- Observability
- Prometheus/Grafana
- Logging
- Distributed tracing
- Security hardening

---

## 🎯 Why This Project?

This project demonstrates practical experience building **production-oriented Agentic AI systems**, rather than a simple LLM chatbot.

It combines:

- Agent orchestration
- LLM integration
- RAG
- MCP
- Kubernetes
- Cloud-native architecture
- Human-in-the-loop controls
- AI evaluation
- Observability
- CI/CD
- Enterprise security

The architecture is designed to evolve from a local development environment using Ollama into a production deployment using **Azure OpenAI and AKS**.

---

## 📌 Current Status

The project is currently in the **foundation phase**.

Current capabilities include:

- LLM provider abstraction
- Ollama support
- Structured incident analysis
- Kubernetes incident triage
- LangChain integration
- Unit testing

The remaining components will be implemented incrementally, with an emphasis on production-grade architecture, testing, observability, and responsible AI practices.
