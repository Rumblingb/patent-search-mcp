     1|# USPTO Patent Search MCP
     2|
     3|**$19/month** — Search US patents via MCP protocol.
     4|▶ [Subscribe Now](https://buy.stripe.com/7sYeVf6Pl2Ju1jqdjl1oI0n) Server
     5|
     6|An MCP (Model Context Protocol) server for searching and retrieving USPTO patent data. Uses the **Google Patents API** (no authentication required) as the primary backend, with the **USPTO official API** as a documented fallback.
     7|
     8|## Features
     9|
    10|| Tool | Description |
    11||---|---|
    12|| `search_patents` | Search patents by keyword query |
    13|| `get_patent_details` | Get detailed info for a specific patent by ID |
    14|| `search_by_assignee` | Find patents assigned to a company/organization |
    15|| `search_by_classification` | Search patents by CPC classification code |
    16|
    17|## Installation
    18|
    19|```bash
    20|pip install -r requirements.txt
    21|```
    22|
    23|## Usage
    24|
    25|### Run as MCP server (stdio)
    26|
    27|```bash
    28|python server.py
    29|```
    30|
    31|### Test from Python
    32|
    33|```python
    34|import httpx
    35|import json
    36|
    37|# Search patents
    38|resp = httpx.get("https://patents.google.com/api/patents", params={
    39|    "q": "machine learning",
    40|    "num": 5,
    41|    "format": "json"
    42|})
    43|data = resp.json()
    44|print(json.dumps(data, indent=2))
    45|```
    46|
    47|## Tools
    48|
    49|### search_patents(query, limit=10)
    50|
    51|Search patents by keyword query. Returns patent ID, title, abstract, assignee, inventors, filing/publication dates, and CPC classifications.
    52|
    53|**Arguments:**
    54|- `query` (string, required) — Patent search query (e.g. `"machine learning"`, `"USPTO"`)
    55|- `limit` (integer, optional, default: 10, max: 50) — Number of results to return
    56|
    57|### get_patent_details(patent_id)
    58|
    59|Get detailed information for a specific patent by ID. Includes full abstract, claims, assignee, inventors, classifications, priority date, and description.
    60|
    61|**Arguments:**
    62|- `patent_id` (string, required) — Patent ID (e.g. `"US10529241B2"`, `"US20200012345A1"`)
    63|
    64|### search_by_assignee(assignee, limit=10)
    65|
    66|Search patents by assignee (company or organization name).
    67|
    68|**Arguments:**
    69|- `assignee` (string, required) — Company name (e.g. `"Apple"`, `"Microsoft"`, `"IBM"`)
    70|- `limit` (integer, optional, default: 10, max: 50) — Number of results to return
    71|
    72|### search_by_classification(class_code, limit=10)
    73|
    74|Search patents by CPC classification code.
    75|
    76|**Arguments:**
    77|- `class_code` (string, required) — CPC code (e.g. `"G06N"` for AI, `"G06F"` for computing, `"H04L"` for networking)
    78|- `limit` (integer, optional, default: 10, max: 50) — Number of results to return
    79|
    80|## API Details
    81|
    82|### Primary: Google Patents API (no auth)
    83|
    84|- **Endpoint:** `GET https://patents.google.com/api/patents?q={query}&num={limit}&format=json`
    85|- **Pros:** No registration required, returns structured JSON
    86|- **Cons:** Unofficial API — may change without notice
    87|
    88|### Fallback: USPTO Official API (requires API key)
    89|
    90|- **Endpoint:** `https://developer.uspto.gov/ds-api/`
    91|- **Registration:** https://developer.uspto.gov/
    92|- **Requires API key** for authenticated access
    93|
    94|## Configuration
    95|
    96|Add to your MCP client configuration:
    97|
    98|### Claude Desktop
    99|
   100|```json
   101|{
   102|  "mcpServers": {
   103|    "patent-search": {
   104|      "command": "python",
   105|      "args": ["/path/to/patent-search-mcp/server.py"]
   106|    }
   107|  }
   108|}
   109|```
   110|
   111|## Project Structure
   112|
   113|```
   114|patent-search-mcp/
   115|├── server.py          # MCP server implementation
   116|├── requirements.txt   # Python dependencies
   117|├── smithery.yaml      # Smithery deployment configuration
   118|└── README.md          # This file
   119|```
   120|
   121|## Dependencies
   122|
   123|- `mcp` — Model Context Protocol Python SDK
   124|- `httpx` — Modern HTTP client for Python
   125|
   126|## License
   127|
   128|MIT
   129|