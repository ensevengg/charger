# Santa's Speedy Shopper: 1,730 TPS

Speed Bounty entry for the Cerebras x Kimi hackathon.

**1,730 tok/s mean · 1,947 p90**, measured by the official OpenClaw speed patch.

- Model: Kimi K3.1 Pro on Cerebras
- Two model calls: 1,947 and 1,514 tok/s
- Best of 1,035 recorded runs (run `u1123-022456`)
- Every gift comes from a live Walmart search, checked after the run
- Video, screenshot and logs: [`submission/`](submission/)

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

## Run it

```sh
cp .env.example .env    # add CEREBRAS_API_KEY and OPENCLAW_GATEWAY_TOKEN
cp searxng/settings.example.yml searxng/settings.yml   # set a random secret_key
./oc up                 # OpenClaw, proxy and SearXNG in Docker
./run-ui.sh myrun       # one recorded run, saved to runs/myrun/
./loop.sh 20            # many runs
```

## What's where

| Path | What it is |
|---|---|
| `submission/` | the entry: videos, screenshot, answer, check, prompt, config |
| `mcp/gift-search.mjs` | the search tool |
| `tpsproxy/` | proxy, timing log and dashboard |
| `recorder/` | drives the web UI, records and cuts video |
| `verify.py` | checks each answer against the live search results |
| `runs/` | every recorded run, ranked in `runs/leaderboard.md` |
| `speedrun*.md` | earlier prompt versions we tested |

Stack: OpenClaw 2026.10.9 with the speed patch, in Docker. Reasoning effort low, temperature 0.6.
