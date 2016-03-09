print("Loading setups...")
import json
with open("setup.json") as f:
        setup = json.loads(f.read())

print("Loading scene...")
from read_scene import read_scene
scene = read_scene("ch_dist_1.json")

import numpy as np
print("Creating base coordinate matrix...")
x = np.linspace(scene.graph_setup.x.min, scene.graph_setup.x.max, scene.graph_setup.x.div)
y = np.linspace(scene.graph_setup.y.min, scene.graph_setup.y.max, scene.graph_setup.y.div)
X, Y = np.meshgrid(x, y)
data_shape=X.shape
cellnum= data_shape[0]*data_shape[1]
print("Data shape setted to {}, simulating {} cells".format(data_shape, cellnum))

print("Creating scene...")
Charge = scene.paint(X, Y)

print("Creating distance matrix...")

def sqr_dist_matrix(dimx, dimy):
    x = np.arange(-dimx, dimx + 1) #+1 is for safety.. i doubt its usefullness
    y = np.arange(-dimy, dimy + 1)
    X, Y = np.meshgrid(x, y)
    return X ** 2 + Y ** 2

print("    Creating duble base distance matrices...")
int_D_matrix = sqr_dist_matrix(*data_shape) #squared int distance, D_matrix[datashape] is 0
sqr_D_matrix = int_D_matrix * (scene.graph_setup.prec**2) #distance squared
D_matrix = np.sqrt(int_D_matrix) * scene.graph_setup.prec #distance, i multiply here for precision sake


print("    Preinverting and multiplying by k...")
k = 1/(4*np.pi*8.86e-12)
E_matrix = k / sqr_D_matrix #electric field
P_matrix = k / D_matrix     #electric potential
print("    Erasing infinite center value...")
E_matrix[data_shape] = 0
P_matrix[data_shape] = 0

print("    Creating slicing arrays...")
#slices array
matrices = [ #per tutte le linee
                [ # e per turre le colonne
                    ( #crea una tupla con dentro
                        slice(x, x + data_shape[0]),
                        slice(y, y + data_shape[1])
                    )
                for y in range(data_shape[1])
                ]
            for x in range(data_shape[0])
            ]
#precalcolo di ogni matrice
matrices = [ #per tutte le linee
                [ # e per turre le colonne
                    ( #crea una tupla con dentro
                        E_matrix[matrices[x][y]],
                        P_matrix[matrices[x][y]]
                    )
                for y in range(data_shape[1])
                ]
            for x in range(data_shape[0])
            ]

print("Creating starting zero fields...")
E_x = np.zeros(data_shape)
E_y = np.zeros(data_shape) #all separate
P = np.zeros(data_shape)

print("Calculating potential ", end="") #not creating newline
steps = cellnum // setup["progress_bar_len"]
count = 0
for ix in range(data_shape[0]):
    for iy in range(data_shape[1]):
        P += matrices[ix][iy][1] * Charge[ix,iy]
        count += 1
        if count%steps == 0:
            print(".",end="")
print(" Done!")


print("Showing off my result...")
import plotly
plotly.offline.plot(plotly.graph_objs.Data([
    plotly.graph_objs.Contour(x=x, y=y, z=P,
                           contours=dict(
                                coloring='heatmap'
                           ),
                           colorbar=dict(
                                ticksuffix = "V"
                            ))]), filename='TestFile.html')



