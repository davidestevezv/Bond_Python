#!/usr/bin/python

from tempfile import mkstemp
import os, shutil

diameter_rebar  = 16.
diameter_number = 10
diameter_list   = [diameter_rebar*i for i in range(1,diameter_number+1)]


def replace(file_path, pattern, subst):
	fh, abs_path=mkstemp()
	with open(abs_path, 'w') as new_file:
		with open(file_path) as old_file:
			for line in old_file:
				new_file.write(line.replace(pattern,subst))
	os.close(fh)
	os.remove(file_path)
	shutil.move(abs_path, file_path)


for d1 in diameter_list:
	for d2 in diameter_list:
		cover  = d1
		lenght = d2
		variable1=2.*cover+diameter_rebar
		variable2=2.*lenght
		name   = 'pull_out_C'+str(cover)+'_L'+str(lenght)
		if not os.path.exists(name):
    			os.makedirs(name)
		ruta = os.getcwd() + os.sep
		origen = ruta + 'pull_out_data.py'
		destino = ruta + 'pull_out_data_copy.py'
		if os.path.exists(origen):
			archivo = shutil.copy2(origen,destino)

		archivo = 'pull_out_data_copy.py'
		pattern = 'variable1=128.'
		subst = 'variable1='+str(variable1)
		replace(archivo, pattern, subst)

		archivo = 'pull_out_data_copy.py'
		pattern = 'variable2=160.'
		subst = 'variable2='+str(variable2)
		replace(archivo, pattern, subst)

		shutil.move(destino, name)

		origen = 'pull_out_main.py'
		destino = 'pull_out_main_copy.py'
		if os.path.exists(origen):
			archivo=shutil.copy2(origen,destino)
		shutil.move(destino, name)

		origen = 'lanzador_local.sh'
		destino = 'lanzador_local_copy.sh'
		if os.path.exists(origen):
			archivo=shutil.copy2(origen,destino)
		shutil.move(destino, name)

		origen = 'pull_out_post.py'
		destino = 'pull_out_post_copy.py'
		if os.path.exists(origen):
			archivo=shutil.copy2(origen,destino)
		shutil.move(destino, name)		

