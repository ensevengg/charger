
## Santa's Speedy Shopper: mechanical speed run

Find five Walmart Christmas gifts. Execute literally. No planning, ranking, gift rationale,
word counting, or copyright deliberation: quoting product pages is approved. Tool-call
replies contain only tool calls.

1. Reply 1: make these five `web_search` calls in parallel, exactly (one slot each):
   - Slot 1: `site:walmart.com/ip LEGO Christmas building set` (backup: `site:walmart.com/ip LEGO holiday`)
   - Slot 2: `site:walmart.com/ip instant camera` (backup: `site:walmart.com/ip digital camera`)
   - Slot 3: `site:walmart.com/ip Bluetooth speaker` (backup: `site:walmart.com/ip wireless earbuds`)
   - Slot 4: `site:walmart.com/ip cozy throw blanket` (backup: `site:walmart.com/ip fleece blanket`)
   - Slot 5: `site:walmart.com/ip board game` (backup: `site:walmart.com/ip jigsaw puzzle`)
2. Reply 2: for each slot, take the first result whose URL starts with `https://www.walmart.com/ip/`.
   Call `web_fetch` on all five in parallel (maxChars 12000). A fetch is usable if it shows a
   product title and the text `Current price is`.
3. If any slot is unusable or duplicates another, take that slot's next `walmart.com/ip/` result
   and fetch all replacements in one parallel reply. If a slot has no usable results left, search
   that slot's backup query (all such slots in one parallel reply). At most two replacement rounds.
4. Final reply: do not think; output immediately, starting with `## Gift 1`, slots in order,
   no preamble or closing note.
   For each slot, exactly:

   ## Gift N
   Name: <product title copied exactly from this slot's fetch>
   Retailer: Walmart
   Price: <the text right after `Current price is`, copied exactly>
   URL: <the exact URL you passed to this slot's successful web_fetch>
   Product page excerpt
   > <verbatim text from that fetch>

   In the excerpt, copy the title, every description, feature and specification line, and the
   price lines, in page order, each line prefixed with `> `. Copy everything available; do not
   summarize, shorten, pad, or insert ellipses.
5. End with a table `| Name | Retailer | Price | URL |` repeating each slot's fields exactly. Nothing after it.

Evidence rules (never break these):
- Every name, price and URL comes character-for-character from that slot's own successful fetch.
- Only fetch URLs that appeared in a tool result. Never build, guess, repair, or shorten a URL or product ID.
- Never fetch google, bing, duckduckgo or other search-engine pages.
- `Sold out` or `Out of stock` on a page makes that slot unusable.
- If five usable slots are impossible after two replacement rounds, output only the usable slots and say how many failed. Never fill a slot from memory or a search snippet.
