"""Cliente mínimo para el complemento Blender MCP (socket JSON en localhost:9876).

Uso:
    python blender/mcp_client.py ping
    python blender/mcp_client.py exec ruta/al/script.py
    python blender/mcp_client.py info
"""

import json
import socket
import sys

HOST, PORT = "localhost", 9876


def send(command: dict, timeout: float = 600.0) -> dict:
    with socket.create_connection((HOST, PORT), timeout=timeout) as s:
        s.sendall(json.dumps(command).encode("utf-8"))
        buffer = b""
        # el complemento responde con un único objeto JSON
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            buffer += chunk
            try:
                return json.loads(buffer.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
    raise RuntimeError("Respuesta vacía o incompleta de Blender")


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "ping"
    if action == "ping":
        result = send({"type": "ping"})
    elif action == "info":
        result = send({"type": "get_scene_info"})
    elif action == "exec":
        with open(sys.argv[2], encoding="utf-8") as f:
            result = send({"type": "execute_code", "params": {"code": f.read()}})
    else:
        sys.exit(f"Acción desconocida: {action}")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:8000])
    if result.get("status") != "success":
        sys.exit(1)


if __name__ == "__main__":
    main()
