[![Build Status](https://github.com/cssr-tools/pymm/actions/workflows/CI.yml/badge.svg)](https://github.com/cssr-tools/pymm/actions/workflows/CI.yml)
<a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12-blue.svg"></a>
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8430989.svg)](https://doi.org/10.5281/zenodo.8430989)

# pymm: An open-source image-based framework for CFD in microsystems 

<img src="docs/text/figs/pymm.gif" width="830" height="700">

## Main feature
Creation of [_OpenFOAM_](https://www.openfoam.com) simulation models from given input images using [_Gmsh_](https://gmsh.info).

## Installation
You will first need to install
* OpenFOAM (https://www.openfoam.com) (tested with OpenFOAM-12)
* Gmsh (https://gmsh.info) (tested with Gmsh 4.13.1)

To install the _pymm_ executable from the development version: 

```bash
pip install git+https://github.com/cssr-tools/pymm.git
```

If you are interested in a specific version (e.g., v2024.10) or in modifying the source code, then you can clone the repository and install the Python requirements in a virtual environment with the following commands:

```bash
# Clone the repo
git clone https://github.com/cssr-tools/pymm.git
# Get inside the folder
cd pymm
# For a specific version (e.g., v2024.10), or skip this step (i.e., edge version)
git checkout v2024.10
# Create virtual environment (to specific Python, python3.12 -m venv vpycopm)
python3 -m venv vpymm
# Activate virtual environment
source vpymm/bin/activate
# Upgrade pip, setuptools, and wheel
pip install --upgrade pip setuptools wheel
# Install the pymm package
pip install -e .
# For contributions/testing/linting, install the dev-requirements
pip install -r dev-requirements.txt
```

See the [_OpenFOAM page_](https://openfoam.org/download/12-ubuntu/), where from OpenFOAM-12 the simulator is available via apt get. 

## Running pymm
You can run _pymm_ as a single command line:
```
pymm -i input_image.png -p input_parameters.toml -o output_folder
```
Run `pymm --help` to see all possible command line argument options. Inside the `input_parameters.toml` file you provide the framework parameters such as the dimensions of the microsystem, mesh size, inlet pressure, and more. See the .toml files in the [_examples_](https://github.com/cssr-tools/pymm/tree/main/examples) and [_tests_](https://github.com/cssr-tools/pymm/tree/main/tests/configs) folders.

## Getting started
See the [_examples_](https://cssr-tools.github.io/pymm/examples.html) in the [_documentation_](https://cssr-tools.github.io/pymm/introduction.html).

## Citing
* Landa-Marbán, D. 2023. An open-source image-based framework for CFD in microsystems. https://doi.org/10.5281/zenodo.8430988.

## Journal papers using pymm
The following is a list of journal papers in which _pymm_ is used:

1. Liu, N., Haugen, M., Benali, B., Landa-Marbán, D., Fernø, M.A., 2023. Pore-scale spatiotemporal dynamics of microbial-induced calcium carbonate growth and distribution in porous media.  Int. J. Greenh. Gas Control 125, 103885. https://doi.org/10.1016/j.ijggc.2023.103885
1. Liu, N., Haugen, M., Benali, B., Landa-Marbán, D., Fernø, M.A., 2023. Pore-scale kinetics of calcium dissolution and secondary precipitation during geological carbon storage. Chem. Geol. 641, 121782. https://doi.org/10.1016/j.chemgeo.2023.121782.

## About pymm
_pymm_, an image-based Python package for computational fluid dynamics, is funded by [_Center for Sustainable Subsurface Resources_](https://cssr.no) [project no. 331841] and [_NORCE Norwegian Research Centre As_](https://www.norceresearch.no) [project number 101070]. 
Contributions are more than welcome using the fork and pull request approach.
For a new feature, please request this by raising an issue.