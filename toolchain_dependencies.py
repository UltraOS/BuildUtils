PACKAGE_MANAGER_TO_DEPS = {
    "gcc": {
        "apt": [
            "build-essential",
            "bison",
            "flex",
            "libgmp-dev",
            "libmpc-dev",
            "libmpfr-dev",
            "texinfo",
            "libisl-dev",
        ],
        "pacman": [
            "base-devel",
            "gmp",
            "libmpc",
            "mpfr",
        ],
        "dnf": [
            "gcc",
            "gcc-c++",
            "make",
            "bison",
            "flex",
            "gmp-devel",
            "libmpc-devel",
            "mpfr-devel",
            "texinfo",
            "isl-devel",
        ],
        "brew": [
            "coreutils",
            "bison",
            "flex",
            "gmp",
            "libmpc",
            "mpfr",
            "texinfo",
            "isl",
        ]
    },
    "clang": {
        "apt": [
            "clang",
            "lld"
        ],
        "pacman": [
            "clang",
            "lld",
        ],
        "dnf": [
            "clang",
            "lld",
        ],
        "brew": [
            "llvm",
            "lld",
        ]
    },
}


def get_dependencies_for_toolchain(type: str) -> dict:
    return PACKAGE_MANAGER_TO_DEPS[type]
