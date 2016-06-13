print("Loading setups...")
import json
with open("assets/setup.json") as f:
    setup = json.load(f)

print("Benvenuti nel programma di simulazione del campo elettrico")

print("Selezionare la scena dalle scelte seguenti: ")


print("Loading scene...")
from read_scene import read_scene
scene = read_scene("scenes/"+setup["scene"])

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

def sqr_dist_matrix(step, dimx, dimy):
    x = np.arange(-dimx, dimx + 1) * step #+1 is for safety.. i doubt its usefullness
    y = np.arange(-dimy, dimy + 1) * step
    X, Y = np.meshgrid(x, y)
    sqr_dists = X ** 2 + Y ** 2
    return (X, Y, sqr_dists, np.sqrt(sqr_dists))

# L'idea è: calcoliamo tutto, poi transliamo di ciò che ci serve


print("    Creating duble base distance matrices...")
D_X, D_Y, sqr_D, D = sqr_dist_matrix(scene.graph_setup.prec, *data_shape) #squared int distance, D_matrix[datashape] is 0


print("    Preinverting and multiplying by k...")
k = 1/(4*np.pi*8.86e-12)
E_large = k / sqr_D #electric field
P_large = k / D     #electric potential
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

if setup["electric_field"]:
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

if setup["potential"]:
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

print("Calculating electric field module and charge density...")
E = np.sqrt(E_x ** 2 + E_y ** 2)
ChDist = Charge / (scene.graph_setup.prec**2)

print("Creating graphs...")
import plotly

with open("assets/graph_setups/charge_setup.json") as setup_file:
    charge_setup = json.load(setup_file)

charge_graph = plotly.graph_objs.Data([
    plotly.graph_objs.Contour(x=x, y=y, z=ChDist,
                           **charge_setup
                              )
])

if setup["electric_field"]:
    with open("assets/graph_setups/electric_field_setup.json") as setup_file:
        electric_field_setup = json.load(setup_file)

    electric_field_graph = plotly.tools.FigureFactory.create_streamline(
                                x,y,E_x,E_y,
                                name="Electrical field",
                                **electric_field_setup["streamline"]
                           )
    electric_field_graph["data"].append(plotly.graph_objs.Contour(x=x, y=y, z=E,
                                            contours=electric_field_setup["contours"],
                                            colorbar=electric_field_setup["colorbar"])
                                        )

if setup["potential"]:
    with open("assets/graph_setups/potential_setup.json") as setup_file:
        potential_setup = json.load(setup_file)

    potential_graph = plotly.graph_objs.Data([
        plotly.graph_objs.Contour(x=x, y=y, z=P,
                               **potential_setup
                                  )
    ])



print("Showing off my result...")
import os
if not os.path.exists("output"):
    os.mkdir("output")

plotly.offline.plot(charge_graph, filename='output/ChargeField.html')

if setup["electric_field"]:
    plotly.offline.plot(electric_field_graph, filename="output/ElectricField.html")

if setup["potential"]:
    plotly.offline.plot(potential_graph, filename='output/PotentialField.html')



