#!/usr/bin/env python3
import json
import sys

if len(sys.argv) != 2:
    sys.stderr.write("Usage: list_agents.py <agents.json>\n")
    sys.exit(2)

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

agents = data.get("agents", [])
for agent in agents:
    name = agent.get("name", "").strip()
    role = agent.get("role", "").strip()
    prompt = agent.get("prompt", "").strip()
    if not name or not prompt:
        continue
    print(f"{name}|{role}|{prompt}")
