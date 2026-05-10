#!/usr/bin/env python3
"""
USPTO Patent Search MCP Server

Provides tools for searching and retrieving patent data from Google Patents API.
Includes search_patents, get_patent_details, search_by_assignee, and
search_by_classification tools.
"""

import json
import re
import sys
from typing import Any

import httpx
from mcp.server import Server, stdio_server
from mcp.types import Tool, TextContent

# ── Constants ─────────────────────────────────────────────────────────────

GOOGLE_PATENTS_API = "https://patents.google.com/api/patents"
USPTO_API_BASE = "https://developer.uspto.gov/ds-api/"

# ── HTTP Client ───────────────────────────────────────────────────────────

_client = httpx.Client(
    timeout=30.0,
    headers={
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
    },
)


def _search_google_patents(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search Google Patents API and return parsed results."""
    params: dict[str, Any] = {"q": query, "num": min(limit, 50), "format": "json"}
    resp = _client.get(GOOGLE_PATENTS_API, params=params)
    resp.raise_for_status()
    data = resp.json()

    results: list[dict[str, Any]] = []
    raw_results = _safe_get(data, ["results"], [])
    if not raw_results:
        raw_results = _safe_get(data, ["patents"], [])
    if not raw_results:
        raw_results = _safe_get(data, ["items"], [])

    for entry in raw_results[:limit]:
        patent = _parse_patent_entry(entry)
        if patent.get("patent_id"):
            results.append(patent)

    return results


def _get_patent_details_google(patent_id: str) -> dict[str, Any]:
    """Fetch detailed information for a specific patent."""
    params = {"q": patent_id, "num": 1, "format": "json"}
    resp = _client.get(GOOGLE_PATENTS_API, params=params)
    resp.raise_for_status()
    data = resp.json()

    raw_results = _safe_get(data, ["results"], [])
    if not raw_results:
        raw_results = _safe_get(data, ["patents"], [])
    if not raw_results:
        raw_results = _safe_get(data, ["items"], [])

    if not raw_results:
        return {"patent_id": patent_id, "error": "Patent not found"}

    entry = raw_results[0]
    details = _parse_patent_entry(entry)
    details["claims"] = _safe_get(entry, ["claims"], "")
    details["description"] = _safe_get(entry, ["description"], "")
    details["priority_date"] = _safe_get(entry, ["priority_date"], "")
    details["ipc_classifications"] = _safe_get(entry, ["ipc"], "")
    details["status"] = _safe_get(entry, ["status"], "")

    if isinstance(details.get("claims"), list):
        details["claims"] = "\n".join(details["claims"])
    if isinstance(details.get("description"), list):
        details["description"] = "\n".join(details["description"])

    return details


def _parse_patent_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Parse a raw patent entry from Google Patents API into a clean dict."""
    patent_id = _safe_get(entry, ["patent_id"], "")
    if not patent_id:
        patent_id = _safe_get(entry, ["id"], "")
    if not patent_id:
        patent_id = _safe_get(entry, ["publication_number"], "")

    title = _safe_get(entry, ["title"], "")
    abstract = _safe_get(entry, ["abstract"], "")

    assignee = _safe_get(entry, ["assignee"], "")
    if not assignee:
        assignee = _safe_get(entry, ["assignee_original"], "")
    if isinstance(assignee, list):
        assignee = "; ".join(assignee)

    inventors = _safe_get(entry, ["inventor"], "")
    if not inventors:
        inventors = _safe_get(entry, ["inventor_name"], "")
    if isinstance(inventors, list):
        inventors = "; ".join(inventors)

    filing_date = _safe_get(entry, ["filing_date"], "")
    publication_date = _safe_get(entry, ["publication_date"], "")
    cpc = _safe_get(entry, ["cpc_classification"], "")
    if isinstance(cpc, list):
        cpc = "; ".join(cpc)

    url = f"https://patents.google.com/patent/{patent_id}/en"

    return {
        "patent_id": patent_id,
        "title": title,
        "abstract": abstract,
        "assignee": assignee,
        "inventors": inventors,
        "filing_date": filing_date,
        "publication_date": publication_date,
        "cpc_classifications": cpc,
        "url": url,
    }


def _safe_get(obj: dict[str, Any], keys: list[str], default: Any = "") -> Any:
    """Safely traverse nested dict keys."""
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key, default)
        else:
            return default
    return obj if obj is not None else default


