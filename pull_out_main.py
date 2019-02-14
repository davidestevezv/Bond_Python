#!/usr/bin/python

#Units mm, N, MPa

from abaqus import *
from abaqusConstants import *
from caeModules import *
import numpy as np
from tempfile import mkstemp
from shutil import move
from os import remove, close
from pull_out_data_copy import *


def calculate_springs(input):
	data['tau_max'] = (data['fcm']**0.5)*2.5
	data['tau_final'] = data['tau_max']*0.4
	data['area'] = np.pi*data['phi']*data['m_size']

	s=0.
	fs_list=[]
	while s<data['s3']:
		
		if s<=data['s1']:
			f = data['tau_max']*((s/data['s1'])**data['alpha'])*data['area']
		elif s>data['s1'] and s<=data['s2']:
			f = data['tau_max']*data['area']
		elif s>data['s2'] and s<=data['s3']:
			f = (data['tau_max']-(data['tau_max']-data['tau_final'])*((s-data['s2'])/(data['s3']-data['s2'])))*data['area']
		else:
			f = data['tau_final']*data['area']

		fs_list.append([f,s])
		fs_int_positive = list(fs_list)
		fs_int_positive = tuple(tuple([i[0], i[1]]) for i in fs_int_positive)
		fs_int_positive_reverse = list(fs_list[:0:-1])
		fs_int_negative = tuple([tuple([-i[0], -i[1]]) for i in fs_int_positive_reverse])
		fs_int = fs_int_negative + fs_int_positive
		fs_ext= tuple([tuple([i[0]/2., i[1]]) for i in fs_int ])
		s += data['s_size']


	return fs_int, fs_ext

fs_int, fs_ext= calculate_springs(input)



def TensionSoftening(input):
	data['fctm']=1.4*((data['fck_cyl']/10.)**(2./3.))
	data['Gf']=(73.*(data['fcm']**0.18))/1000.
	data['wcr']=5.14*(data['Gf']/data['fctm'])

	wt=0.
	tau=data['fctm']
	tau_list=[]
	while tau>=0.1:

		tau=((1.+(data['c1']*(wt/data['wcr']))**3.)*np.exp(-data['c2']*(wt/data['wcr']))-(wt/data['wcr'])*(1.+data['c1']**3.)*np.exp(-data['c2']))*data['fctm']
		tau_list.append([tau,wt])
		wt += data['t_size']

	tension_softening = [tuple([i[0], i[1]/data['m_size']]) for i in tau_list]

	tension_softening = tuple(tension_softening)
	return tension_softening

tension_softening = TensionSoftening(input)


def CompressionHardening(input):
	data['ec1']=(0.7*(data['fcm']**0.31))/1000.
	data['ecu1']=0.0035
	data['kh']=1.05*data['E_c']*(data['ec1']/data['fcm'])
	data['fcm_plastic']=0.4*data['fcm']
	data['ec_plastic']=data['fcm_plastic']/data['E_c']

	comHarden_list=[[data['fcm_plastic'], 0.]]
	ec = data['ec_plastic']+data['c_size']
	while ec<=data['ecu1']:
		data['etha']=ec/data['ec1']
		tau=((data['kh']*data['etha']-data['etha']**2)/((1.+(data['kh']-2.)*data['etha'])))*data['fcm']
		comHarden_list.append([tau,ec])
		ec+=data['c_size']

	compression_hardening = [tuple([i[0], i[1]]) for i in comHarden_list]

	compression_hardening = tuple(compression_hardening)
	return compression_hardening

compression_hardening = CompressionHardening(input)









#Create a new data['model_name']
model = mdb.Model(name=data['model_name'], modelType=STANDARD_EXPLICIT)



#Concrete-Part
s = model.ConstrainedSketch(name='concrete', 
    sheetSize=200.0)
g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
s.rectangle(point1=(-data['lenght']/2., -data['width']/2.), point2=(data['lenght']/2., data['width']/2.))
part = model.Part(name='Concrete', dimensionality=THREE_D, 
    type=DEFORMABLE_BODY)
