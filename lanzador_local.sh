#!/bin/bash

# ################## lanzador-abaqus.sh ##################

# ------ Configuracion del sistema de colas ------
#$ -S /bin/bash
#$ -A Abaqus
#$ -P Abaqus
#$ -N Pull_out
#$ -l vf=4000M
#$ -v CONFIG_FILE=abaqus_v6.env,PROYECTO=Abaqus,ABAQUSVERSION=V6R2017x,MEM=4000
#$ -j y
#$ -m n
#$ -cwd
#$ -o $JOB_NAME.o$JOB_ID
#$ -notify
#$ -q normal.q
#$ -pe abaqus_pe 2

# ---------- Configuracion del entorno -----------

source /share/apps/environment.sh
module use /opt/modulefiles
module load abaqus/$ABAQUSVERSION

# ------------ Ejecucion del programa
abaqus cae noGUI=pull_out_main_copy.py
tiempo "abaqus analysis interactive input=pull_out.inp job=pull_out_results" $JOB_NAME.t$JOB_ID
abaqus cae noGUI=pull_out_post_copy.py