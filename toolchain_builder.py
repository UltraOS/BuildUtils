import platform
import subprocess
import shutil
import os
import contextlib
import urllib.request
from .package_manager import install_dependencies, Brew
from .toolchain_dependencies import get_dependencies_for_toolchain


class ToolchainParams:
    def __init__(
        self, type: str, target_arch: str, target_platform: str,
        root_dir: str, tune_for_native: bool, skip_dependencies: bool,
        sources_dir: str, keep_sources: bool, keep_build: bool
    ):
        self.type = type
        self.target_arch = target_arch
        self.target_platform = target_platform
        self.root_dir = root_dir
        self.tune_for_native = tune_for_native
        self.skip_dependencies = skip_dependencies
        self.sources_dir = sources_dir
        self.keep_sources = keep_sources
        self.keep_build = keep_build


GCC_VERSION = "13.2.0"
BINUTILS_VERSION = "2.41"

SUPPORTED_SYSTEMS = ["Linux", "Darwin"]


def is_supported_system() -> bool:
    this_platform = platform.system()
    ret = this_platform in SUPPORTED_SYSTEMS

    if not ret:
        print(f"Unsupported system '{this_platform}'")

    return ret


def _ensure_dependencies(params: ToolchainParams) -> None:
    if params.skip_dependencies:
        return

    deps = get_dependencies_for_toolchain(params.type)
    install_dependencies(deps)


def _clone_mingw_w64(target_dir: str) -> None:
    if os.path.exists(target_dir):
        print("mingw-w64 already cloned, skipping")
        return

    print("Downloading mingw-w64...")
    subprocess.run(["git", "clone", "https://github.com/mingw-w64/mingw-w64",
                    target_dir], check=True)


def _install_mingw_headers(
    source_dir: str, platform_dir: str, target_dir: str, env: dict
) -> None:
    mingw_headers_dir = os.path.join(target_dir, "mingw_headers")
    os.makedirs(mingw_headers_dir, exist_ok=True)
    configure_path = os.path.join(source_dir, "mingw-w64-headers", "configure")

    print("Installing mingw headers...")
    subprocess.run([configure_path, f"--prefix={platform_dir}"],
                   check=True, cwd=mingw_headers_dir, env=env)
    subprocess.run(["make", "install"], cwd=mingw_headers_dir,
                   check=True, env=env)

    shutil.rmtree(mingw_headers_dir)


def _install_mingw_libs(
    source_dir: str, target: str, platform_dir: str,
    target_dir: str, env: dict
) -> None:
    mingw_crt_dir = os.path.join(target_dir, "mingw_crt")
    os.makedirs(mingw_crt_dir, exist_ok=True)
    configure_path = os.path.join(source_dir, "mingw-w64-crt", "configure")

    print("Compiling mingw crt...")
    subprocess.run([configure_path,
                    f"--prefix={platform_dir}",
                    f"--host={target}",
                    f"--with-sysroot={platform_dir}",
                    "--enable-lib64", "--disable-lib32"],
                   cwd=mingw_crt_dir, check=True, env=env)
    subprocess.run(["make", "-j{}".format(os.cpu_count())], cwd=mingw_crt_dir,
                   check=True, env=env)
    subprocess.run(["make", "install"], cwd=mingw_crt_dir, check=True, env=env)

    shutil.rmtree(mingw_crt_dir)


def _build_binutils(
    binutils_sources: str, binutils_target_dir: str, target: str,
    platform_root: str, env: dict
) -> None:
    configure_full_path = os.path.join(binutils_sources, "configure")

    print("Building binutils...")
    subprocess.run([configure_full_path,
                    f"--target={target}",
                    f"--prefix={platform_root}",
                    "--with-sysroot"
                    "--disable-nls",
                    "--disable-multilib",
                    "--disable-werror"],
                   cwd=binutils_target_dir, env=env, check=True)
    subprocess.run(["make", "-j{}".format(os.cpu_count())], env=env,
                   cwd=binutils_target_dir, check=True)
    subprocess.run(["make", "install"], cwd=binutils_target_dir, check=True)


