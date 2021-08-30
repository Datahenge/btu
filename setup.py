from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in btu/__init__.py
from btu import __version__ as version

setup(
	name="btu",
	version=version,
	description="Background Tasks Unleashed",
	author="Datahenge LLC",
	author_email="brian@datahenge.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
