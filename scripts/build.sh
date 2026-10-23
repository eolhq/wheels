#!/usr/bin/env bash
# Runs inside the manylinux image. Builds one wheel per requirement for one
# CPython and writes the repaired wheels to $OUT.
#
# Usage: build.sh <python-version> <out-dir> <requirement>...
set -euo pipefail

python_version=$1 out=$2
shift 2

tag="cp${python_version/./}"
py="/opt/python/${tag}-${tag}/bin/python"
if [[ ! -x $py ]]; then
	echo "this manylinux image has no ${tag} interpreter; available: $(ls /opt/python)" >&2
	exit 1
fi

# Some sdists (cbor2) build a Rust extension; the image ships no Rust.
if ! command -v cargo >/dev/null; then
	curl -sSf https://sh.rustup.rs | sh -s -- -y -q --profile minimal
	# shellcheck disable=SC1091
	. "$HOME/.cargo/env"
fi

work=$(mktemp -d)
mkdir -p "$out"
for req in "$@"; do
	# Only the requirement itself comes from source; its build backend still
	# installs from wheels, which --no-binary :all: on `pip wheel` would forbid.
	"$py" -m pip download --quiet --no-deps --no-binary :all: --dest "$work/sdist" "$req"
done

for sdist in "$work"/sdist/*; do
	"$py" -m pip wheel --quiet --no-deps --wheel-dir "$work/raw" "$sdist"
done

for wheel in "$work"/raw/*.whl; do
	case $wheel in
	*-none-any.whl) cp "$wheel" "$out/" ;;
	*) auditwheel repair --wheel-dir "$out" "$wheel" ;;
	esac
done

# A wheel that installs on the interpreter it was built for is the minimum bar
# before it is published and pinned by hash in consumers' lockfiles.
"$py" -m pip install --quiet --no-deps --no-index --target "$work/installed" "$out"/*.whl

ls -l "$out"
