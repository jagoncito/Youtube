#!/usr/bin/env bash
set -euo pipefail
# Build into a user-writable cache; never needs system package installation.
# Dependencies: git, GCC/G++, make, Python/pip. Keep normal TLS/proxy settings.
cache="${1:?Specify a writable build directory}"
mkdir -p "$cache"
python -m pip install --target "$cache/tools" 'cmake<4' ninja
if [[ ! -d "$cache/sfizz/.git" ]]; then
 git clone --filter=blob:none --no-checkout https://github.com/sfztools/sfizz.git "$cache/sfizz"
fi
git -C "$cache/sfizz" checkout f5c6e29f23b8057867c08e88f5f6ac6738baa30b
git -C "$cache/sfizz" submodule update --init --depth 1 --jobs 4
PYTHONPATH="$cache/tools" "$cache/tools/bin/cmake" -S "$cache/sfizz" -B "$cache/sfizz/build" -DCMAKE_BUILD_TYPE=Release -DSFIZZ_JACK=OFF -DSFIZZ_RENDER=ON -DSFIZZ_SHARED=ON -DENABLE_LTO=OFF -DSFIZZ_GIT_SUBMODULE_CHECK=OFF
PYTHONPATH="$cache/tools" "$cache/tools/bin/cmake" --build "$cache/sfizz/build" -j 4
