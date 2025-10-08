# HW 2 - NumPy Questions

# Q1.
import numpy as np

A = np.array([1,2,3],[4,5,6])
B = np.array([7,8,9],[10,11,12])

V = np.vstack((A, B))

H = np.hstack((A, B))

# Q2. 
common = np.intersect1d(A, B) 

# Q3. 
A[(A >= 1) & (A <= 5)]'

