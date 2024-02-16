/*--------------------------------*- C++ -*----------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Version:  11
     \\/     M anipulation  |
\*---------------------------------------------------------------------------*/
FoamFile
{
    format      ascii;
    class       dictionary;
    location    "system";
    object      controlDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

application     foamRun;

solver          functions;

subSolver       incompressibleFluid;

startFrom       latestTime;

startTime       0;

subSolverTime   0;

stopAt          endTime;

endTime         ${dic['t_et']};

deltaT          ${dic['t_dt']};

writeControl    runTime;

writeInterval   ${dic['t_wi']};

purgeWrite      0;

writeFormat     ascii;

writePrecision  6;

writeCompression off;

timeFormat      general;

timePrecision   6;

runTimeModifiable true;

functions
{
    #includeFunc scalarTransport(T, diffusivity=constant, D = ${dic['D']})
}

// ************************************************************************* //
