from abaqus import *
from abaqusConstants import *
from caeModules import *
from driverUtils import executeOnCaeStartup

from tempfile import mkstemp
from shutil import move
from os import remove, close
import numpy as np

openMdb(pathName='/home/mcostas/adherencia.cae')

# Tabla codigo modelo
#introducir resistencia caracteristica y espaciado
fck = 50.
rib_spacing = 10. # OJO en mm
col2={'s1':0.6, 's2':0.6, 's3':1.0, 'alpha':0.4, 'Tmax': 2*np.sqrt(fck), 'Tf':0.15*2*np.sqrt(fck)}
col3={'s1':0.6, 's2':0.6, 's3':2.5, 'alpha':0.4, 'Tmax': 1*np.sqrt(fck), 'Tf':0.15*2*np.sqrt(fck)}
col4={'s1':1.0, 's2':3.0, 's3':rib_spacing, 'alpha':0.4, 'Tmax': 2.5*np.sqrt(fck), 'Tf':0.4*2*np.sqrt(fck)}
col5={'s1':1.0, 's2':3.0, 's3':rib_spacing, 'alpha':0.4, 'Tmax': 1.25*np.sqrt(fck), 'Tf':0.4*2*np.sqrt(fck)}

#seleccionar condiciones de adherencia
condiciones = col4
valores_s = np.linspace(0,condiciones['s1'],20).tolist()
valores_s.append(condiciones['s2'])
valores_s.append(condiciones['s3'])

valores_tau = []

for i in valores_s[0:20]:
	valor_tau = condiciones['Tmax']*((i/condiciones['s1'])**condiciones['alpha'])
	valores_tau.append(valor_tau)

valores_tau.append(condiciones['Tmax'])
valores_tau.append(condiciones['Tf'])
#anhadir comportamiento simetrico a compresion
valores_s_compresion = []
for i in list(reversed(valores_s[1::])):
	valores_s_compresion.append(-i)

valores_s = valores_s_compresion + valores_s

valores_tau_compresion = []
for i in list(reversed(valores_tau[1::])):
	valores_tau_compresion.append(-i)

valores_tau = valores_tau_compresion + valores_tau


#conversion de unidades
valores_s = [i/1000 for i in valores_s]
valores_tau = [i*1000 for i in valores_tau]


