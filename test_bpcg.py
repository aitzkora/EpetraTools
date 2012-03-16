from PyTrilinos import Epetra, EpetraExt
from EpetraBpcg import bpcg
from scipy2Trilinos import scipy_csr_matrix2CrsMatrix
from numpy import load, nonzero
from scipy.sparse import csr_matrix
import numpy as np

def load_mat(filename):
    dic=load(filename)
    indp=dic['arr_0']
    indi=dic['arr_1']
    data=dic['arr_2']
    return csr_matrix((data,indi,indp))

def load_vec(filename):
    dic=load(filename)
    return dic['arr_0']

mycomm = Epetra.PyComm()
tps = Epetra.Time(mycomm)
tps.ResetStartTime()
#chargement fichier 
t1 = tps.WallTime()
As=load_mat("A.mat.npz")
t2 = tps.WallTime()
if (mycomm.MyPID() == 0):
   print 'tps load A = %.3es' %  (t2-t1)
t1 = tps.WallTime()
A=scipy_csr_matrix2CrsMatrix(As, mycomm)
t2 = tps.WallTime()
if (mycomm.MyPID() == 0):
   print 'size(A) = (%d,%d) nnz(A) = %d '  %(A.NumGlobalRows(), A.NumGlobalCols(), A.NumGlobalNonzeros())
   print 'tps convert A = %.3es' %  (t2-t1)

from scipy.sparse import spdiags

Bs=load_mat("H.mat.npz")
B=scipy_csr_matrix2CrsMatrix(Bs, mycomm)
Hs=load_mat("H.mat.npz")
Qhs=spdiags(np.ones((Hs.shape[0]), dtype='float'), 0, Hs.shape[0], Hs.shape[1]).tocsr()
Qh=scipy_csr_matrix2CrsMatrix(Qhs, mycomm)
H=scipy_csr_matrix2CrsMatrix(Hs, mycomm)

F = load_vec("F.mat.npz")
mpc=load_vec("mpc.mat.npz")
Qss=spdiags(1./mpc[:,0],(0),mpc.shape[0],mpc.shape[0]).tocsr()
Qs=scipy_csr_matrix2CrsMatrix(Qss, mycomm)

X=Epetra.Vector(A.DomainMap())
for i in range(X.MyLength()):
    X[i] = 0. 
# definition du second membre
Y=Epetra.Vector(A.RangeMap())
for ii in range(Y.MyLength()):
    i=  Y.Map().GID(ii)
    Y[ii] = F[i]
bpcg(H, B, Y, Qh, Qs, X, 1e-3, 10, True)
