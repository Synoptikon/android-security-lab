"""CLI for the controlled FRP simulator. No real-device operations."""
from __future__ import annotations

import argparse
from pathlib import Path

from core import VirtualDevice, run_full_scenario, run_setup_wizard_scenario


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Controlled Android FRP state simulator")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("device_id")
    show = sub.add_parser("show")
    show.add_argument("state_file", type=Path)
    run = sub.add_parser("scenario")
    run.add_argument("device_id")
    run.add_argument("token", help="Synthetic LAB-FRP-XXXXXXXX token")
    run.add_argument("--out", type=Path)
    wizard = sub.add_parser("setup-wizard")
    wizard.add_argument("device_id")
    wizard.add_argument("--profile", default="lab-default")
    wizard.add_argument("--out", type=Path)
    return parser


def _write_or_print(payload: str, output: Path | None) -> None:
    if output:
        output.write_text(payload + "\n")
    else:
        print(payload)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "create":
        print(VirtualDevice(args.device_id).to_json())
        return 0
    if args.command == "show":
        print(VirtualDevice.from_json(args.state_file.read_text()).to_json())
        return 0
    if args.command == "scenario":
        _write_or_print(run_full_scenario(args.device_id, args.token).to_json(), args.out)
        return 0
    if args.command == "setup-wizard":
        _write_or_print(run_setup_wizard_scenario(args.device_id, args.profile).to_json(), args.out)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