part.BaseSolidExtrude(sketch=s, depth=data['height'])


#Rebar-Part
s1 = model.ConstrainedSketch(name='rebar', 
    sheetSize=200.0)
g, v, d, c = s1.geometry, s1.vertices, s1.dimensions, s1.constraints
s1.Line(point1=(0.0, 0.0), point2=(0.0, data['height']))
p = model.Part(name='Rebar', dimensionality=THREE_D, 
    type=DEFORMABLE_BODY)
p = model.parts['Rebar']
p.BaseWire(sketch=s1)


#Cutting planes-Concrete
p = model.parts['Concrete']
p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=data['xy_plane'])
p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=data['xz_plane'])
p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=data['yz_plane'])
c = p.cells
d1=p.datums
d2=p.datums
pickedCells = c.findAt(((0, 0, data['height']/2.), ))
p.PartitionCellByDatumPlane(datumPlane=d1[2], cells=pickedCells)
pickedCells = c.findAt(((0, 0, data['height']), ))
p.PartitionCellByDatumPlane(datumPlane=d2[4], cells=pickedCells)
pickedCells = c.findAt(((data['lenght']/2., 0., data['height']), ))
p.PartitionCellByDatumPlane(datumPlane=d1[3], cells=pickedCells)
pickedCells = c.findAt(((-data['lenght']/2., 0., data['height']), ))
p.PartitionCellByDatumPlane(datumPlane=d2[3], cells=pickedCells)


#Cutting planes-Rebar
p = model.parts['Rebar']
p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=data['height']/2.)
e = p.edges
pickedEdges = e.findAt(((0.0, data['height']/2., 0.0), ))
d1 = p.datums
p.PartitionEdgeByDatumPlane(datumPlane=d1[2], edges=pickedEdges)




#Materials
material_c = model.Material(name='Concrete')
material_c.Elastic(table=((data['E_c'], data['nu_c']), ))
material_c.ConcreteDamagedPlasticity(table=((
    data['dil_angle'], data['eccentricity'], data['fb0_fcO'], data['k'], data['viscosity']), ))
material_c.concreteDamagedPlasticity.ConcreteCompressionHardening(
    table=(compression_hardening))
material_c.concreteDamagedPlasticity.ConcreteTensionStiffening(
    table=(tension_softening))

material_s = model.Material(name='Steel')
material_s.Elastic(table=((data['E_s'], data['nu_s']), ))
material_s.Plastic(table=((548.0, 0.0), (663.0, 
    0.12)))


#Sections
model.CircularProfile(name='phi_rebar', r=data['phi']/2.)
model.BeamSection(name='Rebar', integration=DURING_ANALYSIS, 
    poissonRatio=0.0, profile='phi_rebar', material='Steel', temperatureVar=LINEAR, 
    consistentMassMatrix=False)
model.HomogeneousSolidSection(name='Concrete', 
    material='Concrete', thickness=None)

p = model.parts['Rebar']
e = p.edges
edges = e.findAt(((0.0, 0.0, 0.0), ), ((0.0, data['height'], 0.0), ))
region = regionToolset.Region(edges=edges)
p.SectionAssignment(region=region, sectionName='Rebar', offset=0.0, 
    offsetType=MIDDLE_SURFACE, offsetField='', 
    thicknessAssignment=FROM_SECTION)
edges = e.findAt(((0.0, 0.0, 0.0), ), ((0.0, data['height'], 0.0), ))
region=regionToolset.Region(edges=edges)
p.assignBeamSectionOrientation(region=region, method=N1_COSINES, n1=(0.0, 0.0, 
    -1.0))

p = model.parts['Concrete']
c = p.cells
cells = c.findAt(((0.0, 0.0, 0.0), ), ((-data['lenght']/2., -data['width']/2., 
    data['height']), ), ((-data['lenght']/2., data['width']/2., data['height']), ), ((data['lenght']/2., -data['width']/2., 
    data['height']), ), ((data['lenght']/2., data['width']/2., data['height']), ))
