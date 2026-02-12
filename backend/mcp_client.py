import json
import shlex
import subprocess
from typing import Any, Dict, Optional


def build_command(command: str) -> list:
    return shlex.split(command)


class MCPStdioClient:
    def __init__(self, command: str) -> None:
        self.command = command
        self.process: Optional[subprocess.Popen[str]] = None
        self.request_id = 0

    def __enter__(self) -> "MCPStdioClient":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start(self) -> None:
        if self.process:
            return
        self.process = subprocess.Popen(
            build_command(self.command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self._send({"jsonrpc": "2.0", "id": self._next_id(), "method": "initialize", "params": {}})
        self._read_response()

    def stop(self) -> None:
        if not self.process:
            return
        if self.process.stdin:
            self.process.stdin.close()
        self.process.terminate()
        self.process = None

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments}
        }
        self._send(payload)
        response = self._read_response()
        if "error" in response:
            raise RuntimeError(response["error"]["message"])
        return response.get("result")

    def _send(self, message: Dict[str, Any]) -> None:
        if not self.process or not self.process.stdin:
            raise RuntimeError("MCP server not started")
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def _read_response(self) -> Dict[str, Any]:
        if not self.process or not self.process.stdout:
            raise RuntimeError("MCP server not started")
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("MCP server closed")
        return json.loads(line)

    def _next_id(self) -> int:
        self.request_id += 1
        return self.request_id
