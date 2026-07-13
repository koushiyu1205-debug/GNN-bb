# Lunar native SPPRC backend

This standalone CMake project pins `lab-core/rcspp` and supplies the lunar
multi-sortie resource, forward extension, conservative dominance, route
reconstruction and pybind API. It does not modify the upstream solver.

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
PROJECT_ROOT="$REPO_ROOT/GAT_BPC_moonTerk"
cd "$PROJECT_ROOT"

PY_SITE="$(python -c 'import sysconfig; print(sysconfig.get_path("platlib"))')"
cmake -S native/lunar_spprc \
      -B build/native-spprc \
      -G Ninja \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DPython_EXECUTABLE="$(command -v python)" \
      -Dpybind11_DIR="$(python -m pybind11 --cmakedir)" \
      -DLUNAR_SPPRC_PYTHON_INSTALL_DIR="$PY_SITE" \
      -DLUNAR_SPPRC_RCSPP_COMMIT=2f1d53ba6806844e30ce43ee9c41041a5a1b4e79

cmake --build build/native-spprc --parallel 4
ctest --test-dir build/native-spprc --output-on-failure
cmake --install build/native-spprc
python -c "import lunar_spprc_native; print(lunar_spprc_native.build_info())"
```

Only pull LFS objects when the pinned checkout actually contains them and
`git-lfs` is available:

```bash
RCSPP_SRC="$PROJECT_ROOT/build/native-spprc/_deps/rcspp-src"
if git -C "$RCSPP_SRC" lfs env >/dev/null 2>&1 &&
   test -n "$(git -C "$RCSPP_SRC" lfs ls-files)"; then
    git -C "$RCSPP_SRC" lfs pull
fi
```

The exact configuration disables upstream memory-pressure trimming. A hard
memory limit returns an incomplete status; it never drops labels and then
certifies. The native backend currently supports only empty branch and cut
contexts. Unsupported contexts explicitly fall back to the Python reference.