region = regionToolset.Region(cells=cells)
p.SectionAssignment(region=region, sectionName='Concrete', offset=0.0, 
    offsetType=MIDDLE_SURFACE, offsetField='', 
    thicknessAssignment=FROM_SECTION)


#Step
model.StaticStep(name='Step-1', previous='Initial', 
    maxNumInc=5000, stabilizationMagnitude=0.0002, 
    stabilizationMethod=DISSIPATED_ENERGY_FRACTION, 
    continueDampingFactors=False, adaptiveDampingRatio=0.05, initialInc=0.05, 
    minInc=1e-07, nlgeom=ON)


#Assembly, Loads and Boundary conditions
a = model.rootAssembly
a.DatumCsysByDefault(CARTESIAN)
p = model.parts['Concrete']
a.Instance(name='Concrete', part=p, dependent=OFF)
p = model.parts['Rebar']
a.Instance(name='Rebar', part=p, dependent=OFF)
vector = (data['yz_plane'], data['xz_plane']-data['height'], data['height'])
a.translate(instanceList=('Rebar', ), vector=vector)
a.rotate(instanceList=('Rebar', ), axisPoint=(data['yz_plane'], data['xz_plane'], data['height']), 
    axisDirection=(data['yz_plane']+5., 0.0, 0.0), angle=90.0)
vector = (0., 0., 1.) #Moves the bar 1 mm (z) so that the springs can be connected
a.translate(instanceList=('Rebar', ), vector=vector)

f1 = a.instances['Concrete'].faces
faces1 = f1.findAt(((0.0, 0.0, 0.0), ))
region = regionToolset.Region(faces=faces1)
model.DisplacementBC(name='Disp', createStepName='Step-1', 
    region=region, u1=UNSET, u2=UNSET, u3=data['Displacement'], ur1=UNSET, ur2=UNSET, ur3=UNSET, 
    amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='', 
    localCsys=None)

v1 = a.instances['Rebar'].vertices
verts1 = v1.findAt(((data['yz_plane'],data['xz_plane'] , 1.0), ))
region = regionToolset.Region(vertices=verts1)
model.DisplacementBC(name='BC', createStepName='Step-1', 
    region=region, u1=0.0, u2=0.0, u3=0.0, ur1=0.0, ur2=0.0, ur3=0.0, 
    amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='', 
    localCsys=None)


#Mesh
a = model.rootAssembly
partInstances = (a.instances['Concrete'], a.instances['Rebar'],)
a.seedPartInstance(regions=partInstances, size=data['m_size'], deviationFactor=0.1,
	minSizeFactor=0.1)
elemType = mesh.ElemType(elemCode=C3D8R, elemLibrary=STANDARD, 
    kinematicSplit=AVERAGE_STRAIN, secondOrderAccuracy=OFF, 
    hourglassControl=DEFAULT, distortionControl=DEFAULT)
c = a.instances['Concrete'].cells
cells = c.findAt(((0.0, 0.0, 0.0), ), ((-data['lenght']/2., -data['width']/2., 
    data['height']), ), ((-data['lenght']/2., data['width']/2., data['height']), ), ((data['lenght']/2., -data['width']/2., 
    data['height']), ), ((data['lenght']/2., data['width']/2., data['height']), ))
pickedRegions =(cells, )
a.setElementType(regions=pickedRegions, elemTypes=(elemType,))
a.generateMesh(regions=partInstances)


#Sets for results
a = model.rootAssembly
instancias = a.instances

nodosbarra = instancias['Rebar'].nodes
xmin = data['yz_plane']-0.01
ymin = data['xz_plane']-0.01
zmin = 0.
xmax = data['yz_plane']+0.01
ymax = data['xz_plane']+0.01
zmax = 1.1
RF_point = nodosbarra.getByBoundingBox(xmin,ymin,zmin,xmax,ymax,zmax)
a.Set(nodes=RF_point, name='RF')
xmin = data['yz_plane']-0.01
ymin = data['xz_plane']-0.01
zmin = data['height']
xmax = data['yz_plane']+0.01
ymax = data['xz_plane']+0.01
zmax = data['height']+1.1
DispRebar_point = nodosbarra.getByBoundingBox(xmin,ymin,zmin,xmax,ymax,zmax)
a.Set(nodes=DispRebar_point, name='DispRebar')

