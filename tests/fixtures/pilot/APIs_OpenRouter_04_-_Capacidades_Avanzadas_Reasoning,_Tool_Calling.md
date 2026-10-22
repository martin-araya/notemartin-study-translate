# 04 - Capacidades Avanzadas: Reasoning, Tool Calling y Web Search

# 04 - Capacidades Avanzadas: Reasoning, Tool Calling y Web Search

> Responses API v1, Thinking/Reasoning en modelos avanzados, llamada a herramientas (Tool Calling / Function Calling) simples y paralelas, y búsquedas web en tiempo real.
> 

---

# Responses API

> OpenAI-compatible Responses API
> 

<Info>
**Stateless Only**

This API is **stateless** - each request is independent and no conversation state is persisted between requests. You must include the full conversation history in each request. Requests that set `store: true` or a non-null `previous_response_id` are rejected with a `400` error.
</Info>

OpenRouter's Responses API provides OpenAI-compatible access to multiple AI models through a unified interface, designed to be a drop-in replacement for OpenAI's Responses API. This stateless API offers enhanced capabilities including reasoning, tool calling, and web search integration, with each request being independent and no server-side state persisted.

## Base URL

```
<https://openrouter.ai/api/v1/responses>
```

## Authentication

All requests require authentication using your OpenRouter API key:

<CodeGroup>

```tsx
const response = await fetch('<https://openrouter.ai/api/v1/responses>', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_OPENROUTER_API_KEY',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: 'openai/o4-mini',
    input: 'Hello, world!',
  }),
});
```

```python
import requests

response = requests.post(
    '<https://openrouter.ai/api/v1/responses>',
    headers={
        'Authorization': 'Bearer YOUR_OPENROUTER_API_KEY',
        'Content-Type': 'application/json',
    },
    json={
        'model': 'openai/o4-mini',
        'input': 'Hello, world!',
    }
)
```

```bash
curl -X POST <https://openrouter.ai/api/v1/responses> \
  -H "Authorization: Bearer YOUR_OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/o4-mini",
    "input": "Hello, world!"
  }'
```

</CodeGroup>

## Core Features

### [Basic Usage](https://app.notion.com/p/basic-usage)

Learn the fundamentals of making requests with simple text input and handling responses.

### [Reasoning](https://app.notion.com/p/reasoning)

Access advanced reasoning capabilities with configurable effort levels and encrypted reasoning chains.

### [Tool Calling](https://app.notion.com/p/tool-calling)

Integrate function calling with support for parallel execution and complex tool interactions.

### [Web Search](https://app.notion.com/p/web-search)

Enable web search capabilities with real-time information retrieval and citation annotations.

## Error Handling

The API returns structured error responses:

```json
{
  "error": {
    "code": "invalid_prompt",
    "message": "Missing required parameter: 'model'."
  },
  "metadata": null
}
```

For comprehensive error handling guidance, see [Error Handling](https://app.notion.com/p/error-handling).

## Rate Limits

Standard OpenRouter rate limits apply. See [API Limits](https://app.notion.com/docs/api_reference/limits) for details.

---

# Basic Usage

> Getting started with the Responses API
> 

The Responses API supports both simple string input and structured message arrays, making it easy to get started with basic text generation.

## Simple String Input

The simplest way to use the API is with a string input:

<CodeGroup>

```tsx
const response = await fetch('<https://openrouter.ai/api/v1/responses>', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_OPENROUTER_API_KEY',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: 'openai/o4-mini',
    input: 'What is the meaning of life?',
    max_output_tokens: 9000,
  }),
});

const result = await response.json();
console.log(result);
```

```python
import requests

response = requests.post(
    '<https://openrouter.ai/api/v1/responses>',
    headers={
        'Authorization': 'Bearer YOUR_OPENROUTER_API_KEY',
        'Content-Type': 'application/json',
  