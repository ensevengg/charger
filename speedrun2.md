
## Santa's Speedy Shopper: mechanical speed run (2 replies)

Find five Walmart Christmas gifts. Execute literally. No planning, ranking, gift rationale,
or deliberation. Tool-call replies contain only tool calls.

1. Reply 1: make these five `web_search` calls in parallel, exactly (one slot each):
   - Slot 1: `site:walmart.com/ip LEGO Christmas building set` (backup: `site:walmart.com/ip LEGO holiday`)
   - Slot 2: `site:walmart.com/ip instant camera` (backup: `site:walmart.com/ip Kodak instant camera`)
   - Slot 3: `site:walmart.com/ip JBL speaker` (backup: `site:walmart.com/ip Sony speaker`)
   - Slot 4: `site:walmart.com/ip cozy throw blanket` (backup: `site:walmart.com/ip Better Homes and Gardens throw`)
   - Slot 5: `site:walmart.com/ip board game` (backup: `site:walmart.com/ip jigsaw puzzle`)
2. Only if a slot's results contain no URL starting with `https://www.walmart.com/ip/`, search that
   slot's backup query (all such slots in one parallel reply, no thinking). Otherwise skip this step.
3. Final reply: do not think; output immediately, starting with `## Gift 1`, slots in order,
   no preamble or closing note. For each slot, from that slot's first result whose URL starts with
   `https://www.walmart.com/ip/`, exactly:

   ## Gift N
   Name: <that result's title text, copied exactly>
   Retailer: Walmart
   URL: <that result's url, copied exactly>

   The title text is the line between `---` and `<<<END_EXTERNAL_UNTRUSTED_CONTENT`. Nothing after Gift 5.

Evidence rules (never break these):
- Every name and URL comes character-for-character from that slot's own search result.
- Never build, guess, repair, or shorten a URL or product ID. Never fill a slot from memory.
- If a slot has no Walmart product result even after its backup, output only the other slots and say how many failed.
