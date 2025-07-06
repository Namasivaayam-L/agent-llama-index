# 🧠 HITL-Enhanced LLM Agent with Redis Memory (FastAPI + LlamaIndex)

An enterprise-ready, multi-tool LLM agent framework built using **FastAPI**, **llama-index**, and **Redis**. It supports **human-in-the-loop (HITL)** workflows, **function calling**, and **session persistence**.

---

## 🚀 Features

- ✅ LLM Function Calling via `llama-index` with `FunctionToolWithContext`
- ✅ Human Approval for Risky Tools (HITL)
- ✅ Redis-Powered Chat Memory per `user_id + session_id`
- ✅ WebSocket-based Realtime Interaction
- ✅ Phoenix/OTEL observability tracing
- ✅ Modular Tool Registration

---

## 🧰 Tech Stack

| Component        | Tech                       |
|------------------|----------------------------|
| Backend          | FastAPI                    |
| LLM Integration  | LlamaIndex + OpenInstruct  |
| Chat Store       | Redis (via `RedisChatStore`) |
| LLMs Used        | LLaMA 3.1 8B (function-calling) |
| Observability    | Phoenix + OTEL             |

---

## 🛠️ Setup Instructions

```bash
git clone https://github.com/Namasivaayam-L/agent-llama-index.git
cd agent-llama-index
poetry install
```

### 🔧 Redis
Ensure Redis is running locally:

```bash
sudo service redis-server start
```

---

## 🧑‍💻 Run the Server

```bash
python app.py
```

Server will be running at: `http://localhost:5000`

---

## 🔌 WebSocket Usage

### Endpoint

```text
ws://localhost:5000/chat
```

### Sample JSON Input

```json
{
  "user_id": "user_001",
  "session_id": "session_abc",
  "input": {
    "query": "How do I reset my password?"
  }
}
```

If a tool requires human approval, send:

```json
{
  "user_id": "user_001",
  "session_id": "session_abc",
  "input": {
    "query": "y"
  }
}
```

---

## 🧠 Current Tooling Setup

### 🟢 No Approval Needed

| Tool                     | Purpose                                 |
|--------------------------|-----------------------------------------|
| `fetch_customer_chat_history` | Pull session history from Redis     |
| `faq_lookup_tool`        | Answer FAQs based on rules or lookup    |
| `ticket_status_checker`  | Check support ticket status             |
| `suggest_next_step`      | Recommend action based on issue intent  |

### 🔒 Requires Approval (HITL)

| Tool                           | Purpose                            |
|--------------------------------|------------------------------------|
| `get_product_doc_snippet`      | Provide help based on error codes  |
| `raise_ticket_on_behalf`       | Draft a support ticket             |
| `compose_response_for_complex_issue` | Draft a human-like support reply |

---

## 🔁 Session & History APIs

### Get User Sessions
```http
GET /sessions/user/{user_id}
```

### Get Session Messages
```http
GET /sessions/{user_id}/{session_id}
```

---

## 🔍 System Prompt (LLM Instruction)

> You are an enterprise-grade support agent assistant. You are helpful, calm, and precise. Your primary job is to understand the customer's issue, retrieve relevant data, suggest tools, and decide whether a human agent must be involved.  
>  
> You have access to tools. Use them when necessary. Some tools require human approval—ask before using them. Store conversations in Redis. Avoid hallucinations. Be neutral, focused, and context-aware.

---

## 📈 Observability

- 🔗 Exposed via [Phoenix](https://arize.com/phoenix/)
- Traces streamed to: `http://localhost:6006/v1/traces`

---

## 📂 Project Structure

```
.
├── main.py                        # FastAPI + WebSocket entrypoint
├── src/
│   ├── workflows/
│   │   ├── func_agent.py         # FuncAgentWorkflow class
│   │   └── tools.py              # Tool definitions and registration
│   ├── utils/
│   │   ├── func_tool_with_ctx.py # FunctionToolWithContext
│   │   ├── llms.py               # LLM model mapping
│   │   └── pydantic_models.py    # Request schemas
├── config/
│   └── logging.py                # Logging setup
```

---

## 🧪 Testing with Python Client

```python
import asyncio, json, websockets

async def test():
    uri = "ws://localhost:5000/chat"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "user_id": "user_001",
            "session_id": "session_abc",
            "input": { "query": "Check status of ticket ID: 54892" }
        }))
        while True:
            response = await ws.recv()
            print("→", response)
asyncio.run(test())
```

---

Built by **Mr. Namasivaayam L.**

---