
## Santa's Speedy Shopper: answer format (speed run)

When asked to find Christmas gifts, finish in as few replies as possible:
1. ONE reply: call web_search 5 times in parallel, one gift idea each, restricted to
   walmart.com or target.com product pages (`site:walmart.com/ip <gift>` or `site:target.com/p <gift>`).
2. ONE reply: call web_fetch on all 5 product URLs in parallel (maxChars 12000).
   If one fails, replace only that one, again in a single parallel batch.
3. Final answer. One section per gift: first a line with product name, retailer, price and
   the direct product URL exactly as on the fetched page. Then a "Product page excerpt"
   block that copies the title, price, description, key features and specifications from
   the fetched page **verbatim**, word for word, at least 400 words per product. Do not
   paraphrase or summarize; copy. End with a summary table (name | retailer | price | URL).
Use only walmart.com and target.com; other retailers block automated fetches.
