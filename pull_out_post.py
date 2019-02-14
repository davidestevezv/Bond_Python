#!/usr/bin/python
from odbAccess import*
from abaqusConstants import*
from pull_out_data_copy import*
import numpy as np

odb=openOdb(path='pull_out_results.odb')

lista = odb.steps['Step-1'].historyRegions.keys()

#ConcreteDisplacement = str(lista[1])
#RebarDisplacement = str(lista[3])
RebarReactionForce = str(lista[2])

#region1 = odb.steps['Step-1'].historyRegions[ConcreteDisplacement]
#region2 = odb.steps['Step-1'].historyRegions[RebarDisplacement]
region3 = odb.steps['Step-1'].historyRegions[RebarReactionForce]

#Displacement_Concrete = region1.historyOutputs['U3'].data
#Displacement_Rebar    = region2.historyOutputs['U3'].data
ReactionForce         = region3.historyOutputs['RF3'].data

Force = []
for time,RF in ReactionForce:
	Values = '%5.3f	 %5.3f\n' % (time,RF)
	Force.append(-1*RF)
MaxValue = np.max(Force)
Section = np.pi*data['phi']*data['xy_plane']
m_stress = MaxValue/Section
rebar_stress = MaxValue/(np.pi*(8**2))
percentage = (rebar_stress/548.)*100

ResultsFile = open('results.dat','w')
ResultsFile.write('Cover	Adh_Lenght		Mean_Stress		Rebar_Stress		Percentage 		Force\n')
ResultsFile.write(' phi		phi		  	 	MPa				MPa				    %			kN\n')
ResultsFile.write('%4.1f		%4.1f	  %10.3f	   %10.3f		%10.3f	   %10.3f\n'	%	((data['lenght']-16.)/2,data['height']/2,m_stress,rebar_stress,percentage,MaxValue/1000.))
ResultsFile.close()