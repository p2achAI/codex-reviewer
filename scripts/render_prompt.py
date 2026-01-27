#!/usr/bin/env python3
import os
import sys

if len(sys.argv) != 3:
    sys.stderr.write("Usage: render_prompt.py <template> <output>\n")
    sys.exit(2)

template_path = sys.argv[1]
output_path = sys.argv[2]

with open(template_path, "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    "ROLE": os.getenv("ROLE", ""),
    "OUTPUT_FILE": os.getenv("OUTPUT_FILE", ""),
    "LANGUAGE": os.getenv("LANGUAGE", ""),
    "CUSTOM_INSTRUCTIONS": os.getenv("CUSTOM_INSTRUCTIONS", "").strip(),
    "AGENT_FILES": os.getenv("AGENT_FILES", ""),
    "COMMENTS_FILE": os.getenv("COMMENTS_FILE", ""),
    "PR_DESCRIPTION_FILE": os.getenv("PR_DESCRIPTION_FILE", ""),
}

for key, value in replacements.items():
    content = content.replace("{{%s}}" % key, value)

with open(output_path, "w", encoding="utf-8") as f:
    f.write(content)
