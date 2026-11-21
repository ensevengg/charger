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
`duckduckgo` plugins, `tools.web.search.provider=duckduckgo`,
`agents.defaults.timeoutSeconds=1800`, `tools.patch.json5` (only web_search + web_fetch), and
`kimi.patch.json5` (default model `cerebras/moonshotai-kimi-k3.1-pro-trial`).

## TPS logging proxy

OpenClaw's Cerebras `baseUrl` is set to `http://tpsproxy:8080/v1`. The proxy forwards
everything to `api.cerebras.ai` and appends one line per reply to `logs/tps.jsonl`, using
the bounty formula `(output tokens - 1) / (last token time - first token time)`.
