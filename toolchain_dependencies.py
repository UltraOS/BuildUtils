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
        "brew": [
            "llvm"
        ]
    },
}


def get_dependencies_for_toolchain(type: str) -> dict:
    return PACKAGE_MANAGER_TO_DEPS[type]