nodoshormigon = instancias['Concrete'].nodes
xmin = 3*data['m_size']-0.01
ymin = 0.
zmin = data['height']-0.01
xmax = 3*data['m_size']+0.01
ymax = 0.
zmax = data['height']+0.01
DispConcrete_point = nodoshormigon.getByBoundingBox(xmin,ymin,zmin,xmax,ymax,zmax)
a.Set(nodes=DispConcrete_point, name='DispConcrete')

regionDef = a.sets['DispConcrete']
model.HistoryOutputRequest(name='Disp_Concrete', 
    createStepName='Step-1', variables=('U3', ), region=regionDef)
regionDef = a.sets['DispRebar']
model.HistoryOutputRequest(name='Disp_Rebar', 
    createStepName='Step-1', variables=('U3', ), region=regionDef)
regionDef = a.sets['RF']
model.HistoryOutputRequest(name='Reaction_Force', 
    createStepName='Step-1', variables=('RF3', ), region=regionDef)


#Springs-nodes.
a = model.rootAssembly
instancias = a.instances

tol=1.5

nodoshormigon = instancias['Concrete'].nodes
nodosbarra = instancias['Rebar'].nodes
center1 = (data['yz_plane'], data['xz_plane'], data['xy_plane'])
center2 = (data['yz_plane'], data['xz_plane'], data['height'] + tol)
radius = tol

nodos_adh = nodosbarra.getByBoundingCylinder(center1, center2, radius)

contador = 1
for nodo in nodos_adh:
	punto = nodo.coordinates
	coordZ = punto[2]
	if coordZ<(data['xy_plane']+data['m_size']):
		a.Set(nodes=mesh.MeshNodeArray((nodo,)), name='nb_ext' + str(contador))
		nodocoincidente = nodoshormigon.getByBoundingSphere(punto, tol)
		a.Set(nodes=nodocoincidente, name='nh_ext'+str(contador))
		rgn1pair0=a.sets['nb_ext'+str(contador)]
		rgn2pair0=a.sets['nh_ext'+str(contador)]
		region=((rgn1pair0, rgn2pair0), )
		a.engineeringFeatures.TwoPointSpringDashpot(name='Spring_Ext-'+str(contador), regionPairs=region, axis=FIXED_DOF, dof1=3, dof2=3, springBehavior=ON, springStiffness=500., dashpotBehavior=OFF, dashpotCoefficient=0.0)
		model.Equation(name='Constraint-'+str(contador)+'-U1', terms=((1.0, 'nh_ext'+str(contador), 1), (-1.0, 'nb_ext'+str(contador), 1)))
		model.Equation(name='Constraint-'+str(contador)+'-U2', terms=((1.0, 'nh_ext'+str(contador), 2), (-1.0, 'nb_ext'+str(contador), 2)))

	elif coordZ>data['height']:
		a.Set(nodes=mesh.MeshNodeArray((nodo,)), name='nb_ext' + str(contador))
		nodocoincidente = nodoshormigon.getByBoundingSphere(punto, tol)
		a.Set(nodes=nodocoincidente, name='nh_ext'+str(contador))
		rgn1pair0=a.sets['nb_ext'+str(contador)]
		rgn2pair0=a.sets['nh_ext'+str(contador)]
		region=((rgn1pair0, rgn2pair0), )
		a.engineeringFeatures.TwoPointSpringDashpot(name='Spring_Ext-'+str(contador), regionPairs=region, axis=FIXED_DOF, dof1=3, dof2=3, springBehavior=ON, springStiffness=500., dashpotBehavior=OFF, dashpotCoefficient=0.0)
		model.Equation(name='Constraint-'+str(contador)+'-U1', terms=((1.0, 'nh_ext'+str(contador), 1), (-1.0, 'nb_ext'+str(contador), 1)))
		model.Equation(name='Constraint-'+str(contador)+'-U2', terms=((1.0, 'nh_ext'+str(contador), 2), (-1.0, 'nb_ext'+str(contador), 2)))

	else:
		a.Set(nodes=mesh.MeshNodeArray((nodo,)), name='nb_int' + str(contador))
		nodocoincidente = nodoshormigon.getByBoundingSphere(punto, tol)
		a.Set(nodes=nodocoincidente, name='nh_int'+str(contador))
		rgn1pair0=a.sets['nb_int'+str(contador)]
		rgn2pair0=a.sets['nh_int'+str(contador)]
		region_int=((rgn1pair0, rgn2pair0), )
		a.engineeringFeatures.TwoPointSpringDashpot(name='Spring_Int-'+str(contador), regionPairs=region_int, axis=FIXED_DOF, dof1=3, dof2=3, springBehavior=ON, springStiffness=1000., dashpotBehavior=OFF, dashpotCoefficient=0.0)
		model.Equation(name='Constraint-'+str(contador)+'-U1', terms=((1.0, 'nh_int'+str(contador), 1), (-1.0, 'nb_int'+str(contador), 1)))
		model.Equation(name='Constraint-'+str(contador)+'-U2', terms=((1.0, 'nh_int'+str(contador), 2), (-1.0, 'nb_int'+str(contador), 2)))

	contador = contador + 1



