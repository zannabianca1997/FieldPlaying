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
print("Total charge: {}".format(np.sum(Charge)))

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


print("    Preinverting and multiplying by k...")
k = 1/(4*np.pi*8.86e-12)
E_matrix = k / sqr_D_matrix #electric field
P_matrix = k / D_matrix     #electric potential
print("    Erasing infinite center value...")
E_matrix[data_shape] = 0
P_matrix[data_shape] = 0
print("    Calculating vector components")
E_X_matrix = np.nan_to_num(E_matrix * (int_D_X_matrix * scene.graph_setup.prec / D_matrix) )
E_Y_matrix = np.nan_to_num(E_matrix * (int_D_Y_matrix * scene.graph_setup.prec / D_matrix) )


print("    Creating slicing arrays...")
#slices array
slices_array = [ #per tutte le linee
                [ # e per turre le colonne
                    ( #crea una tupla con dentro
                        slice(data_shape[0] - x, 2*data_shape[0] - x),
                        slice(data_shape[1] - y, 2*data_shape[1] - y)
                    )
                for y in range(data_shape[1])
                ]
            for x in range(data_shape[0])
            ]
#precalcolo di ogni matrice

#EX_factor_index,EY_factor_index,P_factor_index = 0,1,2

        #            ( #crea una tupla con dentro
         #               E_X_matrix[matrices[x][y]], #0: distance from cell in X axis
          #              E_Y_matrix[matrices[x][y]], #1: distance from cell in Y axis
           #             P_matrix[matrices[x][y]]    #2: electrical potential factor
            #        )

print("Creating starting zero fields...")
E_x = np.zeros(data_shape)
E_y = np.zeros(data_shape) #all separate
P = np.zeros(data_shape)

#needed for progress bars
steps = cellnum // setup["progress_bar_len"]

if setup["field"]["calculate"]:
    print("Calculating electrical field ", end="") #not creating newline
    count = 0
    for ix in range(data_shape[0]):
        for iy in range(data_shape[1]):
            if Charge[ix,iy] != 0:
                E_x += E_X_matrix[slices_array[ix][iy]] * Charge[ix,iy] #Electrical field of this cell
                E_y += E_Y_matrix[slices_array[ix][iy]] * Charge[ix,iy]
            count += 1
            if count%steps == 0:
                print(".",end="")
    print(" Done!")

if setup["potential"]["calculate"]:
    print("Calculating potential ", end="") #not creating newline
    count = 0
    for ix in range(data_shape[0]):
        for iy in range(data_shape[1]):
            if Charge[ix,iy] != 0:
                P += P_matrix[slices_array[ix][iy]] * Charge[ix,iy] #potential of this cell
            count += 1
            if count%steps == 0:
                print(".",end="")
    print(" Done!")

print("Removing Nan values...")
E_x = np.nan_to_num(E_x)
E_y = np.nan_to_num(E_y)
P = np.nan_to_num(P)

print("Showing off my result...")
import plotly
plotly.offline.plot(plotly.graph_objs.Data([
    plotly.graph_objs.Contour(x=x, y=y, z=(Charge / (scene.graph_setup.prec**2)),
                           contours=dict(
                                coloring='heatmap'
                           ),
                           colorbar=dict(
                                ticksuffix = "C/m^2"
                            ))]), filename='ChargeField.html')
if setup["field"]["calculate"]:
    fig = plotly.tools.FigureFactory.create_streamline(
                        x,y,E_x,E_y,
                        arrow_scale=setup["field"]["arrowscale"],
                        density = setup["field"]["density"],
                        name="Electrical field"
                    )
    fig["data"].append(plotly.graph_objs.Contour(x=x, y=y, z=np.sqrt(E_x ** 2 + E_y ** 2),
                           contours=dict(
                                coloring='heatmap'
                           ),
                           colorbar=dict(
                                ticksuffix = "N/C"
                            )))
    plotly.offline.plot(fig, filename="ElectricField.html")

if setup["potential"]["calculate"]:
    plotly.offline.plot(plotly.graph_objs.Data([
        plotly.graph_objs.Contour(x=x, y=y, z=P,
                           contours=dict(
                                coloring='heatmap'
                           ),
                           colorbar=dict(
                                ticksuffix = "V"
                            ))]), filename='PotentialField.html')



