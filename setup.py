"""pymm: An open-source image-based framework for CFD in microsystems"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf8") as file:
    long_description = file.read()

with open("requirements.txt", "r", encoding="utf8") as file:
    install_requires = file.read().splitlines()

with open("dev-requirements.txt", "r", encoding="utf8") as file:
    dev_requires = file.read().splitlines()

setup(
    name="pymm",
    version="0.0.1",
    install_requires=install_requires,
    extras_require={"dev": dev_requires},
    setup_requires=["setuptools_scm"],
    description="Open-source image-based workflow for CFD simulations in microsystems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dmar/pymm",
    author="David Landa-Marbán",
    mantainer="David Landa-Marbán",
    mantainer_email="dmar@norceresearch.no",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    keywords="openfoam navier-stokes gmsh cfd microsystems",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    license="GPL-3.0",
    python_requires=">=3.8, <4",
    entry_points={
        "console_scripts": [
            "pymm=pymm.core.pymm:main",
        ]
    },
    include_package_data=True,
)
