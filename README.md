# Event Planning AI MCP

> Event management tools - venue capacity, budgets, schedules, guest lists, catering estimates

Built by **MEOK AI Labs** | [meok.ai](https://meok.ai)

## Features

| Tool | Description |
|------|-------------|
| `calculate_venue_capacity` | See tool docstring for details |
| `plan_budget` | See tool docstring for details |
| `optimize_schedule` | See tool docstring for details |
| `manage_guest_list` | See tool docstring for details |
| `estimate_catering` | See tool docstring for details |

## Installation

```bash
pip install mcp
```

## Usage

### As an MCP Server

```bash
python server.py
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "event-planning-ai-mcp": {
      "command": "python",
      "args": ["/path/to/event-planning-ai-mcp/server.py"]
    }
  }
}
```

## Rate Limits

Free tier includes **30-50 calls per tool per day**. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with FastMCP by MEOK AI Labs
