"""Register Oh My Pi in native ACP client settings or export ready-to-use JSON."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

from .common import load_json_object, ok, skip, warn, write_atomic_text


def _matches(value: object, required: object) -> bool:
    if isinstance(required, dict):
        return isinstance(value, dict) and all(
            key in value and _matches(value[key], expected)
            for key, expected in required.items()
        )
    return type(value) is type(required) and value == required


def _merge(data: dict[str, object], template: dict[str, object], path: Path) -> bool:
    key, registrations = next(iter(template.items()))
    name, required = next(iter(registrations.items()))
    entries = data.get(key, {})
    if not isinstance(entries, dict):
        raise ValueError(f"{path}: {key} must be an object; existing file preserved")
    if name in entries:
        if not _matches(entries[name], required):
            raise ValueError(
                f"{path}: conflicting OMP registration at {key}.{name}; "
                "existing entry preserved; fix it manually"
            )
        return False
    entries[name] = required
    data[key] = entries
    return True


def _preflight_destination(path: Path, *, exporting: bool) -> Path:
    if exporting and (path.exists() or path.is_symlink()):
        raise FileExistsError(f"{path}: already exists; export never overwrites files")
    if path.is_symlink():
        path.resolve(strict=True)
    if path.exists() and not path.is_file():
        raise ValueError(f"{path}: destination must be a regular file")
    for parent in path.parents:
        if parent.exists() or parent.is_symlink():
            if not parent.is_dir():
                raise NotADirectoryError(f"{parent}: parent is not an existing directory")
            break
    return path.resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Native targets: ~/.jetbrains/acp.json and "
            "${T3CODE_HOME:-~/.t3}/userdata/settings.json. "
            "Close T3 Code before applying its settings. All selected destinations "
            "are preflighted before writing; runtime I/O failures are not rolled back."
        ),
    )
    parser.add_argument(
        "--client", action="append", required=True, choices=("pycharm", "t3code"),
        help="Client to configure; repeat to select both",
    )
    parser.add_argument(
        "--output-dir", type=Path, metavar="PATH",
        help="Export pycharm.json/t3code.json into this exact directory instead of editing settings",
    )
    parser.add_argument(
        "--omp", default="omp", metavar="NAME_OR_PATH",
        help="OMP executable name or path, resolved with PATH lookup (default: omp)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preflight and report changes without writing files, directories or backups",
    )
    args = parser.parse_args(argv)

    try:
        executable = shutil.which(os.path.expanduser(args.omp))
        if executable is None:
            raise ValueError(f"OMP executable not found or not executable: {args.omp}")
        command = str(Path(executable).absolute())
        output_dir = args.output_dir.expanduser().absolute() if args.output_dir is not None else None
        plans: list[tuple[Path, str | None]] = []
        destinations: set[Path] = set()
        for client in dict.fromkeys(args.client):
            template_path = Path(__file__).with_name("acp") / f"{client}.json"
            template = load_json_object(template_path)
            if not template:
                raise ValueError(f"{template_path}: missing or invalid packaged ACP template")
            if client == "pycharm":
                template["agent_servers"]["Oh My Pi"]["command"] = command
                native_path = Path.home() / ".jetbrains" / "acp.json"
            else:
                template["providerInstances"]["acpRegistry_omp"]["config"]["commandPath"] = command
                t3_home = Path(os.environ.get("T3CODE_HOME") or Path.home() / ".t3").expanduser()
                native_path = t3_home.absolute() / "userdata" / "settings.json"
            path = output_dir / f"{client}.json" if output_dir is not None else native_path
            resolved = _preflight_destination(path, exporting=output_dir is not None)
            if resolved in destinations:
                raise ValueError(f"{path}: selected client destinations resolve to the same file")
            destinations.add(resolved)
            if output_dir is not None:
                data, changed = template, True
            else:
                data = load_json_object(path)
                if data is None:
                    return 1
                changed = _merge(data, template, path)
            plans.append((path, json.dumps(data, indent=2) + "\n" if changed else None))

        for path, content in plans:
            if content is None:
                skip(f"{path}: OMP registration already matches")
            elif output_dir is not None and not args.dry_run:
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("x", encoding="utf-8") as stream:
                    stream.write(content)
                ok(f"Exported {path}")
            elif not write_atomic_text(path, content, dry_run=args.dry_run):
                return 1
            elif not args.dry_run:
                ok(f"Configured {path}")
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        warn(f"ACP configuration failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
