from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .commands import author as author_command
from .commands import check as check_command
from .commands import init as init_command
from .commands import integration as integration_command
from .commands import list as list_command
from .commands import repair as repair_command
from .commands import run as run_command
from .commands import validate as validate_command
from .core.errors import CoreIncompatibleError, CoreMissingError, RuntimeInputError
from .workspace.layout import resolve_project_path

EXIT_SUCCESS = 0
EXIT_VALIDATION_FAILED = 2
EXIT_CORE_FAILED = 3
EXIT_APPROVAL_REQUIRED = 4
EXIT_INPUT_MISSING = 5


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="proofsignal-spec", description="ProofSignal Spec CLI")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Initialize a target repository")
    init_parser.add_argument("project_path", nargs="?")
    init_parser.add_argument("--here", action="store_true")
    init_parser.add_argument("--integration", choices=["codex", "claude"], required=True)
    init_parser.add_argument("--force", action="store_true")
    init_parser.add_argument("--core-cmd", help="ProofSignal Core executable, command string, or local Core repository path")
    init_parser.add_argument("--json", action="store_true")

    check_parser = subparsers.add_parser("check", help="Check workspace and Core readiness")
    check_parser.add_argument("--project", default=".")
    check_parser.add_argument("--core-cmd", help="ProofSignal Core executable, command string, or local Core repository path")
    check_parser.add_argument("--json", action="store_true")

    author_parser = subparsers.add_parser("author", help="Author a browser use case")
    author_parser.add_argument("alias")
    author_parser.add_argument("description")
    author_parser.add_argument("--project", default=".")
    author_parser.add_argument("--run-request")
    author_parser.add_argument("--skill", action="append", default=[])
    author_parser.add_argument("--json", action="store_true")

    list_parser = subparsers.add_parser("list", help="List use cases")
    list_parser.add_argument("--project", default=".")
    list_parser.add_argument("--json", action="store_true")

    validate_parser = subparsers.add_parser("validate", help="Validate a use case")
    validate_parser.add_argument("alias")
    validate_parser.add_argument("--project", default=".")
    validate_parser.add_argument("--runtime-readiness", action="store_true")
    validate_parser.add_argument("--core-cmd", help="Override configured ProofSignal Core command")
    validate_parser.add_argument("--json", action="store_true")

    run_parser = subparsers.add_parser("run", help="Run a use case")
    run_parser.add_argument("alias")
    run_parser.add_argument("--project", default=".")
    run_parser.add_argument("--profile", default="normal", choices=["normal", "debug"])
    run_parser.add_argument("--core-cmd", help="Override configured ProofSignal Core command")
    run_parser.add_argument("--json", action="store_true")
    run_parser.add_argument("--non-interactive", action="store_true")

    repair_parser = subparsers.add_parser("repair", help="Repair a use case")
    repair_parser.add_argument("alias")
    repair_parser.add_argument("--project", default=".")
    repair_parser.add_argument("--from-report")
    repair_parser.add_argument("--approve", action="store_true")
    repair_parser.add_argument("--core-cmd", help="Override configured ProofSignal Core command")
    repair_parser.add_argument("--json", action="store_true")

    core_parser = subparsers.add_parser("core", help="Inspect configured ProofSignal Core")
    core_sub = core_parser.add_subparsers(dest="core_command", required=True)
    core_version = core_sub.add_parser("version")
    core_version.add_argument("--project", default=".")
    core_version.add_argument("--core-cmd", help="ProofSignal Core executable, command string, or local Core repository path")
    core_version.add_argument("--json", action="store_true")

    integration_parser = subparsers.add_parser("integration", help="Manage agent integrations")
    integration_sub = integration_parser.add_subparsers(dest="integration_command", required=True)
    integration_list = integration_sub.add_parser("list")
    integration_list.add_argument("--project", default=".")
    integration_list.add_argument("--json", action="store_true")
    for action in ["install", "use", "remove"]:
        child = integration_sub.add_parser(action)
        child.add_argument("key", choices=["codex", "claude"])
        child.add_argument("--project", default=".")
        child.add_argument("--force", action="store_true")
        child.add_argument("--json", action="store_true")
    upgrade = integration_sub.add_parser("upgrade")
    upgrade.add_argument("key", choices=["codex", "claude"], nargs="?")
    upgrade.add_argument("--project", default=".")
    upgrade.add_argument("--force", action="store_true")
    upgrade.add_argument("--json", action="store_true")

    return parser


