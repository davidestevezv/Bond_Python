#!/usr/bin/python
data = {}

#data['model_name']-Variables
data['model_name']   = 'pull_out'

variable1=128.
variable2=160.

#Geometry
data['lenght']       =  variable1
data['width']        =  variable1
data['height']       =  variable2
data['phi']          =  16.
data['xy_plane']     =  variable2/2.#Non-adhesive data['lenght']
data['xz_plane']     =  0. #Rebar position
data['yz_plane']     =  0. #Rebar position

#Materials
#-Concrete
data['fck_cube']     =  50.
data['fck_cyl']      =  data['fck_cube']*0.85
data['fcm']          =  data['fck_cyl']+8
data['E_c']          =  21500.*(data['fcm']/10)**(1./3.)
data['nu_c']         =  0.2
data['dil_angle']    =  38.
data['eccentricity'] =  0.1
data['fb0_fcO']      =  1.16
data['k']            =  0.667
data['viscosity']    =  1e-05
#-Steel
data['E_s']          =  200000.
data['nu_s']         =  0.3

#Mesh
data['m_size']       =  4.

#Load
data['Displacement'] =  2.

#Springs 
data['s_size']       =  0.4 #Step size to aproximate the curve
data['s1']           =  1.
data['s2']           =  2.
data['s3']           =  10.
data['alpha']        =  0.4

#CDP Parameters
data['c1']           =  3.
data['c2']           =  6.93
data['ecu1']         =  0.0035
data['t_size']       =  0.01 #Step size to aproximate the tension softening curve
data['c_size']       =  0.0001 #Step size to aproximate the compression hardening curve
