"""Print the release notes for a version from ``CHANGELOG.md``.

Used by the ``Release`` workflow. Prints the body of the ``## [<version>]`` section; if there is
none (or it is empty), the body of ``## [Unreleased]``; if that is empty too, nothing.

Run locally:
    python scripts/release_notes.py 1.2.0
"""

import argparse
import re
from pathlib import Path

HEADING = re.compile(r"^## \[(?P<name>[^\]]+)\]")


def section(changelog: str, name: str) -> str:
    """Return the text below the ``## [name]`` heading, up to the next ``## [`` heading."""
    lines: list[str] = []
    inside = False
    for line in changelog.splitlines():
        match = HEADING.match(line)
        if match:
            if inside:
                break
            inside = match["name"].lower() == name.lower()
            continue
        if inside:
            lines.append(line)
    return "\n".join(lines).strip()


def release_notes(changelog: str, version: str) -> str:
    return section(changelog, version) or section(changelog, "Unreleased")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("version", help="version without the leading v, e.g. 1.2.0")
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    args = parser.parse_args()
    notes = release_notes(args.changelog.read_text(encoding="utf-8"), args.version)
    if notes:
        print(notes)


if __name__ == "__main__":
    main()