def create_app() -> argparse.ArgumentParser:
    """Return the CLI application object.

    The implementation uses argparse as a no-network bootstrap fallback while
    the package still declares Typer/Rich as planned dependencies for future
    richer command rendering.
    """
    return create_parser()


def main(argv: list[str] | None = None) -> int:
    parser = create_app()
    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return EXIT_SUCCESS
    if not args.command:
        parser.print_help()
        return EXIT_SUCCESS
    try:
        result, json_output = dispatch(args)
        emit(result, json_output=json_output)
        return exit_code_for_result(args.command, result)
    except RuntimeInputError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_INPUT_MISSING
    except (CoreMissingError, CoreIncompatibleError) as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_CORE_FAILED
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_VALIDATION_FAILED
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def dispatch(args: argparse.Namespace) -> tuple[dict[str, Any], bool]:
    command = args.command
    if command == "init":
        project = resolve_project_path(args.project_path, here=args.here)
        return init_command.run(project, args.integration, force=args.force, core_cmd=args.core_cmd), args.json
    if command == "check":
        return check_command.run(Path(args.project).resolve(), core_cmd=args.core_cmd), args.json
    if command == "author":
        return author_command.run(Path(args.project).resolve(), args.alias, args.description, run_request=args.run_request, skills=args.skill), args.json
    if command == "list":
        return list_command.run(Path(args.project).resolve()), args.json
    if command == "validate":
        return validate_command.run(Path(args.project).resolve(), args.alias, runtime_readiness=args.runtime_readiness, core_cmd=args.core_cmd), args.json
    if command == "run":
        return run_command.run(Path(args.project).resolve(), args.alias, profile_name=args.profile, interactive=not args.non_interactive, core_cmd=args.core_cmd), args.json
    if command == "repair":
        return repair_command.run(Path(args.project).resolve(), args.alias, from_report=args.from_report, approve=args.approve, core_cmd=args.core_cmd), args.json
    if command == "core":
        from .core.adapter import CoreAdapter
        from .workspace.repository import get_core_command

        project = Path(args.project).resolve()
        if args.core_command == "version":
            return CoreAdapter(executable=args.core_cmd or get_core_command(project), cwd=project).version(), args.json
    if command == "integration":
        project = Path(args.project).resolve()
        if args.integration_command == "list":
            return integration_command.list_integrations(project), args.json
        if args.integration_command == "install":
            return integration_command.install(project, args.key, force=args.force), args.json
        if args.integration_command == "use":
            return integration_command.use(project, args.key), args.json
        if args.integration_command == "upgrade":
            return integration_command.upgrade(project, args.key, force=args.force), args.json
        if args.integration_command == "remove":
            return integration_command.remove(project, args.key, force=args.force), args.json
    raise ValueError(f"Unsupported command: {command}")


def emit(result: dict[str, Any], json_output: bool = False) -> None:
    if json_output:
        print(json.dumps(result, indent=2, sort_keys=False))
        return
    if "useCases" in result:
        for item in result["useCases"]:
            print(f"{item.get('alias', '-'):<24} {item.get('status', item.get('runnableStatus', '-')):<10} {item.get('title', '')}")
        for warning in result.get("warnings", []):
            print(f"warning: {warning}", file=sys.stderr)
        return
    if "workspacePath" in result:
        print(f"Workspace: {result['workspacePath']}")
        print(f"Integration: {result['integration']}")
        print(f"Core: {result['core'].get('message')}")
        print(result.get("next", ""))
        return
    if "status" in result and "workspace" in result:
        print(f"Status: {result['status']}")
        print(f"Workspace: {result['workspace']['path']}")
        print(f"Core: {result['core'].get('message')}")
        return
    print(json.dumps(result, indent=2, sort_keys=False))


def exit_code_for_result(command: str, result: dict[str, Any]) -> int:
    status = result.get("status")
    if command == "check" and status != "passed":
        return EXIT_VALIDATION_FAILED
    if command == "repair" and result.get("repair", {}).get("approvalStatus") == "pending":
        return EXIT_APPROVAL_REQUIRED
    if status in {"blocked", "error"}:
        return EXIT_VALIDATION_FAILED
    return EXIT_SUCCESS
