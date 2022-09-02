% for i in range(l1):
${lol[i][:-1]}
% endfor

% if len(p)>0:
Tp[] = Point "*";
h(${ng}) = hs;
% for i in range(len(p)):
Point(#Tp[]+${i+1}) = {(rL/L)*${p[i][0]}, ${p[i][1]}*rH/H, 0, h(${ng})};
% endfor

Tp1[] = Point "*";
For i In {#Tp[]+1 : #Tp1[] - 1}
  Line(i)={i, i + 1};
EndFor
Line(#Tp1[])={#Tp1[], #Tp[]+1};

Line Loop(1+n+1)={#Tp[]+1: #Tp1[]};
n = n+1;

% endif
% for j in range(l1,lf):
${lol[j][:-1]}
% endfor
${lol[lf]}