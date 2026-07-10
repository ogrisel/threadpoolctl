/*
 * Minimal reproducer for libomp/libiomp incompatibility (LLVM bug 43565).
 * Call OpenMP functions from libomp first, then from libiomp.
 */
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

typedef int (*omp_get_max_threads_fn)(void);
typedef int (*omp_get_num_threads_fn)(void);

int main(void) {
    void *libomp = dlopen("libomp.so", RTLD_NOW | RTLD_GLOBAL);
    void *libiomp = dlopen("libiomp5.so", RTLD_NOW | RTLD_GLOBAL);

    if (!libomp) {
        fprintf(stderr, "Failed to load libomp: %s\n", dlerror());
        return 1;
    }
    if (!libiomp) {
        fprintf(stderr, "Failed to load libiomp5: %s\n", dlerror());
        return 1;
    }

    omp_get_max_threads_fn omp_get_max_threads_llvm =
        (omp_get_max_threads_fn)dlsym(libomp, "omp_get_max_threads");
    omp_get_max_threads_fn omp_get_max_threads_intel =
        (omp_get_max_threads_fn)dlsym(libiomp, "omp_get_max_threads");

    if (!omp_get_max_threads_llvm || !omp_get_max_threads_intel) {
        fprintf(stderr, "Failed to resolve omp_get_max_threads symbols\n");
        return 1;
    }

    printf("Calling libomp omp_get_max_threads()...\n");
    fflush(stdout);
    int llvm_threads = omp_get_max_threads_llvm();
    printf("libomp returned %d\n", llvm_threads);
    fflush(stdout);

    printf("Calling libiomp omp_get_max_threads()...\n");
    fflush(stdout);
    int intel_threads = omp_get_max_threads_intel();
    printf("libiomp returned %d\n", intel_threads);
    fflush(stdout);

    printf("SUCCESS: both calls completed\n");
    return 0;
}