def _is_gcc_toolchain_built(tc_root: str, prefix: str) -> bool:
    full_path = os.path.join(tc_root, "bin", f"{prefix}-")

    # TODO: a more "reliable" check?
    return (os.path.isfile(full_path + "gcc") and
            os.path.isfile(full_path + "ld"))


def _get_gcc_prefix(params: ToolchainParams) -> str:
    arch_to_prefix = {
        "x86_64": "x86_64-{platform}",
        "i686": "i686-{platform}",
        "arm": "arm-{platform}",
        "aarch32": "arm-{platform}",
        "aarch64": "aarch64-{platform}",
    }

    prefix_template = arch_to_prefix[params.target_arch]
    return prefix_template.format(platform=params.target_platform)


def _download_and_extract(
    url: str, target_file: str, target_dir: str, platform: str
) -> bool:
    if os.path.exists(target_dir):
        print(f"{target_dir} already exists")
        return False

    if not os.path.exists(target_file):
        print(f"Downloading {url}...")
        urllib.request.urlretrieve(url, target_file)
    else:
        print(f"{target_file} already exists, not downloading")

    os.mkdir(target_dir)

    command = ["tar", "-xf", target_file, "-C", target_dir,
               "--strip-components", "1"]
    if platform != "Darwin":
        command.append("--checkpoint=.250")

    print(f"Unpacking {target_file}...")
    subprocess.run(command, check=True)

    # line feed after tar printing '....' for progress
    print("")
    return True


def _download_gcc_toolchain_sources(
    platform: str, workdir: str, gcc_target_dir: str,
    binutils_target_dir: str
) -> None:
    gcc_url = f"ftp://ftp.gnu.org/gnu/gcc/gcc-{GCC_VERSION}/"
    gcc_url += f"gcc-{GCC_VERSION}.tar.gz"

    binutils_url = "https://ftp.gnu.org/gnu/binutils/"
    binutils_url += f"binutils-{BINUTILS_VERSION}.tar.gz"

    full_gcc_tarball_path = os.path.join(workdir, "gcc.tar.gz")
    full_binutils_tarball_path = os.path.join(workdir, "binutils.tar.gz")

    _download_and_extract(gcc_url, full_gcc_tarball_path,
                          gcc_target_dir, platform)
    with contextlib.suppress(FileNotFoundError):
        os.remove(full_gcc_tarball_path)

    _download_and_extract(binutils_url, full_binutils_tarball_path,
                          binutils_target_dir, platform)
    with contextlib.suppress(FileNotFoundError):
        os.remove(full_binutils_tarball_path)


def _build_gcc(
    gcc_sources: str, gcc_target_dir: str, this_platform: str,
    target_platform: str, platform_root: str, env: dict
) -> None:
    configure_full_path = os.path.join(gcc_sources, "configure")

    configure_command = [configure_full_path,
                         f"--target={target_platform}",
                         f"--prefix={platform_root}",
                         "--disable-nls",
                         "--enable-languages=c,c++",
                         "--disable-multilib"]

    if this_platform == "Darwin":
        configure_command.extend([
            f"--with-gmp={Brew.prefix('gmp')}",
            f"--with-mpc={Brew.prefix('libmpc')}",
            f"--with-mpfr={Brew.prefix('mpfr')}"
        ])

    print("Building GCC...")
    subprocess.run(configure_command, cwd=gcc_target_dir, env=env, check=True)
    subprocess.run(["make", "all-gcc", "-j{}".format(os.cpu_count())],
                   cwd=gcc_target_dir, env=env, check=True)
    subprocess.run(["make", "install-gcc"], cwd=gcc_target_dir,
                   env=env, check=True)


def _build_libgcc(gcc_dir: str) -> None:
    subprocess.run(["make", "all-target-libgcc",
                    "-j{}".format(os.cpu_count())],
                   cwd=gcc_dir, check=True)
    subprocess.run(["make", "install-target-libgcc"], cwd=gcc_dir, check=True)


