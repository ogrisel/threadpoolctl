#!/usr/bin/env python3
"""Experiments to test libomp + libiomp compatibility on Linux."""

import json
import os
import subprocess
import sys
import time
import warnings

from threadpoolctl import ThreadpoolController, threadpool_info, threadpool_limits


def run_with_timeout(cmd, timeout=30):
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=os.environ.copy(),
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timed_out": True,
        }


def print_section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def library_versions(conda_prefix):
    info = {}
    for lib in ("libiomp5.so", "libomp.so"):
        path = os.path.join(conda_prefix, "lib", lib)
        if os.path.exists(path):
            info[lib] = path
    # system libomp from llvm apt
    for candidate in (
        "/usr/lib/llvm-18/lib/libomp.so",
        "/usr/lib/x86_64-linux-gnu/libomp.so",
    ):
        if os.path.exists(candidate):
            info["libomp.so (system)"] = candidate
    for name, path in info.items():
        try:
            out = subprocess.check_output(["strings", path], text=True, stderr=subprocess.DEVNULL)
            version_lines = [l for l in out.splitlines() if "OpenMP" in l or "version" in l.lower()][:5]
            print(f"{name}: {path}")
            for line in version_lines:
                print(f"  {line}")
        except Exception as exc:
            print(f"{name}: {path} (could not read: {exc})")
    return info


def main():
    print_section("Environment")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    conda_prefix = os.environ.get("CONDA_PREFIX", "")
    print(f"CONDA_PREFIX: {conda_prefix}")

    try:
        import numpy
        import scipy

        print(f"numpy: {numpy.__version__}")
        print(f"scipy: {scipy.__version__}")
    except ImportError as exc:
        print(f"numpy/scipy not available: {exc}")

    print_section("Library versions")
    library_versions(conda_prefix)

    print_section("Loaded OpenMP libraries (before imports)")
    # Import extensions and numpy to load both runtimes
    import tests._openmp_test_helper.openmp_helpers_outer  # noqa: F401
    import numpy.linalg  # noqa: F401

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        controller = ThreadpoolController()
        prefixes = [c.prefix for c in controller.lib_controllers]
        print("Prefixes:", prefixes)
        print("Info:")
        print(json.dumps(controller.info(), indent=2))
        print(f"Warnings raised: {len(caught)}")
        for w in caught:
            print(f"  {w.category.__name__}: {str(w.message)[:200]}")

    print_section("Experiment 1: nested OpenMP loops (outer=libomp, inner=libgomp)")
    from tests._openmp_test_helper.openmp_helpers_outer import check_nested_openmp_loops

    result = run_with_timeout(
        [
            sys.executable,
            "-c",
            "from tests._openmp_test_helper.openmp_helpers_outer import check_nested_openmp_loops; "
            "import numpy.linalg; "
            "print(check_nested_openmp_loops(100, 4))",
        ],
        timeout=15,
    )
    print(json.dumps(result, indent=2))

    print_section("Experiment 2: threadpoolctl get_num_threads after nested prange+BLAS")
    script = """
import numpy as np
from threadpoolctl import ThreadpoolController, threadpool_limits
from tests._openmp_test_helper.nested_prange_blas import check_nested_prange_blas

A = np.random.randn(64, 64)
B = np.random.randn(64, 64)
print("Running nested prange + BLAS...")
check_nested_prange_blas(A, B, 4)
print("Creating ThreadpoolController...")
controller = ThreadpoolController()
print("Calling get_original_num_threads...")
with threadpool_limits(limits=1) as ctx:
    print(ctx.get_original_num_threads())
print("SUCCESS")
"""
    result = run_with_timeout([sys.executable, "-c", script], timeout=30)
    print(json.dumps(result, indent=2))

    print_section("Experiment 3: repeated ThreadpoolController init + threadpool_limits")
    script = """
import numpy.linalg
from tests._openmp_test_helper.openmp_helpers_outer import check_nested_openmp_loops
from threadpoolctl import ThreadpoolController, threadpool_limits

for i in range(20):
    check_nested_openmp_loops(50, 2)
    controller = ThreadpoolController()
    with threadpool_limits(limits=1):
        controller.info()
print("SUCCESS after 20 iterations")
"""
    result = run_with_timeout([sys.executable, "-c", script], timeout=60)
    print(json.dumps(result, indent=2))

    print_section("Experiment 4: subprocess threadpool_info from inner module")
    result = run_with_timeout(
        [
            sys.executable,
            "-c",
            "import json; from threadpoolctl import threadpool_info; "
            "import tests._openmp_test_helper.openmp_helpers_inner; "
            "import numpy.linalg; "
            "print(json.dumps(threadpool_info()))",
        ],
        timeout=15,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
