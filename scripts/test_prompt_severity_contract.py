import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPTS = (
    ROOT / "prompt.txt",
    ROOT / "prompts" / "agent_base.txt",
    ROOT / "prompts" / "agent_spec.txt",
    ROOT / "prompts" / "aggregate.txt",
)

REQUIRED_GUARDS = (
    "Blocking severity guard:",
    "P0, P1, and P2 require a concrete incorrect observable behavior",
    "State the trigger, affected execution path, and incorrect outcome",
    "must not be P0, P1, or P2",
    "explicit authoritative contract or fail-closed constraint",
    "self-audit every P0-P2 finding",
)


class PromptSeverityContractTest(unittest.TestCase):
    def test_every_builtin_prompt_enforces_blocking_severity_guard(self) -> None:
        for prompt in PROMPTS:
            with self.subTest(prompt=prompt.relative_to(ROOT)):
                text = prompt.read_text(encoding="utf-8")
                for guard in REQUIRED_GUARDS:
                    self.assertIn(guard, text)

    def test_builtin_prompt_inventory_is_explicit(self) -> None:
        prompt_files = {ROOT / "prompt.txt", *ROOT.glob("prompts/*.txt")}
        self.assertEqual(set(PROMPTS), prompt_files)


if __name__ == "__main__":
    unittest.main()
