from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in stronger_custom/__init__.py
from stronger_custom import __version__ as version

setup(
	name="stronger_custom",
	version=version,
	description="Factory custom",
	author="houssam",
	author_email="eng.houssam.sawan@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
