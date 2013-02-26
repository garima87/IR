import scipy
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
from numpy.linalg import solve, norm
from numpy.random import rand

l = ['garima', 'agarwal']
A = lil_matrix((len(l), 1000))

A[0,6] = 1
