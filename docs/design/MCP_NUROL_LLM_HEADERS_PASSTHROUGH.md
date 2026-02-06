# Design: Pass Nurol API Call Properties Through SSE to LLM Calls

**Status:** Implemented  
**Related:** [APPLICATION_AUTHORIZATION_API_SPEC.md](../../APPLICATION_AUTHORIZATION_API_SPEC.md)

Headers are captured in middleware from POST /messages/, stored by session and last-POST; the tool reads them via `_get_llm_request_headers_for_tool(ctx)` and passes to the agent. OpenAIClient and ReportBuilder use Authorization as api_key when present; other headers as default_headers. The browser GUI has optional Authorization token and Application name fields.

---

## 1. Goal

When the MCP server is used over SSE/HTTP (e.g. browser or API clients), **forward selected request headers** from the incoming SSE/HTTP request to every **LLM (OpenAI-compatible) API call** made during that request. This allows an upstream LLM gateway or proxy to:

- Validate the caller via `Authorization: Bearer <token>`
- Apply application-scoped access and licensing via `X-Application-Name` / `X-Nurol-Application-Name`

The behavior aligns with the Nurol application authorization API: the same token and application name used to call the MCP server should be used when the MCP server calls the LLM.

---

## 2. Properties to Pass Through

From [APPLICATION_AUTHORIZATION_API_SPEC.md](../../APPLICATION_AUTHORIZATION_API_SPEC.md), the following request properties are relevant for downstream LLM calls. **All are optional.**

| HTTP header / property   | Purpose |
|--------------------------|--------|
| `Authorization`          | Bearer token for auth and licensing |
| `X-Application-Name`     | Application name (preferred) |
| `X-Nurol-Application-Name`| Application name (legacy) |

**Rules:**
- **Pass-through only if sent:** Forward a header to the LLM **only when the MCP client included it** in the request. Do not add or inject any of these headers when the client did not send them.
- Do not overwrite with server-side secrets; only pass through what the client sent.
- If the client sends none of these headers, the LLM is called with no extra headers (env-based config only).

---

## 3. Current Architecture (Relevant Paths)

```
Client (browser / API)
    │
    │  GET /sse  →  SSE stream (session created)
    │  POST /messages/?session_id=...  →  JSON-RPC (tools/call deep_research, etc.)
    │  Headers: Authorization, X-Application-Name, ...
    ▼
ASGI (Starlette)  →  CORS middleware  →  Mount("/", server.sse_app())
    │
    ▼
MCP SSE transport (session per SSE connection; POST /messages/ tied to session)
    │
    ▼
FastMCP tool: deep_research(question, report_type, ctx: Context)
    │
    ▼
deep_research_impl(question, report_type, progress_callback)
    │
    ├─ ReasoningAgent(question, report_type, progress_callback)
    │       │
    │       ├─ create_config()  →  AgentConfig (env-based; no request headers)
    │       └─ OpenAIClient(config)  →  OpenAI(api_key=..., base_url=...)  [no default_headers]
    │               │
    │               └─ client.chat.completions.create(...)  →  LLM (no extra headers)
    │
    └─ ReportBuilder()  →  get_report_config()  →  OpenAI(api_key=..., base_url=...)  [no default_headers]
            │
            └─ client.chat.completions.create(...)  →  LLM (no extra headers)
```

Today, **no part of the request (headers, query, or body)** is used when building `AgentConfig` or the OpenAI clients. All LLM calls use only env-based config (`OPENAI_API_KEY`, `OPENAI_BASE_URL`, etc.).

---

## 4. Design Overview

1. **Capture** the chosen headers from the HTTP request that triggers the tool (e.g. the POST to `/messages/` for the tool call).
2. **Propagate** them into the MCP tool (e.g. `deep_research`) and then into `deep_research_impl` so they are available when building the agent and report builder.
3. **Apply** them to every LLM client used for that request: add the headers as `default_headers` (or equivalent) when constructing `OpenAI` / `AsyncOpenAI` in `OpenAIClient` and in `ReportBuilder`.

---

## 5. Where to Capture Headers

Two main options:

### Option A: From MCP/SSE request context (preferred if available)

If the MCP SDK (FastMCP/SSE) exposes the current HTTP request or its headers on the tool `Context` (e.g. `ctx.request` or `ctx.request_headers`), the tool handler should read them there. This keeps capture inside the MCP layer and avoids depending on transport-specific middleware.

- **Pro:** One place to read headers; works for any transport that provides them on Context.
- **Con:** Requires the SDK to expose request/headers; behavior may differ for stdio vs SSE.

