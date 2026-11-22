## Santa's Speedy Shopper: mechanical speed run

Execute literally. No planning or deliberation. Two replies only.

1. Reply 1: call `gifts__gift_search` 5 times in parallel, exactly:
   - `{"slot":1,"query":"LEGO Christmas building set"}`
   - `{"slot":2,"query":"instant camera"}`
   - `{"slot":3,"query":"JBL speaker"}`
   - `{"slot":4,"query":"cozy throw blanket"}`
   - `{"slot":5,"query":"board game"}`
   Each call does a live Walmart search and returns that slot's gift block.
2. Reply 2: do not think. Output the five returned gift blocks in slot order, each copied
   character-for-character, separated by a blank line. Nothing else: no preamble, no wrapper
   lines, no closing note. Never change or add to a block.
