=============
Output folder
=============

The following screenshot shows the generated files in the selected output folder after 
executing **pymm**.

.. figure:: figs/output.png

    Generated files after executing **pymm**.

The simulation results are saved in the VTK_flowSTokes and VTK_tracerTransport folders, and
`paraview <https://www.paraview.orgs>`_ is used for the visualization.
Then after running **pymm**, one could modify the generated OpenFOAM related files and 
run directly the simulations calling the OpenFOAM solvers, e.g., to change additional 
tolerances that are not currently included in the parameters.toml file and/or to change 
the numerical schemes (see the OpenFOAM documentation 
`here <https://www.openfoam.com/documentation/user-guide/6-solving/6.2-numerical-schemes>`_).
