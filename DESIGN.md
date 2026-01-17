📘 Adaptive AI Tutor: Hackathon Design Document
1. Project Overview
Elevator Pitch: An intelligent tutoring environment that uses AI to "watch" students solve problems in real-time. It ingests textbooks to provide syllabus-aligned help, tracks user weaknesses (e.g., "weak at chain rule") to adapt future guidance, and uses computer vision to correct handwritten math steps instantly.
Target Tracks:
Main: Education Hacks ("Tech Cares")
Category: Best AI Hack, Best UI/UX
Sponsored: Best Use of Gemini (Multimodal), Best Use of MongoDB (Vector Search), Opennote (Productivity)

2. System Architecture
High-Level Flow
Knowledge Base (RAG): The system "reads" a textbook and stores it as vectors.
Adaptive Memory: The system "remembers" what the user gets wrong to customize hints.
Vision Loop: The system "sees" what the user writes on the canvas and identifies errors by step.
Tech Stack
Component
Technology
Purpose
Frontend
React 
Responsive UI & State Management.
Canvas
react-sketch-canvas
Drawing surface for handwriting input.
Math Input
mathlive
fallback for typed equation input.
Backend
FastAPI (Python)
High-speed async API for streaming.
Database
MongoDB Atlas
Vector Search (RAG) + User Profile Store.
LLM (Chat)
Gemini 1.5 Pro
Massive context for textbook reasoning.
LLM (Vision)
Gemini 1.5 Flash
Step-based error detection (no bounding boxes—more reliable than coordinate prediction). 


3. Database Schema (MongoDB)
A. textbook_nodes (The Knowledge)
Stores chunks of the textbook for RAG retrieval.
JSON
{
  "_id": "ObjectId(...)",
  "content": "To solve a quadratic equation using the quadratic formula...",
  "embedding": [0.012, -0.231, ...], // 768-dim vector from Gemini
  "metadata": {
    "chapter": "Quadratics",
    "page": 42,
    "topic": "factorization"
  }
}
B. user_state (The Memory)
Tracks learning history to personalize the AI.
JSON
{
  "_id": "user_123",
  "name": "Alex",
  "weaknesses": {
    "chain_rule": { "error_count": 5, "last_seen": "2024-01-15", "confidence": 0.7 },
    "negative_signs": { "error_count": 12, "last_seen": "2024-01-16", "confidence": 0.9 }
  }
}

C. sessions (Separate Collection)
Stores detailed session logs to avoid unbounded document growth.
JSON
{
  "_id": "ObjectId(...)",
  "user_id": "user_123",
  "problem_id": "p_55",
  "timestamp": "2024-01-16T10:30:00Z",
  "status": "failed",
  "error_type": "chain_rule",
  "steps_attempted": 4
}

4. API Endpoints (FastAPI)
POST /api/chat/stream (Text Helper)
Purpose: Standard chat that uses RAG + User Weaknesses.
Input: { "user_id": "123", "message": "Help me start this problem." }
Logic:
Vector Search textbook_nodes for context.
Fetch user_state to find known weaknesses.
Stream response using Gemini 1.5 Pro.
POST /api/analyze_visual (Vision Helper)
Purpose: Takes a snapshot of the canvas and identifies errors by step number.
Input: { "image": "base64_string...", "problem_context": "Solve for x" }
Logic:
Send image to Gemini 1.5 Flash.
Ask model to detect the first mistake and identify which step contains it.
Response:
JSON
{
  "has_error": true,
  "error_step": 3,
  "error_description": "In step 3, when distributing the negative sign",
  "hint": "Check the sign distribution here. What happens to each term inside the parentheses?"
}

POST /api/generate_problem (Problem Generator) [P2]
Purpose: Generate personalized practice problems targeting user weaknesses.
Input: { "user_id": "123", "topic": "derivatives" }
Logic:
Fetch user weaknesses from user_state.
Use Gemini to generate a problem that exercises weak areas.
Response:
JSON
{
  "problem": "Find the derivative of f(x) = sin(x²)",
  "topic": "derivatives",
  "targets_weakness": "chain_rule",
  "difficulty": "medium"
}

5. Implementation Strategy (36 Hours)
Phase 1: Infrastructure (Fri Night)
[ ] Repo: Set up Monorepo (Client/Server).
[ ] DB: Create MongoDB Atlas Cluster (Free Tier).
[ ] API: Hello World in FastAPI.
[ ] UI: npm install react-sketch-canvas and basic layout.
Phase 2: Core RAG (Sat Morning)
[ ] Ingestion: Write Python script to read textbook.txt, embed with Gemini, save to MongoDB.
[ ] Search: Configure Atlas Vector Search Index (JSON config below).
[ ] Chat: Connect Frontend Chat to Backend stream endpoint.
Phase 3: The "Vision" Feature (Sat Afternoon)
[ ] Canvas: Implement react-sketch-canvas with step separators (horizontal lines or numbered regions).
[ ] Check Button: Add explicit "Check My Work" button (more reliable than auto-debounce).
[ ] Vision Endpoint: Build the Gemini Flash handler to return step-based errors.
[ ] Step Highlighting: CSS logic to highlight the erroneous step (by step number, not coordinates).
Phase 4: Polish (Sun Morning)
[ ] Weakness Dashboard: Show "Your Weak Areas" in the UI with confidence scores and improvement trends.
[ ] Prompt Tuning: Ensure the AI is "Socratic" (asks questions) rather than just solving.
[ ] [P2] Problem Generation: If time permits, implement /api/generate_problem endpoint.

6. Feature Priority
| Priority | Feature | Rationale |
|----------|---------|-----------|
| P0 | RAG chat with textbook | Core value prop |
| P0 | Canvas with "Check My Work" button | Safer than auto-debounce |
| P1 | Weakness tracking (with confidence) | Personalization demo |
| P1 | Step-based error feedback | More reliable than coordinates |
| P2 | Problem generation | Strong differentiator if time permits |
| P3 | Graphs/visualizations | Polish |

7. Critical Configurations
MongoDB Vector Search Index (JSON)
Paste into Atlas UI -> Search -> Create Index -> JSON Editor
JSON
{
  "fields": [
    {
      "numDimensions": 768,
      "path": "embedding",
      "similarity": "cosine",
      "type": "vector"
    },
    {
      "path": "metadata.chapter",
      "type": "filter"
    }
  ]
}
System Prompt (Vision)
Use this in analyze_visual endpoint
Plaintext
Analyze this handwritten math solution step by step.
1. Number each logical step you can identify (Step 1, Step 2, etc.).
2. Identify the FIRST step where a mathematical mistake occurs.
3. Describe WHERE in that step the error is (e.g., "when distributing", "in the exponent").
4. Provide a Socratic hint that guides without solving.
Output JSON ONLY: { "has_error": bool, "error_step": int|null, "error_description": "str", "hint": "str" }
System Prompt (Chat)
Use this in chat/stream endpoint
Plaintext
ROLE: Expert Tutor.
CONTEXT: {textbook_chunk}
USER HISTORY: User struggles with {weakness_list}.
INSTRUCTIONS:
- Guide the user step-by-step.
- If the problem involves their known weaknesses, warn them specifically (e.g. "Watch your signs!").
- Be concise and encouraging.

