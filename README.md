# charger: OpenClaw sandbox for the Cerebras × Kimi Speed Bounty

Everything OpenClaw touches lives in this container and `./state` (gitignored).

```sh
cp .env.example .env   # CEREBRAS_API_KEY, OPENCLAW_GATEWAY_TOKEN
./oc up                # start gateway (Control UI: http://127.0.0.1:18789/)
./oc agent --agent main --session-id run1 --json -m "..."   # one agent turn
./oc sessions tail --session-key agent:main:explicit:run1   # what it did
./oc shell | logs | down
./oc nuke              # remove container, image, and all state
```

Setup already applied to `./state`: onboarding with Cerebras, the `cerebras` and
`searxng` plugins, `tools.web.search.provider=searxng`,
`agents.defaults.timeoutSeconds=1800`, `tools.patch.json5` (only web_search + web_fetch), and
`kimi.patch.json5` (default model `cerebras/moonshotai-kimi-k3.1-pro-trial`).

## TPS logging proxy

OpenClaw's Cerebras `baseUrl` is set to `http://tpsproxy:8080/v1`. The proxy forwards
everything to `api.cerebras.ai` and appends one line per reply to `logs/tps.jsonl`, using
the bounty formula `(output tokens - 1) / (last token time - first token time)`.

## Search

`web_search` uses a self-hosted SearXNG container (no API key). Before the first
`./oc up`, copy `searxng/settings.example.yml` to `searxng/settings.yml` and set a random
`secret_key`.

## Speed-run instructions

`speedrun.md` is appended to the agent's `state/workspace/AGENTS.md`. It makes the agent
batch its tool calls into a few replies and copy product-page text verbatim in the final
answer (copied text decodes much faster than new prose).

## Runs

`./run.sh <session-id>` runs the Speedy Shopper prompt once and saves the reply to
`logs/runs/<session-id>.md`.

## Live dashboard

http://127.0.0.1:8081/ shows each reply's TPS, the best and average, a per-reply chart,
the streamed output, and a request table. It is served by the proxy over server-sent
events. **Clear** hides earlier requests for a clean recording.
