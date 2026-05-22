// SPDX-FileCopyrightText: 2022-2026 NORCE Research AS
// SPDX-License-Identifier: GPL-3.0

w=1.0;
L=${imL}-1.0;
H=${imH}-1.0;

rL=${length}; 
rH=${width};  
rd=${thickness};

hs = ${meshSize};
Mesh.MeshSizeFromPoints = 0;
Mesh.MeshSizeFromCurvature = 0;
Mesh.MeshSizeExtendFromBoundary = 0;
Mesh.MeshSizeMax = hs;
hb = hs;

Tp[] = Point "*";
${point_lines}
Tp[] = Point "*";

For i In {1 : #Tp[] - 1}
  Line(i)={i, i + 1};
EndFor
Line(#Tp[])={#Tp[], 1};
Line Loop(1)={1: #Tp[]};
nLT = #Tp[];
n = 0;

${grain_lines}

Plane Surface(1)={1:1+n};

out[]=Extrude {0, 0, rd} {
  Surface{1};
  Layers{1};
  Recombine;
};

Physical Surface("abovenbelow") = {1,out[0]}; 
Physical Volume("internal") = {out[1]}; 

bdnL[] = {};
bdnT[] = {};
bdnR[] = {};
bdnB[] = {};
bdnW[] = {};

${bdn_lines}

Physical Surface("inlet") = bdn${inlet}[];
Physical Surface("outlet") = bdn${outlet}[];
//Physical Surface("wall") = bdnW[];

Mesh.MshFileVersion=2.2;
Mesh 3;
