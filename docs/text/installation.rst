============
Installation
============

The following steps work installing the dependencies in Linux via apt-get.
While using package managers such as Anaconda, Miniforge, or Mamba might work, these are not tested.
The supported Python versions are 3.12 and 3.13. We will update the documentation when Python3.14 is supported
(e.g., the porespy Python package is not yet available via pip install in Python 3.14).

Python package
--------------

To install the **pymm** executable from the development version: 

.. code-block:: bash

    pip install git+https://github.com/cssr-tools/pymm.git

If you are interested in a specific version (e.g., v2025.10) or in modifying the source code, then you can clone the repository and 
install the Python requirements in a virtual environment with the following commands:

.. code-block:: console

    # Clone the repo
    git clone https://github.com/cssr-tools/pymm.git
    # Get inside the folder
    cd pymm
    # For a specific version (e.g., v2025.10), or skip this step (i.e., edge version)
    git checkout v2025.10
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

.. note::

    While with Python3.12 the previous lines should install all required Python packages with the correct versions, 
    using Python3.13 requires to install a higher version of scikit-image, this by executing **pip install scikit-image==0.25.2** after the previous lines.

.. tip::

    Typing **git tag -l** writes all available specific versions.

OpenFOAM
--------

See the `OpenFOAM page <https://openfoam.org/download/13-ubuntu/>`_, where from OpenFOAM-12 the simulator is available via apt get,
and OpenFOAM-13 is the latest release. To test if OpenFoam is installed and working, you could type in the terminal:

.. code-block:: console

    . /opt/openfoam13/etc/bashrc    
    foamRun -help

Gmsh
----

See the `Gmsh page <https://gmsh.info/#Download>`_.


.. tip::

    See the `CI.yml <https://github.com/cssr-tools/pymm/blob/main/.github/workflows/CI.yml>`_ script 
    for installation of pymm in Ubuntu using Python 3.13.
