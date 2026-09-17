from . import toolchain_builder as tb
import argparse
from typing import Optional


# Add the toolchain arguments to a parser or to an argument group
# the caller made for them, the caller owns the help layout
def add_base_args(target: argparse._ActionsContainer) -> None:
    target.add_argument("--toolchain", choices=["gcc", "clang"],
                        default="clang", help="Toolchain to build")
    target.add_argument(
        "--skip-toolchain-dependencies", action="store_true",
        help="Don't attempt to fetch the toolchain dependencies")
    target.add_argument(
        "--keep-toolchain-sources", action="store_true",
        help="Don't remove the toolchain sources after build")
    target.add_argument(
        "--keep-toolchain-build", action="store_true",
        help="Don't remove the toolchain build directories")
    target.add_argument(
        "--no-tune-native", action="store_true",
        help="Don't optimize the toolchain for the current CPU")


def add_arch_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("arch",
                        choices=["i686", "x86_64", "aarch32", "aarch64"],
                        help="Architecture to build the toolchain for")


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
