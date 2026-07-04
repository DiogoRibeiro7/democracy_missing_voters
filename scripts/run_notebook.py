from __future__ import annotations

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    notebook_path = repo_root / "notebooks" / "democracy_missing_voters_analysis.ipynb"

    notebook = nbformat.read(notebook_path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=300,
        kernel_name="python3",
        resources={"metadata": {"path": str(repo_root)}},
    )

    try:
        client.execute()
    except Exception as exc:  # pragma: no cover
        print(f"Notebook execution failed: {exc}", file=sys.stderr)
        return 1

    nbformat.write(notebook, notebook_path)
    print(notebook_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
