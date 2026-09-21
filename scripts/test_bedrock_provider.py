"""Exercise the review entry point without contacting model providers."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BedrockProviderTest(unittest.TestCase):
    def test_bedrock_preserves_model_and_effort_for_all_labels(self):
        for label in ('codex-review', 'codex-review-high'):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                work = Path(tmp)
                (work / 'pr.diff').write_text('diff --git a/example b/example\n')
                mock = work / 'codex'
                mock.write_text('''#!/usr/bin/env python3
import json, pathlib, sys
pathlib.Path('args.json').write_text(json.dumps(sys.argv[1:]))
pathlib.Path('review.md').write_text('Review completed.\\n')
''')
                mock.chmod(0o755)
                env = dict(os.environ, PROVIDER='bedrock', MODEL='global.openai.gpt-5.6-terra',
                           EFFORT='medium', BEDROCK_REGION='ap-northeast-2',
                           TRIGGER_LABEL=label, WORKDIR=tmp, ACTION_DIR=str(ROOT),
                           CODEX_BIN=str(mock), SKIP_REMOTE_CONTEXT='true',
                           CUSTOM_PROMPT='Read pr.diff and review.', CODEX_EXEC_MODE='ci')
                env.pop('OPENAI_API_KEY', None)
                env.pop('ANTHROPIC_API_KEY', None)
                subprocess.run(['bash', str(ROOT / 'scripts/run_review.sh')],
                               env=env, check=True, capture_output=True, text=True)
                args = json.loads((work / 'args.json').read_text())
                self.assertEqual(args[args.index('-m') + 1], 'global.openai.gpt-5.6-terra')
                self.assertIn('model_provider="amazon-bedrock-runtime"', args)
                self.assertIn('model_reasoning_effort="medium"', args)
                self.assertIn('model_providers.amazon-bedrock-runtime.aws.region="ap-northeast-2"', args)
                self.assertNotIn('--reasoning-effort', args)
                self.assertTrue((work / 'review.md').read_text().strip())

    def test_unknown_provider_fails_before_review(self):
        result = subprocess.run(['bash', str(ROOT / 'scripts/run_review.sh')],
                                env=dict(os.environ, PROVIDER='typo'), capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b'Unsupported provider', result.stderr)


if __name__ == '__main__':
    unittest.main()
