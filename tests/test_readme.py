"""The README example and examples/readme_example.py (rendered to the README image) must match."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_readme_example_matches_rendered_example():
    if not (ROOT / "examples" / "readme_example.py").exists():
        pytest.skip("examples/ is not part of the sdist")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    block = re.search(r"```python\n(.*?)```", readme, re.DOTALL)
    assert block, "README has no python code block"
    shown = block.group(1).removesuffix("fig\n").strip()

    source = (ROOT / "examples" / "readme_example.py").read_text(encoding="utf-8")
    code = source.split('"""', 2)[2].strip()  # without the module docstring

    assert shown == code, (
        "README example and examples/readme_example.py differ; CI renders the README image "
        "from the file, so update both"
    )
