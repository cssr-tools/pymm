======
Online 
======

In this example we consider a micromodel available online in Fig. 2a in 
`Joekar-Niasar et al. 2009 <https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2007WR006641>`_.

The image was extracted by screenshot and saved with the name 'online.png' (1068x1068 pixels).
The configuration file was saved as 'configuration.toml' and contained the following text:

.. code-block:: python
    :linenos:

    #Set the pymm parameters
    lenght = 600e-6       #Image-related, length of the microsystem [m]
    width = 600e-6        #Image-related, height of the microsystem [m]
    tickness = 1.8e-6     #Image-related, depth of the microsystem [m]
    grainMeaning = 1      #Image-related, 0 if the grains in the image are light colors (e.g., white) or 1 for dark colors (e.g., black)
    threshold = 0.5       #Image-related, threshold for converting the image to binary
    rescale = 1           #Image-related, rescaled factor for the input image
    grainsSize = 50       #Image-related, minimum size of the grain clusters
    borderTol = 1         #Image-related, tolerance to approximate the border as polygon
    grainsTol = 1         #Image-related, tolerance to approximate the grains as polygon
    lineWidth = 1         #Figure-related, line width to show the contours in the produced figures
    channelWidth = 6e-6   #Device-related, width of the top and bottom channels in the micromodel device [m]
    meshSize = 1e-6       #Mesh-related, mesh size [m]
    viscocity = 1e-6      #Fluid-related, kinematic viscosity [dynamic viscosity/fluid_density, m2/s]
    diffusion = 1e-12     #Fluid-related, diffusion coefficient for tracer [m2/s]
    inletLocation = "top" #Simulation-related, inlet bc location (left, top, right, or bottom)
    inletValue = 2.0e-3   #Simulation-related, inlet boundary condition (pressure/fluid_density, [Pa/(kg/m3)])
    tracerTime = 120      #Simulation-related, end time for the tracer simulation [s]
    tracerWrite = 1       #Simulation-related, time interval to write the tracer results [s]
    pressureConv = 1e-7   #Solver-related, convergence criterium for the pressure solution in the numerical scheme for the Stokes simulation
    velocityConv = 1e-8   #Solver-related, convergence criterium for the velocity solution in the numerical scheme for the Stokes simulation
    iterationsMax = 10000 #Solver-related, maximum number of iterations for the Stokes simulation in case the convergence criteria have not been reached
    tracerStep = 1        #Solver-related, time step in the numerical scheme for the tracer simulation [s]

Here we used a version of Gmsh built from source, then we gave the path to the executable via the '-g' flag.
Since we are interested in the flow and tracer simulations, then we add the flag '-t all'.
Then, the following command was exectued in the terminal:

.. code-block:: bash

    pymm -i online.png -p configuration.toml -m device -t all -gmsh /home/AD.NORCERESEARCH.NO/dmar/Github/gmsh/build/gmsh

The execution time was ca. 15 minutes and the following are screenshots of the simulation results:

.. figure:: figs/online_pressure.png
.. figure:: figs/online_velocity.png
.. figure:: figs/online_tracer.png

    Simulation results of the (top) pressure, (middle) velocity, and (bottom) tracer concentration.