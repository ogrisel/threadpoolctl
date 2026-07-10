/*
 * Variants of the libomp/libiomp reproducer.
 * Usage: ./libomp_libiomp_variants [llvm-first|intel-first|load-only]
 */
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef int (*omp_get_max_threads_fn)(void);

static int call_llvm_first(void) {
    void *libomp = dlopen("libomp.so", RTLD_NOW | RTLD_GLOBAL);
    void *libiomp = dlopen("libiomp5.so", RTLD_NOW | RTLD_GLOBAL);
    if (!libomp || !libiomp) return 1;
    omp_get_max_threads_fn f_llvm = (omp_get_max_threads_fn)dlsym(libomp, "omp_get_max_threads");
    omp_get_max_threads_fn f_intel = (omp_get_max_threads_fn)dlsym(libiomp, "omp_get_max_threads");
    printf("llvm=%d\n", f_llvm());
    fflush(stdout);
    printf("intel=%d\n", f_intel());
    fflush(stdout);
    return 0;
}

static int call_intel_first(void) {
    void *libomp = dlopen("libomp.so", RTLD_NOW | RTLD_GLOBAL);
    void *libiomp = dlopen("libiomp5.so", RTLD_NOW | RTLD_GLOBAL);
    if (!libomp || !libiomp) return 1;
    omp_get_max_threads_fn f_llvm = (omp_get_max_threads_fn)dlsym(libomp, "omp_get_max_threads");
    omp_get_max_threads_fn f_intel = (omp_get_max_threads_fn)dlsym(libiomp, "omp_get_max_threads");
    printf("intel=%d\n", f_intel());
    fflush(stdout);
    printf("llvm=%d\n", f_llvm());
    fflush(stdout);
    return 0;
}

static int load_only(void) {
    void *libomp = dlopen("libomp.so", RTLD_NOW | RTLD_GLOBAL);
    void *libiomp = dlopen("libiomp5.so", RTLD_NOW | RTLD_GLOBAL);
    if (!libomp || !libiomp) return 1;
    printf("loaded both\n");
    fflush(stdout);
    return 0;
}

int main(int argc, char **argv) {
    const char *mode = argc > 1 ? argv[1] : "llvm-first";
    if (strcmp(mode, "llvm-first") == 0) return call_llvm_first();
    if (strcmp(mode, "intel-first") == 0) return call_intel_first();
    if (strcmp(mode, "load-only") == 0) return load_only();
    fprintf(stderr, "unknown mode %s\n", mode);
    return 2;
}
