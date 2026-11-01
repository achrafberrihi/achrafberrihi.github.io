"""Checks that every niche file in the prompt library is complete and well-formed."""
import re
from pathlib import Path

NICHES = sorted((Path(__file__).parent / "niches").glob("*.md"))


def test_there_are_19_niches():
    assert len(NICHES) == 19


def test_each_niche_has_five_complete_prompts():
    for path in NICHES:
        text = path.read_text(encoding="utf-8")
        titles = re.findall(r"^## \d+\. .+$", text, re.M)
        blocks = re.findall(r"```text\n.+?```", text, re.S)
        tips = re.findall(r"^> \*\*Why it works:\*\*", text, re.M)
        assert len(titles) == len(blocks) == len(tips) == 5, path.name


def test_index_links_every_niche():
    index = (Path(__file__).parent / "example_prompts.md").read_text(encoding="utf-8")
    for path in NICHES:
        assert f"niches/{path.name}" in index, path.name
