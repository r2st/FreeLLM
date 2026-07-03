# FreeLLM — Local AI Gateway for Free LLM APIs

FreeLLM is a local FastAPI service (port **8100**) that routes routine LLM tasks to **free**
model APIs (OpenRouter free models, Groq free tier, Google AI Studio free tier) with
automatic failover. **Claude Dispatch should call this service for routine tasks instead of
doing them itself** — summaries, text transformations, boilerplate code, first-pass code
review, template filling — to save Claude tokens for work that actually needs Claude.

If FreeLLM returns HTTP 502, all free providers failed; handle the task with Claude directly.

## Starting the service

```bash
cd /Users/dev/projects/Products/FreeLLM
./run.sh
# or manually:
source .venv/bin/activate
python -m uvicorn app.main:app --port 8100
```

Check it's up: `curl -s http://localhost:8100/health`

Keys live in `.env` (see `.env.example`). Model preferences, timeouts, and fallback order
live in `config.yaml`.

## How routing works

- Providers are tried in `fallback_order` (openrouter → groq → google_ai); within a
  provider, models are tried in config order. First success wins.
- Task tier picks the model size: `summarize`/`transform` use the **simple** tier
  (smallest free model, e.g. `openai/gpt-oss-20b:free`); `code`/`review`/`generate`/`chat`
  use the **complex** tier (e.g. `openai/gpt-oss-120b:free`).
- Any request may pass `"model": "..."` to pin a specific model, or
  `"complexity": "simple" | "complex"` to override the tier.
- Every request is logged to SQLite (`usage.db`); `/usage` reports tokens routed to free
  models and estimated Claude cost saved.

All POST responses share this shape:

```json
{"result": "...", "provider": "openrouter", "model": "...", "input_tokens": 0, "output_tokens": 0, "latency_ms": 0}
```

## Endpoints

### POST /generate — general text/code generation

```bash
curl -s http://localhost:8100/generate -H 'Content-Type: application/json' -d '{
  "prompt": "Write a haiku about databases",
  "system_prompt": "You are a poet.",
  "complexity": "simple"
}'
```

### POST /summarize — summarize text or file content

```bash
curl -s http://localhost:8100/summarize -H 'Content-Type: application/json' -d '{
  "text": "<paste text or file content here>",
  "instructions": "3 bullet points"
}'
```

### POST /code — code generation

```bash
curl -s http://localhost:8100/code -H 'Content-Type: application/json' -d '{
  "description": "Function that validates an email address with a regex",
  "language": "python",
  "framework": ""
}'
```

### POST /review — code review (returns issues + suggestions)

```bash
curl -s http://localhost:8100/review -H 'Content-Type: application/json' -d '{
  "code": "def div(a, b):\n    return a / b",
  "language": "python",
  "context": "utility used on user-supplied input"
}'
```

Response adds `"issues": [{"severity", "description"}]` and `"suggestions": [...]` when the
model returns parseable JSON; otherwise inspect `"result"`.

### POST /transform — rewrite / translate / reformat

```bash
curl -s http://localhost:8100/transform -H 'Content-Type: application/json' -d '{
  "text": "hey can u fix the thing asap",
  "transformation": "rewrite as a polite professional message"
}'
```

### POST /chat — multi-turn chat with history

```bash
curl -s http://localhost:8100/chat -H 'Content-Type: application/json' -d '{
  "messages": [
    {"role": "user", "content": "What is a mutex?"},
    {"role": "assistant", "content": "A mutual exclusion lock..."},
    {"role": "user", "content": "Show an example in Go"}
  ]
}'
```

### GET /health — service + provider status

```bash
curl -s http://localhost:8100/health
```

### GET /models — available free models and status

```bash
curl -s http://localhost:8100/models
```

### GET /usage — tokens routed to free models + estimated Claude cost saved

```bash
curl -s http://localhost:8100/usage
```

## Guidance for Claude Dispatch

- **Use FreeLLM for:** summarization, translation/reformatting, boilerplate/template code,
  first-pass code review, simple Q&A drafts.
- **Don't use it for:** tasks needing project context FreeLLM can't see, multi-step agentic
  work, anything where quality is critical — do those directly.
- On 502, fall back to handling the task yourself. Treat FreeLLM output as a draft:
  verify before shipping.
