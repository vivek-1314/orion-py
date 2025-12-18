# Orion — System Design (Technical)
` Orion (memory foundation) is designed as a memory-augmented, agent-orchestrated system that prioritizes: `
 - structured long-term memory
 - predictable behavior
 - low token usage
 - scalable execution


###### The system separates probabilistic reasoning (LLMs) from deterministic system responsibilities such as memory management, routing, and retrieval.

## High-Level Architecture

```Orion follows a node-based execution graph, where each node has a single, clearly defined responsibility.```

```sh 
START
  ↓
Segmentation Node (LLM)
  ↓
Classification Node (Deterministic)
  ↓
Router Node
  ↓
┌───────────────┬────────────────┐
│ Memory Writer │ Memory Reader  │  (async / parallel)
└───────────────┴────────────────┘
  ↓
Final Answer Node (LLM)
  ↓
END
```


Parallelism is introduced after intent and memory classification, ensuring that expensive I/O operations do not block response generation.

### Node Responsibilities
#### 1. Segmentation Node (LLM-based)

###### Responsibility:
  - Analyze raw user input
  - Segment it into atomic units
  - Identify memory intent signals

###### Output categories:

 - memory_to_write
 - question - [basically memories to fetch]
 - ignore

##### This node is the only place where ambiguity is handled probabilistically.
It does not perform storage, retrieval, or routing.

#### 2. Classification Node (Deterministic)

###### Responsibility:

> Assign explicit memory types to segmented items
> Classification is rule-based and deterministic:

 - Identity → regex-based matching
 - Habits → frequency indicators
 - Preferences → explicit liking signals
 - Events → temporal indicators
 - Tasks → reminder / deadline patterns
 - Unknown → safe fallback


#### This design:
 - removes memory typing from the LLM
 - ensures predictable schemas
 - enables reliable downstream routing


#### 3. Router Node (Orchestration Layer)

###### Responsibility:

 - Acts as the central orchestrator for memory operations
 - Receives classified signals from the previous node
 - Triggers memory writes and memory reads in parallel

> Maintain a unified execution state


## Memory Subsystem

```Orion uses a dual-store memory architecture, separating semantic recall from structured storage.```

> Memory Writing Pipeline (Asynchronous)
> Memory writes are fully parallelized.

```sh 
For each memory item:
  ├─ Generate embedding
  ├─ Check if memory already exists (similarity)
  ├─ Upsert vector representation
  └─ Store structured data + metadata
```

#### Key properties:
 - Each memory item is processed independently
 - Writes run concurrently using asyncio.gather
 - Vector and relational writes execute in parallel
 - TTL logic is applied at write time (e.g., events)


#### This ensures:

 - low latency
 - non-blocking execution
 - scalable ingestion under load

## Memory Storage Strategy

#### `Semantic Store (Vector DB):`
 - Used only for similarity matching
 - Stores embeddings + minimal metadata
 - Optimized for recall, not structure

#### `Structured Store (Relational / JSONB):`
 - Stores canonical memory text
 - Maintains TTL, type, ownership, traceability
 - Enables deterministic access (e.g., identity fields)

> No single storage system is overloaded with conflicting responsibilities.

## Memory Reading Pipeline

Memory retrieval adapts based on memory type:

#### Identity memories

 - Retrieved deterministically from structured storage
 - No embeddings involved

#### Preferences / Habits / Events

 - Query text is embedded
 - Semantic similarity search is performed
 - Canonical memory text is fetched from structured storage

> Current behavior retrieves the most relevant match per query item.
> Set-based aggregation is intentionally deferred until memory correctness > is fully validated.

## Parallel Execution Model
Parallelism is a core design principle:

 - Memory reads and writes run concurrently
 - Vector DB and relational DB operations run in parallel
 - I/O-heavy tasks do not block response generation

This is achieved using:
 - async/await `[asyncio in python]`
 - task-level concurrency
 - stateless node execution

> The system is designed to scale horizontally without architectural > changes.

## Final Answer Generation

###### The LLM is invoked once per user query, after:

 - memory writes are scheduled
 - memory reads have completed
 - relevant context is curated

###### The model receives:

 - clean user input
 - selectively retrieved memory context
 - no raw conversation history dumps
###### This significantly reduces:

 - token usage
 - hallucinations
 - response variance

#### Performance & Optimization Principles

 - Minimal LLM calls per request
 - Deterministic logic wherever possible 
 - Parallel I/O over sequential workflows
 - Stateless nodes with shared execution state
 - Explicit memory lifecycles (TTL, updates)

#### These choices lead to:

 - predictable latency
 - lower operational cost
 - modular, testable components

#### Current Capabilities

 - Structured memory ingestion
 - Deterministic memory classification
 - Semantic memory recall
 - Parallel memory operations
 - Single-pass answer generation

#### Known Limitations (By Design)
 - Set-based query aggregation is not yet implemented
 - Query intent differentiation is minimal
 - Proactive execution is gated behind memory validation

 > These are intentional constraints to preserve system correctness.

#### Design Intent Going Forward

Future extensions will focus on:
 - intent-aware retrieval strategies
 - controlled aggregation over memory sets
 - time-bounded and status-based queries
 - proactive execution triggers

> All additions will preserve the core principles of determinism, efficiency, and observability.

## Final Note

`` Orion is not optimized for demo behavior.

It is optimized for long-term correctness, scalability, and personalization discipline. ``
