w=1.0;
L=${dic['imL']}-1.0;
H=${dic['imH']}-1.0;

rL=${dic['Ls']}; 
rH=${dic['Hs']};  
rd=${dic['Ds']};

hs = ${dic['hz']};
Mesh.MeshSizeFromPoints = 0;
Mesh.MeshSizeFromCurvature = 0;
Mesh.MeshSizeExtendFromBoundary = 0;
Mesh.MeshSizeMax = hs;
hb = hs;

Point(1) = {0, 0, 0, hs};
Tp[] = Point "*";
% for i in range(len(dic['pl'])):
Point(#Tp[]+${i+1}) = {${dic['pl'][len(dic['pl'])-1-i][0]-0.5}*rL/L, ${dic['pl'][len(dic['pl'])-1-i][1]-0.5}*rH/H, 0, hb};
% endfor
Tp[] = Point "*";
Point(#Tp[]+1) = {0, rH, 0, hs};
Tp[] = Point "*";
% for i in range(len(dic['pb'])-1):
Point(#Tp[]+${i+1}) = {${dic['pb'][len(dic['pb'])-1-i][0]+0.5}*rL/L, ${dic['pb'][len(dic['pb'])-1-i][1]-0.5}*rH/H, 0, hb};
% endfor
Tp[] = Point "*";
Point(#Tp[]+1) = {rL, rH, 0, hs};
Tp[] = Point "*";
% for i in range(len(dic['pr'])-1):
Point(#Tp[]+${i+1}) = {${dic['pr'][len(dic['pr'])-1-i][0]+0.5}*rL/L, ${dic['pr'][len(dic['pr'])-1-i][1]-0.5}*rH/H, 0, hb};
% endfor
Tp[] = Point "*";
Point(#Tp[]+1) = {rL, 0, 0, hs};
Tp[] = Point "*";
% for i in range(len(dic['pt'])-2):
Point(#Tp[]+${i+1}) = {${dic['pt'][len(dic['pt'])-1-i][0]+0.5}*rL/L, ${dic['pt'][len(dic['pt'])-1-i][1]-1.5}*rH/H, 0, hb};
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
% for i in range(len(dic['bdnL'])):
bdnL[] += {out[${dic['bdnL'][i]+2}]};
% endfor
% for i in range(len(dic['bdnT'])):
bdnT[] += {out[${dic['bdnT'][i]+2}]};
% endfor
% for i in range(len(dic['bdnR'])):
bdnR[] += {out[${dic['bdnR'][i]+2}]};
% endfor
% for i in range(len(dic['bdnB'])):
bdnB[] += {out[${dic['bdnB'][i]+2}]};
% endfor
% for i in range(len(dic['wall'])-1):
bdnW[] += {out[${dic['wall'][i]+2}]};
% endfor

//Physical Surface("left") = bdnL[];
Physical Surface("inlet") = bdnT[];
//Physical Surface("right") = bdnR[];
Physical Surface("outlet") = bdnB[];
//Physical Surface("wall") = bdnW[];

Mesh.MshFileVersion=2.2;
Mesh 3;