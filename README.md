# wheels

Linux x86_64 wheels for packages that PyPI has no wheel for yet on a new
CPython. Each wheel is built here once and attached to a release, and every
eolhq project reuses it instead of compiling it in its own Dockerfile.

## What gets built

- `packages.txt` lists the requirements, each pinned with `==`.
- `python-versions.txt` lists the Pythons to build them for.

A push to `main` that changes either file builds every requirement for every
Python. To build a single package, run the **Build wheels** workflow by hand
with a `requirement` (and optionally a `python`).

Builds run on `np-amd64` inside `quay.io/pypa/manylinux_2_28_x86_64`. Rust is
installed for sdists that need it, and compiled wheels are tagged by
`auditwheel repair`.

## Where the wheels go

There is one release per CPython tag, for example `cp315`. A wheel already on a
release is **never replaced**. Consumers pin each wheel's hash in `uv.lock`, so
rebuilding one would break every lockfile that holds it. To change a wheel,
bump the requirement's version instead.

Download them with:

```sh
gh release download cp315 --repo eolhq/wheels --dir wheels
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
