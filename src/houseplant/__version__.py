VERSION = (0, 2, 5)
PRERELEASE = None  # alpha, beta or rc
REVISION = None


def generate_version(version, prerelease=None, revision=None):
    version_parts = [".".join(map(str, version))]
    if prerelease is not None:
        version_parts.append(f"-{prerelease}")
    if revision is not None:
        version_parts.append(f".{revision}")
    return "".join(version_parts)


__title__ = "houseplant"
__description__ = "Database Migrations for ClickHouse."
__url__ = "https://github.com/juneHQ/houseplant"
__version__ = generate_version(VERSION, prerelease=PRERELEASE, revision=REVISION)
__author__ = "June"
__author_email__ = "eng@june.so"
__license__ = "MIT License"
