import os
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import cm, colors
from mpl_toolkits.mplot3d import Axes3D
import scipy.interpolate as interp


diameter_rebar  = 16.
diameter_number = 10
diameter_list1   = [diameter_rebar*i for i in range(1,diameter_number+1)]
diameter_list2   = [diameter_rebar*i for i in range(1,diameter_number+1)]

Cover_list =		[]
Adh_Lenght_list =   []
Mean_Stress_list =  []
Rebar_Stress_list = []
Percentage_list =   []
Force_list = 		[]

root = os.getcwd()

file = 'results.dat'
names = ['Cover', 'Adh_Lenght', 'Mean_Stress', 'Rebar_Stress', 'Percentage', 'Force']

for d1 in diameter_list1:
	for d2 in diameter_list2:
		os.chdir(root)
		N1 = d1
		N2 = d2
		directory_name = 'pull_out_C'+str(N1)+'_L'+str(N2)
		os.chdir(directory_name)
		data = pd.read_table(file ,names=names, sep='\s+', skiprows=2)
		Cover_list.append(int(data.ix[:,0]))
		Adh_Lenght_list.append(int(data.ix[:,1]))
		Mean_Stress_list.append(int(data.ix[:,2]))
		Rebar_Stress_list.append(int(data.ix[:,3]))
		Percentage_list.append(int(data.ix[:,4]))
		Force_list.append(int(data.ix[:,5]))

os.chdir(root)

X = Cover_list
Y = Adh_Lenght_list
Z = Percentage_list

plotx,ploty, = np.meshgrid(np.linspace(np.min(X),np.max(X),40),\
                           np.linspace(np.min(Y),np.max(Y),40))
plotz = interp.griddata((X,Y),Z,(plotx,ploty),method='linear')

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(plotx, ploty, plotz, linewidth=0.1, antialiased=True, shade=True, alpha=0.95, cmap=cm.RdYlGn)

# Add a color bar which maps values to colors
fig.colorbar(surf, shrink=0.5, aspect=10)


ax.set_xlabel('Cover (mm)')
ax.set_xlim(0, 160)
ax.set_ylabel('Adh. Lenght (mm)')
ax.set_ylim(0, 160)
ax.set_zlabel('Percentage')
ax.set_zlim(0, 120)

ax.grid(False)
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False

plt.savefig('Percentage')
plt.show()