def _extract_json_from_html(text: str) -> dict[str, Any]:
    """Fallback: try to extract JSON-LD from HTML response."""
    match = re.search(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        text,
        re.DOTALL,
    )
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return {}


def _flatten_text(value: Any) -> str:
    """Convert a value to a plain string, flattening lists."""
    if isinstance(value, list):
        return "\n".join(str(v) for v in value if v)
    return str(value) if value else ""


# ── MCP Server ────────────────────────────────────────────────────────────

server = Server("patent-search")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_patents",
            description="Search patents by keyword query using Google Patents API. "
            "Returns patent ID, title, abstract, assignee, inventors, dates, "
            "and CPC classifications.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Patent search query (e.g. 'machine learning', 'USPTO')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default 10, max 50)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_patent_details",
            description="Get detailed information for a specific patent by patent ID. "
            "Includes full abstract, claims, assignee, inventors, classifications, "
            "and description when available.",
            inputSchema={
                "type": "object",
                "properties": {
                    "patent_id": {
                        "type": "string",
                        "description": "Patent ID (e.g. US10529241B2, US20200012345A1)",
                    },
                },
                "required": ["patent_id"],
            },
        ),
        Tool(
            name="search_by_assignee",
            description="Search patents by assignee (company or organization name). "
            "Returns patents assigned to the specified entity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "assignee": {
                        "type": "string",
                        "description": "Company or organization name (e.g. 'Apple', 'Microsoft')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default 10, max 50)",
                        "default": 10,
                    },
                },
                "required": ["assignee"],
            },
        ),
        Tool(
            name="search_by_classification",
            description="Search patents by CPC classification code. "
            "Returns patents matching the given CPC class.",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_code": {
                        "type": "string",
                        "description": "CPC classification code (e.g. 'G06N', 'G06F', 'H04L')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default 10, max 50)",
                        "default": 10,
                    },
                },
                "required": ["class_code"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str, arguments: dict[str, Any]
) -> list[TextContent]:
    try:
        if name == "search_patents":
            query = arguments.get("query", "")
            limit = min(int(arguments.get("limit", 10)), 50)
            results = _search_google_patents(query, limit)
            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == "get_patent_details":
            patent_id = arguments.get("patent_id", "")
            details = _get_patent_details_google(patent_id)
            return [TextContent(type="text", text=json.dumps(details, indent=2))]

        elif name == "search_by_assignee":
            assignee = arguments.get("assignee", "")
            limit = min(int(arguments.get("limit", 10)), 50)
            query = f'assignee:"{assignee}"'
            results = _search_google_patents(query, limit)
            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == "search_by_classification":
            class_code = arguments.get("class_code", "")
            limit = min(int(arguments.get("limit", 10)), 50)
            query = f'cpc:"{class_code}"'
            results = _search_google_patents(query, limit)
            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    except httpx.HTTPStatusError as e:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": f"Google Patents API error: {e.response.status_code}",
                        "details": str(e),
                    },
                    indent=2,
                ),
            )
        ]
    except httpx.RequestError as e:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"error": "Network error contacting Google Patents API", "details": str(e)},
                    indent=2,
                ),
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"error": f"Unexpected error: {type(e).__name__}", "details": str(e)},
                    indent=2,
                ),
            )
        ]


# ── Entry Point ───────────────────────────────────────────────────────────

def main() -> None:
    """Run the MCP server using stdio transport."""
    try:
        import anyio
        from mcp.server.stdio import stdio_server

        async def _run():
            async with stdio_server() as (read, write):
                await server.run(read, write, server.create_initialization_options())

        anyio.run(_run)
    except ImportError:
        # Fallback for older versions
        from mcp.server.stdio import stdio_server

        async def _run():
            async with stdio_server() as (read, write):
                await server.run(read, write, server.create_initialization_options())

        import asyncio
        asyncio.run(_run())


if __name__ == "__main__":
    main()
