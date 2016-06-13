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

    # loading defaults value for shapes and charges
    with open("./assets/shapes_defaults.json") as f:
        shapes_defaults = json.loads(f.read())
    with open("./assets/charges_defaults.json") as f:
        charges_defaults = json.loads(f.read())

    def paint_circle(X, Y, data):
        center = data["center"]
        dists_sqr = (X - center[0]) ** 2 + (Y - center[1]) ** 2 #all this are matrices
        return dists_sqr < (data["radius"]**2) # here is the circle

    def paint_ring(X, Y, data):
        center = data["center"]
        radius = data["radius"]
        thickness = data["thickness"]
        dists = np.abs(np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2) - radius) #all this are matrices
        return dists < thickness # here is the ring

    def paint_rect(X, Y, data):
        return (X < data["xmax"]) * (Y < data["ymax"]) * \
               (X > data["xmin"]) * (Y > data["ymin"])

    def paint_sum(X, Y, data):
        field = np.zeros(X.shape)
        for shape in data["content"]:
            np.logical_or( field, vect_interpreter.__getshape(X, Y, shape), out=field)
        return field

    __shapes_types = {"circle": paint_circle, "ring": paint_ring, "rect":paint_rect, "sum":paint_sum}

    def __getshape(X, Y, data):
        for field in vect_interpreter.shapes_defaults[data["type"]]:
            if not field in data:
                data[field] = vect_interpreter.shapes_defaults[data["type"]][field]
        return vect_interpreter.__shapes_types[data["type"]](X, Y, data)

    def paint_uniform(X, Y, new_field, data, graphdata):
        cell_charge = data["density"] * (graphdata.prec ** 2) #densità per area della cella
        return np.full(new_field.shape, cell_charge) #campo costante

    def paint_shift(X, Y, new_field, data, graphdata):
        contained = vect_interpreter.__getcharge(X, Y, new_field, data["base"], graphdata) #base charge the shape
        offset = data["offset"]   #spostamento per cella
        return contained + offset #spostiamo

    def paint_void(X, Y, new_field, data, graphdata):
        return np.zeros(X.shape) #just a blank gradient

    def paint_total(X, Y, new_field, data, graphdata):
        contained = vect_interpreter.__getcharge(X, Y, new_field, data["base"], graphdata) #base charge the shape
        if data["method"] == "shift":
            offset = (data["total"] - np.sum(contained * new_field)) / np.sum(new_field)# si va di spostamento
            return contained + offset #spostiamo
            #calcolo di quanto lo devo spostare (prima applico il gradiente, poi faccio l'offset totale,infine
            #divido per il numero di celle
        elif data["method"] == "factor":
            factor = data["total"] / np.sum(contained * new_field)
            return contained * factor #riscaliamo
        else:
            raise Exception("total 'method' must be 'shift' or 'factor'") #TODO:polish graphdata mess

    __charges_fill = {"uniform": paint_uniform,"shift":paint_shift,"void":paint_void,"total":paint_total}
    def __getcharge(X, Y, shape_field, charge, graphdata):
        for field in vect_interpreter.charges_defaults[charge["type"]]:
            if not field in charge:
                charge[field] = vect_interpreter.charges_defaults[charge["type"]][field]
        return vect_interpreter.__charges_fill[charge["type"]] (X, Y, shape_field, charge, graphdata)

    def paint(self, content, graphdata, X, Y):
        field = np.zeros(X.shape)
        for object in content:
            shape_field = vect_interpreter.__getshape(X, Y, object["shape"]) #fill the field with the shape
            charge_field = vect_interpreter.__getcharge(X, Y, shape_field, object["charge"], graphdata) #charge the shape
            field += shape_field * charge_field
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
