% for i in range(dic['l1']):
${dic['geo'][i][:-1]}
% endfor

% if len(dic['p'])>0:
Tp[] = Point "*";
h(${dic['ng']}) = hs;
% for i in range(len(dic['p'])):
Point(#Tp[]+${i+1}) = {(rL/L)*${dic['p'][i][0]}, ${dic['p'][i][1]}*rH/H, 0, h(${dic['ng']})};
% endfor

Tp1[] = Point "*";
For i In {#Tp[]+1 : #Tp1[] - 1}
  Line(i)={i, i + 1};
EndFor
Line(#Tp1[])={#Tp1[], #Tp[]+1};

Line Loop(1+n+1)={#Tp[]+1: #Tp1[]};
n = n+1;

% endif
% for j in range(dic['l1'],dic['lf']):
${dic['geo'][j][:-1]}
% endfor
${dic['geo'][dic['lf']]}