#Job
mdb.Job(name=data['model_name'], model=data['model_name'], description='', type=ANALYSIS, 
    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90, 
    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, 
    explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF, 
    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='', 
    scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT, numCpus=2, 
    numDomains=2, numGPUs=0)


#Creates inp file and modifies the springs
mdb.jobs[data['model_name']].writeInput(consistencyChecking=OFF)



#funcion buscar y reemplazar
def replace(file_path, pattern, subst):
	fh, abs_path=mkstemp()
	with open(abs_path, 'w') as new_file:
		with open(file_path) as old_file:
			for line in old_file:
				new_file.write(line.replace(pattern,subst))
	close(fh)
	remove(file_path)
	move(abs_path, file_path)

archivo = data['model_name']+str('.inp')
pattern = 'Spring2'
subst = 'SpringA'
replace(archivo, pattern, subst)

pattern = '*Spring, elset'
subst = '*Spring, nonlinear, elset'
replace(archivo, pattern, subst)


with open((data['model_name']+str('.inp'))) as f:
	archivoviejo = f.read().splitlines() #leemos el archivo almacenando cada linea en una lista como si fuese un string

archivonuevo = [] #abrimos una lista y la guardamos en la variable archivonuevo
lineastotales = len(archivoviejo) #almacenamos en la variable el numero de elementos de la lista archivoviejo
contador = 0
while contador < lineastotales:
	if archivoviejo[contador][0:7] != '*Spring': #Si el elemento en la lista contiene los primeros caracteres distintos a *Spring anhadimos directamente esa fila al nuevo archivo
 		archivonuevo.append(archivoviejo[contador])
 		contador = contador + 1
 	elif archivoviejo[contador][0:36] == '*Spring, nonlinear, elset=Spring_Ext':
 		archivonuevo.append(archivoviejo[contador])
 		archivonuevo.append('')
 		ley = ''
 		valores = [str(fi)+','+str(si) for fi,si in fs_ext] #Elimino () de la tupla
 		for i in valores[0:-1]: #Cada par de puntos en una linea.
 			ley += i + '\n'
 		ley += valores[-1] #Se evita que tras anhadir el ultimo elemento se introduzca un salto de linea
 		archivonuevo.append(ley)
 		contador = contador + 3
 	else:
 		archivonuevo.append(archivoviejo[contador])
 		archivonuevo.append('')
 		ley = ''
 		valores = [str(fi)+','+str(si) for fi,si in fs_int]
 		for i in valores[0:-1]:
 			ley += i + '\n'
 		ley += valores[-1]
 		archivonuevo.append(ley)
 		contador = contador + 3
f.close()

with open(data['model_name']+str('.inp'), 'w') as inpfinal:
	for linea in archivonuevo:
 		inpfinal.write("%s\n" % linea)
inpfinal.close()
