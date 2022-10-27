============
Introduction
============

.. image:: ./_static/pymm.gif

This documentation describes the content of the **pymm** package.
This package relies on python packages (e.g., `porespy <https://porespy.org>`_ and 
`skimage <https://scikit-image.org>`_) to generate the spatial domains for the simulations from
the microsystem images, and `Gmsh <https://gmsh.info>`_ as a mesh generator. 
The numerical simulations for the water flow and tracer are performed using 
the `OpenFOAM <https://www.openfoam.com>`_ simulator. This framework could be applied to general images and 
the current implementation could be ('easily') extended to consider further 
geometry of devices and solvers in OpenFOAM.

Overview
--------

The current implementation supports the following executable with the argument options:

.. code-block:: bash

    pymm -i image.png -p configuration_file.txt -o output -m image -t all -g gmsh

where 

- \-i, \-image: The base name of the image ('microsystem.png' by default).
- \-p, \-parameters: The base name of the :doc:`configuration file <./configuration_file>` ('parameters.txt' by default).
- \-m, \-mode: The configuration of the microsystem, currently only image and device supported ('image' by default).
- \-t, \-type: Run the whole framework ('all'), only the mesh part ('mesh'), keep the current mesh and only the flow ('flow'), flow and tracer ('flowntracer'), or only tracer ('tracer') ('mesh' by default).
- \-o, \-output: The base name of the :doc:`output folder <./output_folder>` ('output' by default).
- \-g, \-gmsh: The full path to the Gmsh executable or simple 'gmsh' if it runs from the terminal ('gmsh' by default).

Installation
------------

See the `Github page <https://github.com/daavid00/pymm>`_.