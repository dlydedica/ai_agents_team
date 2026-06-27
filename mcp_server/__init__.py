"""MCP Server task store - re-export for easy importing."""
import sys
from pathlib import Path

# Add the mcp-server directory to path
_server_dir = Path(__file__).resolve().parent.parent / "mcp-server"
if str(_server_dir) not in sys.path:
    sys.path.insert(0, str(_server_dir))
