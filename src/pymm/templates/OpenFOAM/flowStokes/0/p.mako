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
    class       volScalarField;
    object      p;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform 0;

boundaryField
{
    abovenbelow
    {
        type            empty;
    }
    inlet
    {
        type            fixedValue;
        value           uniform ${dic['bc_inlet']};   
    }
    outlet
    {
        type            fixedValue;
        value           uniform 0;   
    }
    defaultFaces
    {
        type            zeroGradient;
    }
}


// ************************************************************************* //
