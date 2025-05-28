============
Installation
============

The following steps work installing the dependencies in Linux via apt-get.
While using package managers such as Anaconda, Miniforge, or Mamba might work, these are not tested.

Python package
--------------

To install the **pymm** executable from the development version: 

.. code-block:: bash

    pip install git+https://github.com/cssr-tools/pymm.git

If you are interested in a specific version (e.g., v2024.10) or in modifying the source code, then you can clone the repository and 
install the Python requirements in a virtual environment with the following commands:

.. code-block:: console

    # Clone the repo
    git clone https://github.com/cssr-tools/pymm.git
    # Get inside the folder
    cd pymm
    # For a specific version (e.g., v2024.10), or skip this step (i.e., edge version)
    git checkout v2024.10
    # Create virtual environment (to specific Python, python3.12 -m venv vpymm)
    python3 -m venv vpymm
    # Activate virtual environment
    source vpymm/bin/activate
    # Upgrade pip, setuptools, and wheel
    pip install --upgrade pip setuptools wheel
    # Install the pymm package
    pip install -e .
    # For contributions/testing/linting, install the dev-requirements
    pip install -r dev-requirements.txt

.. tip::

    Typing **git tag -l** writes all available specific versions.

OpenFOAM
--------

See the `OpenFOAM page <https://openfoam.org/download/12-ubuntu/>`_, where from OpenFOAM-12 the simulator is available via apt get.

Gmsh
----

See the `Gmsh page <https://gmsh.info/#Download>`_.


.. tip::

    See the `CI.yml <https://github.com/cssr-tools/pymm/blob/main/.github/workflows/CI.yml>`_ script 
    for installation of pymm in Ubuntu using Python3.13. Using Python3.13 requires to install a higher version
    of scikit-image by executing **pip install scikit-image==0.25.2**.
