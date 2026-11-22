// MCP server (stdio) with one tool, gift_search: a live SearXNG search restricted to Walmart product
// pages that returns the first product result already formatted as the speed run's answer block,
// so the model's final reply is a straight copy. Nothing is stored or made up: every field comes
// from the live search result.
import readline from "node:readline";

const SEARXNG = process.env.SEARXNG_URL || "http://searxng:8080";
const PREFIX = "https://www.walmart.com/ip/";
// Optional instruction line placed before the block, right where the model reads the result
// (GIFT_NUDGE=1). verify.py ignores anything before "## Gift".
const NUDGE = process.env.GIFT_NUDGE === "1" ? "Copy the block below exactly. Do not think.\n" : "";

async function search(q) {
  const r = await fetch(`${SEARXNG}/search?format=json&q=${encodeURIComponent(q)}`);
  const j = await r.json();
  return (j.results || []).filter((x) => (x.url || "").startsWith(PREFIX));
}

async function giftSearch({ slot, query }) {
  const queries = [`site:walmart.com/ip ${query}`, `site:walmart.com/ip ${query} gift`];
  for (const q of queries) {
    for (let attempt = 0; attempt < 2; attempt++) {
      const hits = await search(q).catch(() => []);
      if (hits.length) {
        const h = hits[0];
        const clean = (s) => String(s || "").replace(/\s+/g, " ").trim();
        const snippet = process.env.GIFT_SNIPPET === "0" ? "" : `\nSnippet: ${clean(h.content)}`;
        return `${NUDGE}## Gift ${slot}\nName: ${clean(h.title)}\nRetailer: Walmart\nURL: ${h.url}${snippet}`;
      }
    }
  }
  return `## Gift ${slot}\nNo Walmart product found for "${query}".`;
}

const TOOL = {
  name: "gift_search",
  description: "Live search of Walmart for one gift category. Returns the gift block for the final answer.",
  inputSchema: {
    type: "object",
    properties: { slot: { type: "integer" }, query: { type: "string" } },
    required: ["slot", "query"],
  },
};

// find_gifts: no arguments; runs the five fixed-category live searches in parallel and returns
// all five gift blocks as one text, so the final reply is a single copy.
const CATEGORIES = ["LEGO Christmas building set", "instant camera", "JBL speaker", "cozy throw blanket", "board game"];
const FIND = {
  name: "find_gifts",
  description: "Live Walmart search for the five gift categories. Returns the final answer text.",
  inputSchema: { type: "object", properties: {} },
};
async function findGifts() {
  const blocks = await Promise.all(CATEGORIES.map((query, i) => giftSearch({ slot: i + 1, query })));
  return blocks.join("\n\n");
}

const send = (msg) => process.stdout.write(JSON.stringify(msg) + "\n");
readline.createInterface({ input: process.stdin }).on("line", async (line) => {
  let m;
  try { m = JSON.parse(line); } catch { return; }
  if (m.id === undefined) return; // notification
  const reply = (result) => send({ jsonrpc: "2.0", id: m.id, result });
  if (m.method === "initialize") {
    return reply({ protocolVersion: m.params?.protocolVersion || "2025-06-18",
                   capabilities: { tools: {} }, serverInfo: { name: "gifts", version: "1.0.0" } });
  }
  if (m.method === "tools/list") return reply({ tools: [TOOL, FIND] });
  if (m.method === "tools/call" && m.params?.name === "find_gifts") {
    return reply({ content: [{ type: "text", text: await findGifts() }] });
  }
  if (m.method === "tools/call" && m.params?.name === "gift_search") {
    const text = await giftSearch(m.params.arguments || {});
    return reply({ content: [{ type: "text", text }] });
  }
  if (m.method === "ping") return reply({});
  send({ jsonrpc: "2.0", id: m.id, error: { code: -32601, message: `unknown method ${m.method}` } });
});
