[![Build Status](https://github.com/daavid00/pymm/actions/workflows/CI.yml/badge.svg)](https://github.com/daavid00/pymm/actions/workflows/CI.yml)
<a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.8%20|%203.9%20|%203.10-blue.svg"></a>
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# pymm: An open-source image-based framework for CFD in microsystems 

<img src="docsrc/_static/pymm.gif" width="830" height="700">

This repository provides a workflow to perform computational fluid dynamics (CFD) simulations in microsystems. Given an image of a microsystem and an input text file with few parameters, then the _pymm_ executable process the image and builds the grid using [_Gmsh_](https://gmsh.info) and runs the CFD simulations using [_OpenFOAM_](https://www.openfoam.com).

## Installation
You will first need to install
* OpenFOAM (https://www.openfoam.com) (tested with OpenFOAM v2206)
* Gmsh (https://gmsh.info) (tested with Gmsh 4.11.0) 

You will also need to install some python packages, see ```requirements.txt``` for a complete list. You can install all the required python packages in a virtual environment with the following commands:

```bash
# Clone the repo
git clone https://github.com/daavid00/pymm.git
# Get inside the folder
cd pymm
# Create virtual environment
python3 -m venv vpymm
# Activate virtual environment
source vpymm/bin/activate
# Upgrade pip, setuptools, and wheel
pip install --upgrade pip setuptools wheel
# Install the pymm package
pip install .
```

## Running pymm
You can run _pymm_ as a single command line:
```
pymm -i some_input_image.png -p some_input_parameters.txt -o some_output_folder
```
Run `pymm --help` to see all possible command line argument options. Inside the `some_input_parameters.txt` file you provide the framework parameters such as the dimensions of the microsystem, mesh size, inlet pressure, and more. See the .txt files in the examples folder.

## Getting started
See the [_documentation_](https://daavid00.github.io/pymm/introduction.html).

## Examples
All the numerical simulations included in the below publication can be found in the examples folder. 

## Citing
If you use _pymm_ in your research, please cite the following publication: 

Liu, N., Haugen, M., Benali, B., Landa-Marbán, D., Fernø, M.A., Pore-scale spatiotemporal dynamics of microbial-induced calcium carbonate growth and distribution in porous media. Submitted.
