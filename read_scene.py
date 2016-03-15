import json
import numpy as np


class bounds:
    def __init__(self, min_val, max_val, prec):
        self.min = min_val
        self.max = max_val
        self.div = int((max_val - min_val) // prec)


class graphdata:
    def __init__(self, datas):
        self.prec = datas["prec"]
        self.x = bounds(datas["xmin"], datas["xmax"], self.prec)
        self.y = bounds(datas["ymin"], datas["ymax"], self.prec)


class vect_interpreter:

    def paint_circle(X, Y, data, graphdata):
        center = data["center"]
        dists_sqr = (X - center[0]) ** 2 + (Y - center[1]) ** 2 #all this are matrices
        return dists_sqr < (data["radius"]**2) # here is the circle

    def paint_ring(X, Y, data, graphdata):
        center = data["center"]
        radius = data["radius"]
        thickness = data["thickness"]
        dists = np.abs(np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2) - radius) #all this are matrices
        return dists < thickness # here is the ring

    def paint_rect(X, Y, data, graphdata):
        return (X < data["xmax"]) * (Y < data["ymax"]) * \
               (X > data["xmin"]) * (Y > data["ymin"])

    def paint_sum(X, Y, data, graphdata):
        field = np.zeros(X.shape)
        for shape in data["content"]:
            field = np.logical_or( field,
                vect_interpreter.__shapes_types[shape["type"]](X, Y, shape, graphdata),
                                   out=field
            )
        return field

    __shapes_types = {"circle": paint_circle, "ring": paint_ring, "rect":paint_rect, "sum":paint_sum}

    def paint_uniform(X, Y, new_field, data, graphdata):
        if "density" in data: # se ha specificato la densità
            cell_charge = data["density"] * (graphdata.prec ** 2) #densità per area della cella
        else:
            cell_charge = 1 #densità standard... in genere riscalata
        return np.full(new_field.shape, cell_charge) #campo costante

    def paint_total(X, Y, new_field, data, graphdata):
        contained = vect_interpreter.__charges_fill[data["base"]["type"]]\
                            (X, Y, new_field, data["base"], graphdata) #base charge the shape
        if "offset" in data: # se ha specificato l'offset
            offset = data["offset"]   #spostamento per cella
        else:
            offset = (data["total"] - np.sum(contained * new_field)) / np.sum(new_field)
            #calcolo di quanto lo devo spostare (prima applico il gradiente, poi faccio l'offset totale,infine
            #divido per il numero di celle
        return contained + offset #spostiamo

    __charges_fill = {"uniform": paint_uniform,"shift":paint_total}

    def paint(self, content, graphdata, X, Y):
        field = np.zeros(X.shape)
        for shape in content:
            new_field = self.__shapes_types[shape["shape"]["type"]](X, Y, shape["shape"], graphdata) #fill the field with the shape
            new_field = new_field * \
                        self.__charges_fill[shape["charge"]["type"]]\
                            (X, Y, new_field, shape["charge"], graphdata) #charge the shape
            field += new_field
        return field

class charge_field:
    __paint_interpreters = {"vectorial":vect_interpreter}

    def __init__(self, datas, graph_setup):
        self.type = datas["type"]
        self.content = datas["content"]
        self.interpreter = self.__paint_interpreters[self.type]() #crea l'interprete
        self.graph_setup = graph_setup

    def paint(self, *indexes):
        return self.interpreter.paint(self.content, self.graph_setup, *indexes)



def read_scene(filename):
    with open(filename) as f:
        set_up = json.loads(f.read())
    graph_setup = graphdata(set_up["graphdata"])
    charges = charge_field(set_up["charges"], graph_setup) #gli servono i dati nel caso di una datamap
    return charges
