/*--------------------------------*- C++ -*----------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Version:  12
     \\/     M anipulation  |
\*---------------------------------------------------------------------------*/
FoamFile
{
    format      ascii;
    class       dictionary;
    object      topoSetDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

actions
(
    {
        name    f0;
        type    faceSet;
        action  new;
        source  patchToFace;
        patch   inlet;
    }
    {
        name    c0;
        type    cellSet;
        action  new;
        source  faceToCell;
        option  any;
        set     f0;
    }

    {
        name    c0Zone;
        type    cellZoneSet;
        action  new;
        source  setToCellZone;
        set     c0;
    }

);


// ************************************************************************* //
