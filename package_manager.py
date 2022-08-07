from abc import abstractmethod, ABC
import platform
import subprocess


def _command_exists(cmd):
    ret = subprocess.run(["command", "-v", cmd], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, shell=True)
    return ret.returncode == 0


class PackageManager(ABC):
    cached = None

    @staticmethod
    @abstractmethod
    def detect() -> bool:
        pass

    @staticmethod
    @abstractmethod
    def is_dep_installed(dep) -> bool:
        pass

    @abstractmethod
    def install_dep(dep):
        pass


class Apt(PackageManager):
    name = "apt"
    did_update = False

    @staticmethod
    def detect() -> bool:
        return _command_exists(Apt.name)

    @staticmethod
    def is_dep_installed(dep) -> bool:
        args = ["apt", "--installed", "list", dep, "-qq"]
        out = subprocess.check_output(args, stderr=subprocess.DEVNULL,
                                      text=True)

        # could be [installed] or [installed,...], maybe something else too?
        return "[installed" in out

    @staticmethod
    def install_dep(dep):
        if not Apt.did_update:
            subprocess.run(["sudo", "apt-get", "update"])
            Apt.did_update = True

        subprocess.run(["sudo", "apt-get", "install", "-y", dep], check=True)


class Pacman(PackageManager):
    name = "pacman"

    @staticmethod
    def detect() -> bool:
        return _command_exists(Pacman.name)

    @staticmethod
    def is_dep_installed(dep) -> bool:
        ret = subprocess.run(["pacman", "-Qs", dep],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        return ret.returncode == 0

    @staticmethod
    def install_dep(dep):
        subprocess.run(["sudo", "pacman", "-Sy", dep, "--noconfirm"],
                       check=True)


class Brew(PackageManager):
    name = "brew"

    @staticmethod
    def detect() -> bool:
        return _command_exists(Brew.name)

    @staticmethod
    def is_dep_installed(dep):
        ret = subprocess.run(["brew", "list", dep],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        return ret.returncode == 0

    @staticmethod
    def install_dep(dep):
        subprocess.run(["brew", "install", dep], check=True)


PACKAGE_MANAGERS = (
    Apt,
    Pacman,
    Brew,
)


def get_package_manager() -> PackageManager:
    if PackageManager.cached is not None:
        return PackageManager.cached

    system = platform.system()

    if system == "Darwin":
        PackageManager.cached = Brew
        return PackageManager.cached

    for pm in PACKAGE_MANAGERS:
        if pm.detect():
            print(f"Detected package manager {pm.name}")
            PackageManager.cached = pm
            break

    if PackageManager.cached is None:
        raise RuntimeError("Couldn't detect a supported package manager")

    return PackageManager.cached


def install_dependencies(deps):
    pm = get_package_manager()
    pm_deps = deps[pm.name]

    for dep in pm_deps:
        if pm.is_dep_installed(dep):
            print(f"{dep} is already installed")
            continue

        print(f"Installing {dep}...")
        pm.install_dep(dep)