def _build_gcc_toolchain(
    params: ToolchainParams, gcc_sources: str,
    binutils_sources: str, this_platform: str
) -> None:
    compiler_prefix = _get_gcc_prefix(params)
    binutils_build_dir = os.path.join(params.root_dir,
                                      f"binutils-{params.target_arch}-build")
    gcc_build_dir = os.path.join(params.root_dir,
                                 f"gcc-{params.target_arch}-build")

    is_mingw = "mingw" in params.target_platform

    if is_mingw:
        mingw_w64_dir = os.path.join(params.root_dir, "mingw-w64")
        mingw_target_dir = os.path.join(params.root_dir, compiler_prefix)
        os.makedirs(mingw_target_dir, exist_ok=True)
        _clone_mingw_w64(mingw_w64_dir)

    env = os.environ.copy()

    cflags = ["-g", "-O2"]

    if params.tune_for_native:
        # -march=native doesn't work on MacOS clang for some reason
        if this_platform == "Darwin":
            cflags.append("-mtune=native")
        else:
            cflags.append("-march=native")

    env["CFLAGS"] = env.get("CFLAGS", "") + " ".join(cflags)
    env["CXXFLAGS"] = env.get("CXXFLAGS", "") + " ".join(cflags)

    bin_dir = os.path.join(params.root_dir, "bin")
    env["PATH"] = bin_dir + ":" + env.get("PATH", "")

    print(f"Building the GCC toolchain for {params.target_arch} "
          f"({compiler_prefix})...")

    os.makedirs(binutils_build_dir, exist_ok=True)
    _build_binutils(binutils_sources, binutils_build_dir, compiler_prefix,
                    params.root_dir, env)

    if is_mingw:
        _install_mingw_headers(mingw_w64_dir, mingw_target_dir,
                               params.root_dir, env)

    os.makedirs(gcc_build_dir, exist_ok=True)
    _build_gcc(gcc_sources, gcc_build_dir, this_platform, compiler_prefix,
               params.root_dir, env)

    if is_mingw:
        _install_mingw_libs(mingw_w64_dir, compiler_prefix, mingw_target_dir,
                            params.root_dir, env)

    _build_libgcc(gcc_build_dir)

    print(f"Toolchain for {params.target_arch} built succesfully!")

    if not params.keep_sources and is_mingw:
        shutil.rmtree(mingw_w64_dir)

    if not params.keep_build:
        print("Removing build directories...")
        shutil.rmtree(binutils_build_dir)
        shutil.rmtree(gcc_build_dir)


def _ensure_gcc_toolchain(params: ToolchainParams) -> None:
    if _is_gcc_toolchain_built(params.root_dir, _get_gcc_prefix(params)):
        print(f"Toolchain for {params.target_arch} is already built")
        return

    os.makedirs(params.root_dir, exist_ok=True)

    _ensure_dependencies(params)

    gcc_dir = "gcc_sources"
    binutils_dir = "binutils_sources"
    gcc_dir_full_path = os.path.join(params.sources_dir, gcc_dir)
    binutils_dir_full_path = os.path.join(params.sources_dir, binutils_dir)

    native_platform = platform.system()
    _download_gcc_toolchain_sources(native_platform, params.sources_dir,
                                    gcc_dir_full_path, binutils_dir_full_path)

    os.makedirs(params.root_dir, exist_ok=True)
    _build_gcc_toolchain(params, gcc_dir_full_path, binutils_dir_full_path,
                         native_platform)

    if not params.keep_sources:
        print("Removing source directories...")
        shutil.rmtree(gcc_dir_full_path)
        shutil.rmtree(binutils_dir_full_path)

    print("Successfully built GCC toolchain!")


def _ensure_clang_toolchain(params: ToolchainParams) -> None:
    _ensure_dependencies(params)


def build_toolchain(params: ToolchainParams) -> None:
    if params.type == "gcc":
        _ensure_gcc_toolchain(params)
    else:
        _ensure_clang_toolchain(params)