**Action:** Confirm in FastMCP/MCP Python SDK whether `Context` (or equivalent) provides access to the current HTTP request or a headers dict for SSE. If yes, use that in `deep_research(..., ctx)` and pass the result into `deep_research_impl`.

### Option B: ASGI middleware and context variable

If the SDK does not expose headers on Context, add ASGI middleware that runs before the MCP app and, for each request, extracts the chosen headers and stores them in an `contextvars.ContextVar` (e.g. `mcp_request_headers`). The MCP server code (e.g. inside the tool or inside the SSE handler that dispatches to the tool) must run in the same async context so it can read this variable before calling `deep_research_impl`.

- **Pro:** Works with any backend; full control over which headers are captured.
- **Con:** Tied to HTTP; must ensure the context var is set for the request that actually invokes the tool (POST /messages/), and that no other concurrent request overwrites it (per-request isolation).

**Recommendation:** Prefer Option A; fall back to Option B if the SDK does not expose request headers.

---

## 6. Propagation Path

- **From tool to impl:** Extend the tool signature or the call to `deep_research_impl` with an optional parameter, e.g. `llm_request_headers: Optional[Dict[str, str]] = None`. The tool handler (which has access to `ctx` or the context var) builds this dict and passes it in.
- **From impl to agent and report:** `deep_research_impl` receives `llm_request_headers` and passes it when creating the agent and when the agent creates the report. So:
  - **ReasoningAgent:** Must accept an optional `llm_request_headers` (or an optional `override_config` that can carry it). The agent uses it when building or using the OpenAI client.
  - **ReportBuilder:** Must be able to receive the same headers (e.g. via constructor or a method that uses them when creating the OpenAI client). Today `ReportBuilder` is created inside the agent/report flow; that creation point must have access to `llm_request_headers`.

Concrete flow:

1. `deep_research(question, report_type, ctx)`  
   - Reads headers from `ctx` (Option A) or from context var (Option B).  
   - Builds `llm_request_headers` containing **only** the headers that the client actually sent (e.g. if the client sent only `Authorization`, the dict has only that key). If the client sent none of the optional auth headers, `llm_request_headers` is empty or `None`.  
   - Calls `deep_research_impl(question, report_type, progress_callback, llm_request_headers=llm_request_headers)`.

2. `deep_research_impl(..., llm_request_headers=None)`  
   - Creates `ReasoningAgent(..., llm_request_headers=llm_request_headers)`.  
   - When the agent later creates `ReportBuilder`, it must pass the same `llm_request_headers` (e.g. agent holds the dict and passes it to the report builder).

3. **ReasoningAgent**  
   - If `llm_request_headers` is provided, merge it into the config used for the LLM (e.g. add to `AgentConfig` or pass as override).  
   - When creating `OpenAIClient(config)`, ensure the client is built with these headers (see below).  
   - When creating or calling `ReportBuilder`, pass `llm_request_headers` so the report builder’s LLM client also uses them.

4. **OpenAIClient** and **ReportBuilder**  
   - When constructing `OpenAI(...)` and `AsyncOpenAI(...)`, pass `default_headers=llm_request_headers` only when `llm_request_headers` is non-empty (the client sent at least one of the optional headers). If empty or `None`, do not set `default_headers`.  
   - This way every `chat.completions.create` from that client instance sends the Nurol headers to the LLM only when the client provided them.

---

## 7. Config and Client Changes

- **LLMConfig (reasoning/config.py):** Add an optional field, e.g. `extra_headers: Optional[Dict[str, str]] = None`. When building the OpenAI client, if `extra_headers` is set and non-empty, pass it as `default_headers`; otherwise do not pass default_headers. Do not persist `extra_headers` to env or to any long-lived global; it is per-request.
- **OpenAIClient (reasoning/clients/openai_client.py):** In `__init__`, read `config.llm.extra_headers`; pass it to both `OpenAI(..., default_headers=...)` and `AsyncOpenAI(..., default_headers=...)` only when it is non-empty.
- **ReportBuilder (reasoning/builders/report.py):** Today it uses `get_report_config()` and builds its own OpenAI clients. Either:
  - **Option R1:** Add an optional `extra_headers` (or `request_headers`) argument to `ReportBuilder.__init__`. When building `OpenAI` / `AsyncOpenAI`, pass `default_headers=extra_headers` only when `extra_headers` is non-empty. The agent creates `ReportBuilder(stream_event=..., extra_headers=self._llm_request_headers)`.
  - **Option R2:** Have ReportBuilder accept an optional pre-built config object that already carries `extra_headers`, and use that when constructing the clients.

