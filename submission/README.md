# Speed Bounty submission: 1,487 TPS mean

Run `u1122-223255` (Nov 22 2026, 22:32 IST), recorded in OpenClaw's web chat UI with the official speed patch.

- **Patch readout:** `1,487 tok/s mean · 1,522 p90 (server)`. Two model calls: 1,522 and 1,451 tok/s
  (completion_tokens / time_info.completion_time, Cerebras server timing).
- **Check:** PASS (`verify.txt`). Each of the 5 gifts is exactly a block the live search tool returned in this
  run, with unique Walmart product links.

## Files

| File | What |
|---|---|
| `demo.mp4` | 11.7 s video, queue waits cut: the answer streaming, the readout, the 5 gifts with links |
| `full.mp4` | the whole run uncut |
| `final.png` | last frame: readout next to the message box, gifts 2-5 with links |
| `answer.md` | the model's final answer |
| `verify.txt` | per-call rates and the gift-by-gift check |
| `readout.json` | the readout text captured from the UI |
| `system-compact-A.md` | the system prompt the model ran with (swapped in by our proxy) |
| `rewrite.json` | the proxy's request changes: tool_choice required on call 1, no tools on call 2, compact system prompt |
| `openclaw.json` | OpenClaw config used (secrets come from env vars, none stored) |
| `gift-search.mjs` | the MCP tool: five live SearXNG searches restricted to walmart.com/ip, formatted gift blocks |
| `window.txt` | run start/end (epoch seconds) |

The run folder's `AGENTS.md` (in `runs/u1122-223255/`) is the older 5-call instruction file; the model followed
`system-compact-A.md`, which replaced the system prompt.

## Setup

- OpenClaw 2026.10.9 (commit 8b18b55) + the official speed patch, in Docker; model `moonshotai-kimi-k3.1-pro-trial`
  on Cerebras, reasoning_effort low, temperature 0.6.
- Call 1: one `gifts__find_gifts` tool call. The tool runs five fixed-category live Walmart searches and returns
  the gift blocks. Call 2: the model copies them unchanged.
- `tpsproxy/proxy.py` sits between OpenClaw and Cerebras: it logs timings and applies `rewrite.json`. It never
  changes responses or the timing the patch reads.

## Products

1. LEGO Christmas Tree Toy Building Set 40573: https://www.walmart.com/ip/LEGO-Iconic-Christmas-Tree-40573/1970544820
2. Fujifilm instax Mini 99 Instant Camera: https://www.walmart.com/ip/Fujifilm-instax-Mini-99-Instant-Camera/5625569696
3. JBL Flip 5 Portable Waterproof Bluetooth Speaker: https://www.walmart.com/ip/JBL-Flip-5-Portable-Waterproof-Speaker-Black-Matte/870189368
4. Better Homes & Gardens Cozy Knit Throw Blanket: https://www.walmart.com/ip/Better-Homes-and-Gardens-Beige-Cozy-Knit-Throw-50-x-72/2602015509
5. Pop-O-Matic Trouble Board Game: https://www.walmart.com/ip/Pop-O-Matic-Trouble-Board-Game-for-Kids-and-Family-Ages-5-and-Up-2-4-Players/334768093
