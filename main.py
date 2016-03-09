from read_scene import read_scene

print("Loading setups...")
#eventual general setups
print("Loading scene...")
scene = read_scene("ch_dist_1.json")

import numpy as np
print("Creating base coordinate matrix...")
x = np.linspace(scene.graph_setup.x.min, scene.graph_setup.x.max, scene.graph_setup.x.div)
y = np.linspace(scene.graph_setup.y.min, scene.graph_setup.y.max, scene.graph_setup.y.div)
X, Y = np.meshgrid(x, y)
data_shape=X.shape
print("Data shape setted to {}".format(data_shape))

print("Creating scene...")
Charge = scene.paint(X, Y)

print("Creating starting zero fields...")
E_x = np.zeros(data_shape)
E_y = np.zeros(data_shape) #all separate
P = np.zeros(data_shape)

print("Creating distance matrix...")


def dist_matrix(dimx, dimy):
    print("    Creating duble base coordinate matrix...")
    x = np.arange(-dimx, dimx + 1)
    y = np.arange(-dimy, dimy + 1)
    X, Y = np.meshgrid(x, y)
    return np.sqrt(X ** 2 + Y ** 2)

D_matrix = dist_matrix(*data_shape) * scene.graph_setup.prec #distance, cell [datashape] is 0

def blit(dest, src, loc): #blit function
    pos = [i if i >= 0 else None for i in loc] #valori positivi
    neg = [-i if i < 0 else None for i in loc] #valori negativi
    target = dest[[slice(i,None) for i in pos]]  #prende la parte in cui copiare, tagliando dai positivi in su
    src = src[[slice(i, j) for i,j in zip(neg, target.shape)]]  #taglia solo la parte da copiare
    target[[slice(None, i) for i in src.shape]] = src #copia quella parte
    return dest

import plotly
plotly.offline.plot(plotly.graph_objs.Data([
    plotly.graph_objs.Contour(x=x, y=y, z=(Charge / (scene.graph_setup.prec**2) ),
                           contours=dict(
                                coloring='heatmap'
                           ),
                           colorbar=dict(
                                thickness=25,
                                thicknessmode='pixels',
                                len=0.5,
                                lenmode='fraction',
                                outlinewidth=0,
                                ticksuffix = "C/m^2"
                            ))]), filename='TestFile.html')



