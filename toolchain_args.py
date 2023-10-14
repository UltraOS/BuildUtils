from . import toolchain_builder as tb
import argparse
from typing import Optional


def add_base_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--toolchain", choices=["gcc", "clang"],
                        default="clang", help="toolchain to build")
    parser.add_argument(
        "--skip-toolchain-dependencies", action="store_true",
        help="don't attempt to fetch the toolchain dependencies")
    parser.add_argument(
        "--keep-toolchain-sources", action="store_true",
        help="don't remove the toolchain sources after build")
    parser.add_argument(
        "--keep-toolchain-build", action="store_true",
        help="don't remove the toolchain build directories")
    parser.add_argument(
        "--no-tune-native", action="store_true",
        help="don't optimize the toolchain for the current CPU")


def add_arch_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("arch", choices=["i686", "x86_64"],
                        help="architecture to build the toolchain for")


def params_from_args(
    args: argparse.Namespace, platform: str, tc_root: str,
    tc_sources_root: str, arch: Optional[str] = None
) -> tb.ToolchainParams:
    if arch is None and hasattr(args, "arch"):
        arch = args.arch
    assert arch

    return tb.ToolchainParams(
        args.toolchain, arch, platform,
        tc_root, not args.no_tune_native,
        args.skip_toolchain_dependencies,
        tc_sources_root,
        args.keep_toolchain_sources,
        args.keep_toolchain_build,
    )
