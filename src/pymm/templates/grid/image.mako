w=1.0;
L=${imL}-1.0;
H=${imH}-1.0;

rL=${Ls}; 
rH=${Hs};  
rd=${Ds};

hs = ${hz};
Mesh.MeshSizeFromPoints = 0;
Mesh.MeshSizeFromCurvature = 0;
Mesh.MeshSizeExtendFromBoundary = 0;
Mesh.MeshSizeMax = hs;
hb = hs;

Point(1) = {0, 0, 0, hs};
Tp[] = Point "*";
% for i in range(len(pl)):
Point(#Tp[]+${i+1}) = {${pl[len(pl)-1-i][0]-0.5}*rL/L, ${pl[len(pl)-1-i][1]-0.5}*rH/H, 0, hb};
% endfor
Tp[] = Point "*";
Point(#Tp[]+1) = {0, rH, 0, hs};
Tp[] = Point "*";
% for i in range(len(pb)-1):
Point(#Tp[]+${i+1}) = {${pb[len(pb)-1-i][0]+0.5}*rL/L, ${pb[len(pb)-1-i][1]-0.5}*rH/H, 0, hb};
% endfor
Tp[] = Point "*";
Point(#Tp[]+1) = {rL, rH, 0, hs};
Tp[] = Point "*";
% for i in range(len(pr)-1):
Point(#Tp[]+${i+1}) = {${pr[len(pr)-1-i][0]+0.5}*rL/L, ${pr[len(pr)-1-i][1]-0.5}*rH/H, 0, hb};
% endfor
Tp[] = Point "*";
Point(#Tp[]+1) = {rL, 0, 0, hs};
Tp[] = Point "*";
% for i in range(len(pt)-2):
Point(#Tp[]+${i+1}) = {${pt[len(pt)-1-i][0]+0.5}*rL/L, ${pt[len(pt)-1-i][1]-1.5}*rH/H, 0, hb};
% endfor
Tp[] = Point "*";

For i In {1 : #Tp[] - 1}
  Line(i)={i, i + 1};
EndFor
Line(#Tp[])={#Tp[], 1};
Line Loop(1)={1: #Tp[]};
nLT = #Tp[];
n = 0;

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
% for i in range(len(bdnL)):
bdnL[] += {out[${bdnL[i]+2}]};
% endfor
% for i in range(len(bdnT)):
bdnT[] += {out[${bdnT[i]+2}]};
% endfor
% for i in range(len(bdnR)):
bdnR[] += {out[${bdnR[i]+2}]};
% endfor
% for i in range(len(bdnB)):
bdnB[] += {out[${bdnB[i]+2}]};
% endfor
% for i in range(len(wall)-1):
bdnW[] += {out[${wall[i]+2}]};
% endfor

//Physical Surface("left") = bdnL[];
Physical Surface("inlet") = bdnT[];
//Physical Surface("right") = bdnR[];
Physical Surface("outlet") = bdnB[];
//Physical Surface("wall") = bdnW[];

Mesh.MshFileVersion=2.2;
Mesh 3;