#funcion buscar y reemplazar
def replace(file_path, pattern, subst):
    fh, abs_path = mkstemp()
    with open(abs_path,'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))
    close(fh)
    remove(file_path)
    move(abs_path, file_path)

#funcion calculo de distancia
def distancia(coords1, coords2):
	dist = np.sqrt((coords2[2]-coords1[2])**2 + (coords2[1]-coords1[1])**2 + (coords2[0]-coords1[0])**2)
	return dist


#comandos para preparar el modelo (prescindibles en un caso general)
a = mdb.models['Model-1'].rootAssembly
f1 = a.instances['viga-1'].faces
faces1 = f1.getSequenceFromMask(mask=('[#8 ]', ), )
region = regionToolset.Region(faces=faces1)
mdb.models['Model-1'].EncastreBC(name='BC-1', createStepName='Initial', region=region, localCsys=None)
mdb.models['Model-1'].StaticStep(name='Step-1', previous='Initial')
session.viewports['Viewport: 1'].assemblyDisplay.setValues(step='Step-1')
session.viewports['Viewport: 1'].assemblyDisplay.setValues(loads=ON, bcs=ON, 
    predefinedFields=ON, connectors=ON, adaptiveMeshConstraints=OFF)
a = mdb.models['Model-1'].rootAssembly
f1 = a.instances['viga-2'].faces
faces1 = f1.getSequenceFromMask(mask=('[#2 ]', ), )
region = regionToolset.Region(faces=faces1)
mdb.models['Model-1'].DisplacementBC(name='BC-2', createStepName='Step-1', 
    region=region, u1=0.0, u2=0.0, u3=0.001, ur1=0.0, ur2=0.0, ur3=0.0, 
    amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='', 
    localCsys=None)

mdb.models['Model-1'].steps['Step-1'].setValues(maxNumInc=100000, initialInc=0.001, minInc=1e-20, nlgeom=ON)



#encontrar nodos coincidentes y asignar muelles lineales
a = mdb.models['Model-1'].rootAssembly
instancias = mdb.models['Model-1'].rootAssembly.instances


tol = 1e-6
tolgrande = 1e-3

nodosbarras = instancias['barra_viga-1'].nodes
for instancia in instancias.items():
	if instancia[0][0:5] == 'barra' and instancia[0] != 'barra_viga-1':
		nodosbarras = nodosbarras + instancia[1].nodes

nodosviga1 = instancias['viga-1'].nodes
nodosviga2 = instancias['viga-2'].nodes


cotainterfaz = 0.2
toleranciainterfaz = 0.001
contadormuelles = 1
for nodo in nodosbarras:
	punto = nodo.coordinates
	coordY = punto[1]
	a.Set(nodes=mesh.MeshNodeArray((nodo,)), name='puntobarra'+str(contadormuelles))
	if coordY - cotainterfaz < -toleranciainterfaz:
		nodocoincidente = nodosviga1.getByBoundingSphere(punto,tol)
	elif coordY - cotainterfaz > toleranciainterfaz:
		nodocoincidente = nodosviga2.getByBoundingSphere(punto,tol)
	elif abs(coordY - cotainterfaz) <= toleranciainterfaz:
		continue
	elementos = nodo.getElements()
	if len(elementos) == 1:
		nodoselemento = elementos[0].getNodes()
		coords1 = nodoselemento[0].coordinates
		coords2 = nodoselemento[1].coordinates
		longelemento = distancia(coords1,coords2)
		inst = elementos[0].instanceName
		parte = a.instances[inst].part
		seccion = parte.sectionAssignments[0].sectionName
		perfil = mdb.models['Model-1'].sections[seccion].profile
		radio = mdb.models['Model-1'].profiles[perfil].r
		atributaria = 2*3.141592*radio*longelemento/2
		print atributaria
	else:
		nodoselemento1 = elementos[0].getNodes()
		coords11 = nodoselemento1[0].coordinates
		coords12 = nodoselemento1[1].coordinates
		longelemento1 = distancia(coords11,coords12)
		nodoselemento2 = elementos[1].getNodes()
		coords21 = nodoselemento2[0].coordinates
		coords22 = nodoselemento2[1].coordinates
		longelemento2 = distancia(coords21,coords22)
		inst = elementos[0].instanceName
		parte = a.instances[inst].part
		seccion = parte.sectionAssignments[0].sectionName
		perfil = mdb.models['Model-1'].sections[seccion].profile
		radio = mdb.models['Model-1'].profiles[perfil].r
		atributaria1 = 2*3.141592*radio*longelemento1/2		
		atributaria2 = 2*3.141592*radio*longelemento2/2
		atributaria = atributaria1 + atributaria2
		print atributaria
		# almacenar el valor del area tributaria en la rigidez para poder sustituirlo bien despues
	a.Set(nodes = nodocoincidente, name='puntoviga'+str(contadormuelles))
	rgn1pair0=a.sets['puntobarra'+str(contadormuelles)]
	rgn2pair0=a.sets['puntoviga'+str(contadormuelles)]
	region=((rgn1pair0, rgn2pair0), )
	mdb.models['Model-1'].rootAssembly.engineeringFeatures.TwoPointSpringDashpot(name='Springs/Dashpots-'+str(contadormuelles), regionPairs=region, axis=FIXED_DOF, dof1=2, dof2=2, springBehavior=ON, springStiffness=atributaria, dashpotBehavior=OFF, dashpotCoefficient=0.0)
	mdb.models['Model-1'].Equation(name='Constraint-'+str(contadormuelles)+'-U1', terms=((1.0, 'puntoviga'+str(contadormuelles), 1), (-1.0, 'puntobarra'+str(contadormuelles), 1)))
	mdb.models['Model-1'].Equation(name='Constraint-'+str(contadormuelles)+'-U3', terms=((1.0, 'puntoviga'+str(contadormuelles), 3), (-1.0, 'puntobarra'+str(contadormuelles), 3)))
	if len(elementos) == 1:
		nombrepunto = 'puntobarra'+str(contadormuelles)
		region = a.sets[nombrepunto]
		nombrebc = 'torsor'+str(contadormuelles)
		mdb.models['Model-1'].DisplacementBC(name=nombrebc, createStepName='Step-1', region=region, u1=UNSET, u2=UNSET, u3=UNSET, ur1=UNSET, ur2=0.0, ur3=UNSET, amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='', localCsys=None)
	contadormuelles = contadormuelles + 1		


#sustituir lineal por no lineal en el inp...
mdb.jobs['testadh'].writeInput(consistencyChecking=OFF)
archivo = 'testadh.inp'
pattern = 'Spring2'
subst = 'SpringA'
replace(archivo, pattern, subst)

pattern = '*Spring, elset'
subst = '*Spring, nonlinear, elset'
replace(archivo, pattern, subst)

with open('testadh.inp') as f:
    archivoviejo = f.read().splitlines()


#... y anhadir el comportamiento no lineal
archivonuevo = []
lineastotales = len(archivoviejo)
contador = 0
while contador < lineastotales:
	if archivoviejo[contador][0:7] != '*Spring':
		archivonuevo.append(archivoviejo[contador])
		contador = contador + 1
	else:
		archivonuevo.append(archivoviejo[contador])
		archivonuevo.append('')
		ley = ''
		area = float(archivoviejo[contador+2])
		cortantes = [i*area for i in valores_tau]
		junto = [str(ti)+','+str(si) for ti,si in zip(cortantes,valores_s)]
		for i in junto[0:-1]:
			ley +=i+'\n'
		ley += junto[-1]
		archivonuevo.append(ley)
		contador = contador + 3
f.close()

inpfinal = open('adherencia.inp', 'w')
for linea in archivonuevo:
	inpfinal.write("%s\n" % linea)
inpfinal.close()
