from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


TEMPLATE = Path(__file__).resolve().parents[1] / "agentic_env/vendored/mattpocock/skills/wizard/template.sh"
KEEP_TOKEN = (
    '\nENV_FILE="$1"\n'
    + '"$2" WIZARD_TOKEN "Keep token:"\n'
    + 'printf "%s" "$WIZARD_TOKEN" > "$ENV_FILE.kept"\n'
    + 'write_env WIZARD_TOKEN "$WIZARD_TOKEN"\n'
)


def wizard_library() -> str:
    # Without the marker the split keeps the example stages, which open a browser
    # and set real GitHub secrets.
    library, marker, _ = TEMPLATE.read_text().partition("\nrun_wizard() {")
    if not marker:
        raise AssertionError("template.sh lost its run_wizard marker")
    return library


def parse_env(path: Path) -> dict[str, str]:
    parsed = subprocess.run(
        ["node", "-e", "const fs = require('node:fs'); "
         "const {parseEnv} = require('node:util'); "
         "console.log(JSON.stringify(parseEnv(fs.readFileSync(process.argv[1], 'utf8'))));",
         str(path)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(parsed.stdout)


@unittest.skipUnless(shutil.which("bash") and shutil.which("node"), "requires Bash and Node.js")
class WizardTests(unittest.TestCase):
    def test_saved_values_survive_dotenv_loading_and_keep_current(self) -> None:
        library = wizard_library()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wizard = root / "wizard.sh"
            wizard.write_text(
                library
                + '\nENV_FILE="$1"\n'
                + 'write_env WIZARD_TOKEN "$2"\n'
                + 'cp "$ENV_FILE" "$ENV_FILE.before"\n'
                + 'ask_secret WIZARD_TOKEN "Keep token:"\n'
                + 'printf "%s" "$WIZARD_TOKEN" > "$ENV_FILE.kept"\n'
                + 'write_env WIZARD_TOKEN "$WIZARD_TOKEN"\n'
            )
            for value in (
                "demo's-token",
                '  say "hello" # $HOME =  ',
                r"C:\new\raw",
                r"it's $HOME\path # token",
                "",
            ):
                with self.subTest(value=value):
                    env_file = root / ".env"
                    result = subprocess.run(
                        ["bash", str(wizard), str(env_file), value],
                        input="\n", capture_output=True, text=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual((root / ".env.kept").read_text(), value)
                    self.assertEqual(parse_env(env_file)["WIZARD_TOKEN"], value)
                    self.assertEqual(env_file.read_bytes(), (root / ".env.before").read_bytes())

    def test_unrepresentable_values_leave_existing_configuration_untouched(self) -> None:
        library = wizard_library()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wizard = root / "wizard.sh"
            wizard.write_text(library + '\nENV_FILE="$1"\nwrite_env WIZARD_TOKEN "$2"\n')
            env_file = root / ".env"
            original = "KEEP='existing configuration'\n"
            env_file.write_text(original)
            for value in ("both ' and \" quotes", "two\nlines", "carriage\rreturn", r"it's \new"):
                with self.subTest(value=value):
                    result = subprocess.run(
                        ["bash", str(wizard), str(env_file), value],
                        capture_output=True, text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(env_file.read_text(), original)

    def test_enter_keeps_hand_written_values_as_dotenv_reads_them(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wizard = root / "wizard.sh"
            wizard.write_text(wizard_library() + KEEP_TOKEN)
            env_file = root / ".env"
            for seed, value in (
                ("abc # note", "abc"),
                ("  abc  ", "abc"),
                ('"abc" # note', "abc"),
                ("'x y' # note", "x y"),
                (" 'a#b'  ", "a#b"),
                ('say "hi"', 'say "hi"'),
            ):
                for prompt in ("ask", "ask_secret"):
                    with self.subTest(seed=seed, prompt=prompt):
                        env_file.write_text(f"WIZARD_TOKEN={seed}\n")
                        self.assertEqual(parse_env(env_file)["WIZARD_TOKEN"], value)
                        result = subprocess.run(
                            ["bash", str(wizard), str(env_file), prompt],
                            input="\n", capture_output=True, text=True,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual((root / ".env.kept").read_text(), value)
                        self.assertEqual(parse_env(env_file)["WIZARD_TOKEN"], value)

    def test_enter_refuses_values_it_cannot_keep_as_written(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wizard = root / "wizard.sh"
            wizard.write_text(wizard_library() + KEEP_TOKEN)
            env_file = root / ".env"
            for seed in ('"a\\nb"', "'it's'", '"abc', "abc#x", "`x`"):
                for prompt in ("ask", "ask_secret"):
                    with self.subTest(seed=seed, prompt=prompt):
                        original = f"KEEP='existing'\nWIZARD_TOKEN={seed}\n"
                        env_file.write_text(original)
                        result = subprocess.run(
                            ["bash", str(wizard), str(env_file), prompt],
                            input="\n", capture_output=True, text=True,
                        )
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("WIZARD_TOKEN", result.stderr)
                        self.assertEqual(env_file.read_text(), original)
