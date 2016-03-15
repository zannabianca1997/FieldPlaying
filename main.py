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

def sqr_dist_matrix(dimx, dimy, step):
    x = np.arange(-dimx, dimx + 1) * step #+1 is for safety.. i doubt its usefullness
    y = np.arange(-dimy, dimy + 1) * step
    X, Y = np.meshgrid(x, y)
    sqr_dists = X ** 2 + Y ** 2
    return (X, Y, sqr_dists, np.sqrt(sqr_dists))

# L'idea è: calcoliamo tutto, poi transliamo di ciò che ci serve


print("    Creating duble base distance matrices...")
D_X, D_Y, sqr_D, D = sqr_dist_matrix(*data_shape, scene.graph_setup.prec) #squared int distance, D_matrix[datashape] is 0


print("    Preinverting and multiplying by k...")
k = 1/(4*np.pi*8.86e-12)
E_large = k / D #electric field
P_large = k / np.sqrt(D)     #electric potential
print("    Erasing infinite center value...")
E_large[data_shape] = 0
P_large[data_shape] = 0
print("    Calculating vector components")
E_X_large = np.nan_to_num(E_large * (D_X / D) )
E_Y_large = np.nan_to_num(E_large * (D_Y / D) )


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
                E_x += E_X_large[slices_array[ix][iy]] * Charge[ix,iy] #Electrical field of this cell
                E_y += E_Y_large[slices_array[ix][iy]] * Charge[ix,iy]
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
                P += P_large[slices_array[ix][iy]] * Charge[ix,iy] #potential of this cell
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



