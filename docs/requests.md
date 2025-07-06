# 📩 Sample Request Bodies for WebSocket Agent Testing

These are JSON payloads to test various tools via WebSocket at:

```
ws://localhost:8000/chat
```

---

## 🟢 Tools That Do NOT Require Approval

### 1. `fetch_customer_chat_history`

```json
{
  "user_id": "user_001",
  "session_id": "session_abc",
  "input": {
    "query": "Fetch my recent chat history for session_id: session_abc"
  }
}
```

---

### 2. `faq_lookup_tool`

```json
{
  "user_id": "user_001",
  "session_id": "session_abc",
  "input": {
    "query": "How do I reset my password?"
  }
}
```

---

### 3. `ticket_status_checker`

```json
{
  "user_id": "user_001",
  "session_id": "session_abc",
  "input": {
    "query": "Check status of ticket ID: 54892"
  }
}
```

---

### 4. `suggest_next_step`

```json
{
  "user_id": "user_001",
  "session_id": "session_abc",
  "input": {
    "query": "I'm having issues logging in to my account"
  }
}
```

---

## 🔒 Tools That Require HITL Approval

### 5. `get_product_doc_snippet`

```json
{
  "user_id": "user_001",
  "session_id": "session_abc",
  "input": {
    "query": "Explain error code ERR_500"
  }
}
```

#### 🔁 Response for Approval Prompt

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

### 6. `raise_ticket_on_behalf`

```json
{
  "user_id": "user_001",
  "session_id": "session_abc",
  "input": {
    "query": "Raise a ticket for user john@example.com about email sync failure"
  }
}
```

---

### 7. `compose_response_for_complex_issue`

```json
{
  "user_id": "user_001",
  "session_id": "session_abc",
  "input": {
    "query": "Compose a detailed reply about delayed account verification"
  }
}
```

---

## 🛑 Exit Session

```json
{
  "user_id": "user_001",
  "session_id": "session_abc",
  "input": {
    "query": "bye"
  }
}
```

---