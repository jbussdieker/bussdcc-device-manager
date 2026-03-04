from importlib.metadata import PackageNotFoundError, version

PACKAGE_NAME = "bussdcc-device-manager"


def get_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "0.0.0"


__name__ = PACKAGE_NAME
__version__ = get_version()
