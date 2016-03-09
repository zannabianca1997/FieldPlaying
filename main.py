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

print("Creating distance matrices...")

def sqr_dist_matrix(dimx, dimy):
    x = np.arange(-dimx, dimx + 1) #+1 is for safety.. i doubt its usefullness
    y = np.arange(-dimy, dimy + 1)
    X, Y = np.meshgrid(x, y)
    return (X, Y, X ** 2 + Y ** 2)

# L'idea è: calcoliamo tutto, poi transliamo di ciò che ci serve


print("    Creating duble base distance matrices...")
int_D_X_matrix, int_D_Y_matrix, int_D_matrix = sqr_dist_matrix(*data_shape) #squared int distance, D_matrix[datashape] is 0

sqr_D_matrix = int_D_matrix * (scene.graph_setup.prec**2) #distance squared
D_matrix = np.sqrt(int_D_matrix) * scene.graph_setup.prec #distance, i multiply here for precision sake

D_X_matrix = int_D_X_matrix * scene.graph_setup.prec
D_Y_matrix = int_D_Y_matrix * scene.graph_setup.prec


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

E_X_factor_index,E_Y_factor_index,E_factor_index,P_factor_index = 0,1,2,3

matrices = [ #per tutte le linee
                [ # e per turre le colonne
                    ( #crea una tupla con dentro
                        D_matrix[matrices[x][y]] / D_X_matrix[matrices[x][y]], #0: distance from cell in X axis
                        D_matrix[matrices[x][y]] / D_Y_matrix[matrices[x][y]], #1: distance from cell in Y axis
                        E_matrix[matrices[x][y]],                              #2: electrical field factor
                        P_matrix[matrices[x][y]]                               #3: electrical potential factor
                    )
                for y in range(data_shape[1])
                ]
            for x in range(data_shape[0])
            ]

print("Creating starting zero fields...")
E_x = np.zeros(data_shape)
E_y = np.zeros(data_shape) #all separate
P = np.zeros(data_shape)

#needed for progress bars
steps = cellnum // setup["progress_bar_len"]

print("Calculating electrical field ", end="") #not creating newline
count = 0
for ix in range(data_shape[0]):
    for iy in range(data_shape[1]):
        E = matrices[ix][iy][E_factor_index] * Charge[ix,iy] #Electrical field of this cell
        E_x += E * matrices[ix][iy][E_X_factor_index]
        E_y += E * matrices[ix][iy][E_Y_factor_index]
        count += 1
        if count%steps == 0:
            print(".",end="")
print(" Done!")

print("Calculating potential ", end="") #not creating newline
count = 0
for ix in range(data_shape[0]):
    for iy in range(data_shape[1]):
        P += matrices[ix][iy][P_factor_index] * Charge[ix,iy] #potential of this cell
        count += 1
        if count%steps == 0:
            print(".",end="")
print(" Done!")


print("Showing off my result...")
import plotly
plotly.offline.plot(plotly.graph_objs.Data([
    plotly.graph_objs.Contour(x=x, y=y, z=(Charge / (scene.graph_setup.prec**2)),
                           contours=dict(
                                coloring='heatmap'
                           ),
                           colorbar=dict(
                                ticksuffix = "C/m^2"
                            ))]), filename='TestChargeFile.html')
plotly.offline.plot(plotly.graph_objs.Data([
    plotly.graph_objs.Contour(x=x, y=y, z=P,
                           contours=dict(
                                coloring='heatmap'
                           ),
                           colorbar=dict(
                                ticksuffix = "V"
                            ))]), filename='TestPotentialFile.html')



