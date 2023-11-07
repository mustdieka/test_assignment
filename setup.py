from pathlib import Path

from setuptools import find_namespace_packages, setup

_HERE = Path(__file__).parent
_PATH_VERSION = _HERE / "power_plant_construction" / "version.py"

about: dict = {}
exec(_PATH_VERSION.read_text(), about)
long_description = Path(_HERE, "README.md").read_text()

setup(
    name=about["__title__"],
    version=about["__version__"],
    description=about["__description__"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="mustdieka",
    packages=find_namespace_packages(include=["power_plant_construction.*", "scripts.*"]),
    python_requires=">=3.11",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "db-migrate=power_plant_construction.manage:db_migrate",
            "start-api=power_plant_construction.manage:start_api",
            "start-app=power_plant_construction.manage:start_app",
            "bootstrap-knowledge-maps=power_plant_construction.manage:bootstrap_knowledge_maps",
        ]
    },
)
