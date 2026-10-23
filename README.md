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

Once PyPI publishes a manylinux wheel for a package on every Python listed,
remove it from `packages.txt`. Then re-lock the consumers so they take PyPI's
wheel.
