# wheels

Linux x86_64 wheels for packages that PyPI has no wheel for yet on a new
CPython. Each wheel is built here once and attached to a release, and every
eolhq project reuses it instead of compiling it in its own Dockerfile.

## Public PyPI releases only

This repository and its releases are public. Only an unmodified sdist of a
public PyPI release is ever built here: never eolhq code or other first-party
software, never a fork or patched copy, and never anything from a git URL, a
local path or a private index. The workflow takes exact `name==version` pins
only, and fails a requirement PyPI does not have. A package we wrote that needs
a wheel is built in its own project's pipeline.

## What gets built

- `packages.txt` lists the requirements, each pinned with `==`.
- `python-versions.txt` lists the Pythons to build them for.

A push to `main` that changes either file builds every requirement for every
Python. To build a single package, run the **Build wheels** workflow by hand
with a `requirement` (and optionally a `python`).

Builds run on GitHub-hosted `ubuntu-latest` (never the self-hosted runners,
since the repo is public) inside `quay.io/pypa/manylinux_2_28_x86_64`. Rust is
installed for sdists that need it, and compiled wheels are tagged by
`auditwheel repair`.

## Where the wheels go

There is one release per CPython tag, for example `cp315`. A wheel already on a
release is **never replaced**. Consumers pin each wheel's hash in `uv.lock`, so
rebuilding one would break every lockfile that holds it. To change a wheel,
bump the requirement's version instead.

Projects point uv straight at the download URL, Linux x86_64 only, so no
fetch step or token is needed in CI, Docker builds or Renovate:

```toml
[tool.uv.sources]
pyyaml = [{ url = "https://github.com/eolhq/wheels/releases/download/cp315/<filename>.whl", marker = "sys_platform == 'linux' and platform_machine == 'x86_64'" }]
```

## Retiring a package

Before building, the workflow asks PyPI whether it already has a wheel that
installs on manylinux x86_64 for every Python listed. A pure-Python
`py3x-none-any` wheel or a compatible `abi3` wheel counts. Requirements that
pass are skipped, and one Discord message lists them.

The same check also runs every Monday on a schedule, because PyPI adding a
wheel changes nothing in this repo. Scheduled runs only check; they never
build.

When the notice comes:

1. Remove the entry from `packages.txt`.
2. In each project that uses it, delete the package's `[tool.uv.sources]`
   line and re-lock.

`uv.lock` pins our wheel's hash, so a project keeps installing our wheel until
it is re-locked.