Option R1 is simpler and keeps ReportBuilder’s constructor small.

- **ReasoningAgent (reasoning/agent.py):** Accept optional `llm_request_headers: Optional[Dict[str, str]] = None`. In `__init__`, if provided, set `self._llm_request_headers = llm_request_headers` and merge into config (e.g. `self.config.llm.extra_headers = llm_request_headers`) before creating `OpenAIClient`. When creating `ReportBuilder`, pass `extra_headers=self._llm_request_headers`.

---

## 8. Other MCP Tools

- **deep_research:** Full pass-through as above (multiple LLM calls: reasoning + report).
- **web_batch_search, web_scrape, web_visit_compress, configure_research, get_server_status:** No direct LLM calls in the current design. No change unless we later add LLM-backed behavior to these tools; then the same pattern (capture headers from context, pass into impl, then into client/config) applies.

---

## 9. Security and CORS

- **Do not log or echo** `Authorization` (or any secret) in logs or error messages.
- **Forward only the headers listed above;** do not blindly forward all request headers to the LLM.
- CORS: If the browser sends `Authorization` or custom headers, the server must respond with `Access-Control-Allow-Headers` that includes them (e.g. `Authorization`, `X-Application-Name`, `X-Nurol-Application-Name`). The current CORS setup uses `allow_headers=["*"]`; confirm that the actual requests from the client include these headers when using the GUI or other browser-based clients.

---

## 10. Stdio Transport

For `--transport stdio` (e.g. Claude Desktop), there is no HTTP request. Options:

- Do not pass any Nurol headers (leave `llm_request_headers` empty/None). LLM calls use only env-based config.
- Or, allow a future extension where the client can send these properties in the JSON-RPC request (e.g. in a custom field or in `params`). This is out of scope for this design unless required.

---

## 11. Implementation Outline

1. **Verify MCP Context (Option A):** In the MCP Python SDK/FastMCP, check whether the tool `Context` exposes the current HTTP request or headers for SSE. Document the exact attribute (e.g. `ctx.request_headers`).
2. **Capture layer:** Implement header extraction (from Context or from context var in middleware). For each of the optional headers (`Authorization`, `X-Application-Name`, `X-Nurol-Application-Name`), include it in `llm_request_headers` only if the client sent it. Normalize header names to the exact strings expected by the Nurol/LLM API. If the client sent none of these, pass an empty dict or `None` into `deep_research_impl`.
3. **Config/LLMConfig:** Add `extra_headers: Optional[Dict[str, str]] = None` to `LLMConfig`. No env or file persistence.
4. **OpenAIClient:** Pass `config.llm.extra_headers` as `default_headers` into `OpenAI` and `AsyncOpenAI`.
5. **ReportBuilder:** Add optional `extra_headers` to `__init__`; pass to `OpenAI` and `AsyncOpenAI` as `default_headers`.
6. **ReasoningAgent:** Add optional `llm_request_headers`; set `config.llm.extra_headers` and pass the same to `ReportBuilder` when created.
7. **deep_research_impl:** Add parameter `llm_request_headers=None`; pass it into `ReasoningAgent(..., llm_request_headers=llm_request_headers)`.
8. **deep_research tool:** In the tool handler, obtain headers from Context (or context var), build `llm_request_headers`, call `deep_research_impl(..., llm_request_headers=llm_request_headers)`.
9. **Tests:** Unit tests for header extraction (no Authorization value in logs), and integration-style test that a mock LLM receives the forwarded headers when the client sends them.
10. **Docs:** Update [docs/guides/MCP.md](../guides/MCP.md) (or equivalent) to state that when using SSE, the client may send `Authorization`, `X-Application-Name`, and `X-Nurol-Application-Name`; these are forwarded to the LLM backend.

---

## 12. Summary

| Item | Decision |
|------|----------|
| What to pass | `Authorization`, `X-Application-Name`, `X-Nurol-Application-Name` (all optional) |
| When to pass | Only headers that the MCP client actually sent; do not add any if the client sent none |
| Where to capture | MCP Context (preferred) or ASGI context var |
| Where to apply | Every OpenAI/AsyncOpenAI used for that request (OpenAIClient + ReportBuilder), only when non-empty |
| Config change | LLMConfig.extra_headers (optional, per-request) |
| Stdio | No headers passed unless we add a separate mechanism later |

This design keeps the pass-through explicit, forwards only what the client sent, and avoids persisting or logging secrets.
