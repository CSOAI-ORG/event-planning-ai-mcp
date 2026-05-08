<div align="center">

# Event Planning Ai MCP

**Event Planning AI MCP Server**

[![PyPI](https://img.shields.io/pypi/v/meok-event-planning-ai-mcp)](https://pypi.org/project/meok-event-planning-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Event Planning AI MCP Server
Event management tools powered by MEOK AI Labs.

## Tools

| Tool | Description |
|------|-------------|
| `calculate_venue_capacity` | Calculate venue capacity for different seating layouts. |
| `plan_budget` | Create an event budget plan with cost breakdowns and tracking. |
| `optimize_schedule` | Optimize event schedule with breaks, room assignments, and time slots. |
| `manage_guest_list` | Manage guest list with RSVP tracking, dietary needs, and table assignments. |
| `estimate_catering` | Estimate catering costs and quantities for an event. |

## Installation

```bash
pip install meok-event-planning-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "event-planning-ai": {
      "command": "python",
      "args": ["-m", "meok_event_planning_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 5 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
