#!/bin/bash
#-----------------------------------------------------------------------
# Makefile for FAR3d Eigensolver executable
#-----------------------------------------------------------------------

echo Welcome to FAR3d Eigensolver
cd Eigensolver

#These are generic flags and commands.
Comp="gfortran" 
Exc=" xEigen" 
Opt=" -O2"
Flag=" -ffixed-form"

echo The Eigensolver executable is been compiled

#Libraries:
OBJS=" LIB_JDQZ/error.f LIB_JDQZ/jdqz.f LIB_JDQZ/jdqzmv.f LIB_JDQZ/makemm.f LIB_JDQZ/mkqkz.f LIB_JDQZ/myexc.f" 
OBJS2=" LIB_JDQZ/psolve.f LIB_JDQZ/qzsort.f LIB_JDQZ/select.f LIB_JDQZ/zcgstab.f LIB_JDQZ/zgmres.f"
OBJS3=" LIB_JDQZ/zmgs.f LIB_JDQZ/zones.f LIB_JDQZ/zxpay.f LIB_JDQZ/zzeros.f LIB_JDQZ/zgegs.f LIB_JDQZ/zgegv.f"

#Main eigensolver files:
OBJS4=" grandom_mod.f90 symtrd_mod.f90 myjdqz_mod_TAEFL_cmplx.f90 main_jdqz_TAEFL_cmplx.f90"

#lapack library:
OBJS5=" -I. -L/sci_software/lapack-3.6.1/LAPACKE/llapack -L/share/apps/scalapack_gcc_5.2/lib -lreflapack -lrefblas -lm -L/LIB_JDQZ/libblas.so.3"

$Comp -o $Exc $Opt $Flag $OBJS $OBJS2 $OBJS3 $OBJS4 $OBJS5 

echo The FAR3d Eigensolver is created 
	 

