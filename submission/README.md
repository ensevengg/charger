# Speed Bounty entry: 1,487 TPS

**1,487 tok/s mean · 1,522 p90**, measured by the official OpenClaw speed patch.

- Run: `u1122-223255`, Nov 22, 22:32 IST
- Model: Kimi K3.1 Pro on Cerebras
- Two model calls: 1,522 and 1,451 tok/s
- Check: PASS. Every gift comes from a live Walmart search in this run.

## The 5 gifts

1. [LEGO Christmas Tree 40573](https://www.walmart.com/ip/LEGO-Iconic-Christmas-Tree-40573/1970544820)
2. [Fujifilm instax Mini 99](https://www.walmart.com/ip/Fujifilm-instax-Mini-99-Instant-Camera/5625569696)
3. [JBL Flip 5 speaker](https://www.walmart.com/ip/JBL-Flip-5-Portable-Waterproof-Speaker-Black-Matte/870189368)
4. [Better Homes & Gardens knit throw](https://www.walmart.com/ip/Better-Homes-and-Gardens-Beige-Cozy-Knit-Throw-50-x-72/2602015509)
5. [Trouble board game](https://www.walmart.com/ip/Pop-O-Matic-Trouble-Board-Game-for-Kids-and-Family-Ages-5-and-Up-2-4-Players/334768093)

## How it works

1. **Call 1:** the model makes one tool call, `find_gifts`.
2. **The tool** runs 5 live Walmart searches and formats the results.
3. **Call 2:** the model copies the results unchanged.

Copying is the fastest thing the model can write, so both calls stay fast.

A small proxy forces call 1 to be a tool call, drops tools from call 2, and uses a short system prompt. It never touches the timing the patch reads.

## Files

| File | What it is |
|---|---|
| `demo.mp4` | 12 s video to post |
| `full.mp4` | full run, uncut |
| `final.png` | last frame: score and gifts |
| `answer.md` | the model's answer |
| `verify.txt` | speed per call and the gift check |
| `system-compact-A.md` | prompt the model used |
| `rewrite.json` | the proxy's request changes |
| `openclaw.json` | OpenClaw config (no secrets) |
| `gift-search.mjs` | the search tool |

Stack: OpenClaw 2026.10.9 with the speed patch, in Docker. Reasoning effort low, temperature 0.6.
