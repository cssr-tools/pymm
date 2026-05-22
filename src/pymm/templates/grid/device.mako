// SPDX-FileCopyrightText: 2022-2026 NORCE Research AS
// SPDX-License-Identifier: GPL-3.0

w=1.0;
L=${imL}-1.0;
H=${imH}-1.0;

rL=${length}; 
rH=${width};  
rd=${thickness};
rc=${channelWidth};

hs = ${meshSize};
Mesh.MeshSizeFromPoints = 0;
Mesh.MeshSizeFromCurvature = 0;
Mesh.MeshSizeExtendFromBoundary = 0;
Mesh.MeshSizeMax = hs;
hb = hs;

Point(1) = {-2*rc, -rc-rc, 0, hs};
Point(2) = {0, 0, 0, hs};

Tp[] = Point "*";
cL = #Tp[]-1;
${point_left_lines}

Tp[] = Point "*";
Point(#Tp[]+1) = {0, rH, 0, hs};
Point(#Tp[]+2) = {-2*rc, rH+rc+rc, 0, hs};

Tp[] = Point "*";
nLl = #Tp[]-1;
Point(#Tp[]+1) = {-rc, rH+rc+2*rc, 0, hs};

Tp[] = Point "*";
cT = #Tp[]-1;
Point(#Tp[]+1) = {rc, rH+rc, 0, hs};
Point(#Tp[]+2) = {rL-rc, rH+rc, 0, hs};
Point(#Tp[]+3) = {rL+rc, rH+rc+2*rc, 0, hs};

Tp[] = Point "*";
nLlt = #Tp[]-1;
Point(#Tp[]+1) = {rL+2*rc, rH+rc+rc, 0, hs};

Tp[] = Point "*";
cR = #Tp[]-1;
Point(#Tp[]+1) = {rL, rH, 0, hs};

Tp[] = Point "*";
${point_right_lines}

Tp[] = Point "*";
Point(#Tp[]+1) = {rL, 0, 0, hs};
Point(#Tp[]+2) = {rL+2*(rc), -rc-(rc), 0, hs};

Tp[] = Point "*";
nLltr = #Tp[]-1;
Point(#Tp[]+1) = {rL+rc, -rc-2*(rc), 0, hs};

Tp[] = Point "*";
cB = #Tp[]-1;
Point(#Tp[]+1) = {rL-rc, -rc, 0, hs};
Point(#Tp[]+2) = {rc, -rc, 0, hs};
Point(#Tp[]+3) = {-rc, -rc-2*rc, 0, hs};

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
Physical Surface("inlet") = {out[1+c${inlet}]};
Physical Surface("outlet") = {out[1+c${outlet}]}; 

Mesh.MshFileVersion=2.2;
Mesh 3;
