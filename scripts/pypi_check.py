"""Drop requirements that PyPI already ships a usable wheel for.

Reads REQUIREMENTS and PYTHONS (space-separated) from the environment, writes
the requirements still worth building to $GITHUB_OUTPUT as `build`, and posts
one Discord message listing the ones that can be retired. A requirement is
kept unless PyPI has a manylinux x86_64 (or pure-Python) wheel for every
Python being built: a wheel for 3.15 but not a later version listed still
needs ours for that later version.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request

PYPI_URL = "https://pypi.org/pypi/{name}/{version}/json"
REPO_URL = "https://github.com/eolhq/wheels"


def wheel_tags(filename):
    """(python, abi, platform) of a wheel filename, or None for an sdist."""
    if not filename.endswith(".whl"):
        return None
    parts = filename[: -len(".whl")].split("-")
    return parts[-3], parts[-2], parts[-1]


def serves(filename, python_version):
    """Whether a PyPI file installs on CPython `python_version` on manylinux x86_64."""
    tags = wheel_tags(filename)
    if tags is None:
        return False
    py, abi, platform = tags
    # Each field can be a compressed tag set: py2.py3, manylinux_2_17_x86_64.manylinux2014_x86_64.
    linux = any(p.startswith("manylinux") and p.endswith("x86_64") for p in platform.split("."))
    if abi == "none" and (platform == "any" or linux) and any(t.startswith("py3") for t in py.split(".")):
        return True
    if not linux:
        return False
    target = int(python_version.split(".")[1])
    for tag in py.split("."):
        minor = re.fullmatch(r"cp3(\d+)", tag)
        if not minor:
            continue
        if abi == "abi3" and int(minor.group(1)) <= target:
            return True
        if int(minor.group(1)) == target:
            return True
    return False


def pypi_files(requirement):
    name, version = requirement.split("==")
    try:
        with urllib.request.urlopen(PYPI_URL.format(name=name, version=version), timeout=30) as response:
            return [f["filename"] for f in json.load(response)["urls"]]
    except urllib.error.HTTPError as error:
        if error.code == 404:
            sys.exit(f"{requirement} is not on PyPI")
        raise


def notify(retirable, pythons):
    webhook = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook:
        print("::warning::DISCORD_WEBHOOK_URL is not set; no Discord notice sent")
        return
    names = ", ".join(f"**{r}**" for r in retirable)
    content = (
        f"🧹 PyPI now ships a wheel for {names} on Python {', '.join(pythons)}. "
        f"Remove it from packages.txt in eolhq/wheels, then delete its `[tool.uv.sources]` "
        f"entry and re-lock in each project that uses it: {REPO_URL}/blob/main/packages.txt"
    )
    request = urllib.request.Request(
        webhook,
        data=json.dumps({"content": content}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "eolhq-wheels"},
    )
    with urllib.request.urlopen(request, timeout=30):
        pass


def main():
    requirements = os.environ["REQUIREMENTS"].split()
    pythons = os.environ["PYTHONS"].split()

    build, retirable = [], []
    for requirement in requirements:
        files = pypi_files(requirement)
        if all(any(serves(f, py) for f in files) for py in pythons):
            retirable.append(requirement)
            print(f"::notice::PyPI ships a wheel for {requirement} on {' '.join(pythons)}; not building it")
        else:
            build.append(requirement)

    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"build={' '.join(build)}\n")
    if retirable:
        notify(retirable, pythons)


if __name__ == "__main__":
    main()
