from setuptools import find_packages, setup

with open("README.md") as f:
    long_description = f.read()

with open("requirements.txt") as f:
    install_requires = f.read().splitlines()

setup(
    name="pymm",
    version="0.0.1",
    install_requires=install_requires,
    setup_requires=["setuptools_scm"],
    python_requires=">=3.8",
    description="Open-source image-based workflow for CFD simulations in microsystems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dmar/pymm",
    author="David Landa-Marbán",
    author_email="dmar@norceresearch.no",
    package_dir={"": "src"},
    packages=find_packages("src"),
    entry_points={
        "console_scripts": [
            "pymm=pymm.core.pymm:main",
        ]
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
