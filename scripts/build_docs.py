"""Build the documentation site published on GitHub Pages.

* executes ``examples/examples.ipynb`` and renders it to ``index.html`` with interactive plotly
  figures (plotly.js is loaded from plotly's CDN),
* copies the executed notebook next to it (``examples.ipynb``, for download),
* renders the README example to ``images/readme-example.png`` (static image via kaleido).

Nothing of this is committed: CI uploads the output directory as an artifact (pull requests)
and deploys it to GitHub Pages (main).

Run locally:
    uv run --group notebook --with "nbconvert>=7.16" --with "kaleido>=1.0" \\
        python scripts/build_docs.py --out site
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK = ROOT / "examples" / "examples.ipynb"
README_EXAMPLE = ROOT / "examples" / "readme_example.py"
TIMEOUT_PER_CELL = 300  # seconds


def build_gallery(out: Path) -> None:
    import nbformat
    from nbclient import NotebookClient
    from nbconvert import HTMLExporter

    # Self-contained HTML output for every figure, plotly.js from the CDN. Set before the kernel
    # starts, which inherits the environment.
    os.environ["PLOTLY_RENDERER"] = "notebook_connected"
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    NotebookClient(
        notebook,
        timeout=TIMEOUT_PER_CELL,
        kernel_name="python3",
        resources={"metadata": {"path": str(NOTEBOOK.parent)}},
    ).execute()

    nbformat.write(notebook, out / "examples.ipynb")
    exporter = HTMLExporter(template_name="lab")
    html, _ = exporter.from_notebook_node(
        notebook, resources={"metadata": {"name": "plotlywaterfall examples"}}
    )
    (out / "index.html").write_text(html, encoding="utf-8")
    print(f"wrote {out / 'index.html'} ({len(html) / 1e6:.1f} MB)")


def build_readme_image(out: Path) -> None:
    import runpy

    figure = runpy.run_path(str(README_EXAMPLE))["fig"]
    images = out / "images"
    images.mkdir(parents=True, exist_ok=True)
    target = images / "readme-example.png"
    try:
        figure.write_image(target, width=1000, height=500, scale=2)
    except Exception as exc:  # kaleido cannot find a Chrome: download one and retry
        print(f"write_image failed ({exc}); installing Chrome for kaleido", file=sys.stderr)
        import kaleido

        kaleido.get_chrome_sync()
        figure.write_image(target, width=1000, height=500, scale=2)
    print(f"wrote {target}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=ROOT / "site", help="output directory")
    args = parser.parse_args()

    out: Path = args.out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / ".nojekyll").touch()  # serve files as they are

    build_gallery(out)
    build_readme_image(out)


if __name__ == "__main__":
    main()
