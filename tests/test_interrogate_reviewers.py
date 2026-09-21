from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "agentic_env/vendored/pstack/skills/interrogate/scripts/run_reviewers.py"


class InterrogateReviewerTests(unittest.TestCase):
    def test_failed_and_aliased_responses_do_not_establish_model_diversity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prompt = root / "prompt.txt"
            prompt.write_text("Review the supplied fixture, report only.\n")
            # A protocol fixture, not evidence of real provider access. Real-model
            # routing is exercised separately by the installation smoke run.
            client = root / "omp-fixture"
            client.write_text(
                f"#!{sys.executable}\n"
                "import json, sys\n"
                "requested = sys.argv[sys.argv.index('--model') + 1]\n"
                "sys.stdin.buffer.read()\n"
                "message = {'role': 'assistant', 'provider': 'fixture', 'model': 'one', "
                "'stopReason': 'stop', 'content': [{'type': 'text', 'text': 'Review complete.'}]}\n"
                "if requested == 'fixture/broken':\n"
                "    message.update(model='two', stopReason='error', errorMessage='upstream disconnected')\n"
                "print(json.dumps({'type': 'turn_end', 'message': message}))\n"
            )
            client.chmod(0o755)
            output = root / "reviews"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--omp", str(client),
                 "--prompt", str(prompt), "--output", str(output),
                 "--model", "fixture/one", "--model", "fixture/alias", "--model", "fixture/broken"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            summary = json.loads((output / "reviewers.json").read_text())
            self.assertEqual(summary["distinct_models"], ["fixture/one"])
            reviewers = summary["reviewers"]
            self.assertEqual(reviewers[1]["returned"], "fixture/one")
            self.assertEqual(reviewers[2]["status"], "error")
            self.assertIsNone(reviewers[2]["review_file"])
            self.assertIn("upstream disconnected", reviewers[2]["error"])
            self.assertNotEqual(reviewers[0]["review_file"], reviewers[1]["review_file"])
            self.assertIn(
                {"requested": "fixture/alias", "returned": "fixture/one"},
                summary["substitutions"],
            )
