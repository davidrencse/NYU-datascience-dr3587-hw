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
A_in_range = A[(A >= 1) & (A <= 5)]

# Q4.
url = 'https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data'
iris_2d = np.genfromtxt(url, delimiter=',', dtype='float', usecols=[0,1,2,3])
cond = (iris_2d[:, 2] > 1.5) & (iris_2d[:, 0] < 5.0)

# HW 2 - Pandas Questions

# Q1.
import pandas as pd

df = pd.read_csv('https://raw.githubusercontent.com/selva86/datasets/master/Cars93_miss.csv')
every_20th = df.loc[::20, ['Manufacturer', 'Model', 'Type']]

# Q2.

df = pd.read_csv('https://raw.githubusercontent.com/selva86/datasets/master/Cars93_miss.csv')
cols = ['Min.Price', 'Max.Price']
df[cols] = df[cols].fillna(df[cols].mean())

# Q3.
df2 = pd.DataFrame(np.random.randint(10, 40, 60).reshape(-1, 4))
rows_sum_gt_100 = df2[df2.sum(axis=1) > 100]


