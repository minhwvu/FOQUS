import os
import numpy as np
import pandas as pd
import random as rn
import tensorflow as tf

# set seed values for reproducibility
os.environ["PYTHONHASHSEED"] = "0"
os.environ[
    "CUDA_VISIBLE_DEVICES"
] = ""  # changing "" to "0" or "-1" may solve import issues
np.random.seed(46)
rn.seed(1342)
tf.random.set_seed(62)

# Example follows the sequence below:
# 1) Code at end of file to import data and create model
# 2) Call create_model() to define inputs and outputs
# 3) Call CustomLayer to define network structure, which uses
#    call() to define layer connections and get_config to attach
#    attributes to CustomLayer class object
# 4) Back to create_model() to compile and train model
# 5) Back to code at end of file to save, load and test model

# custom class to define Keras NN layers
@tf.keras.utils.register_keras_serializable()
class mea_column_model(tf.keras.layers.Layer):
    def __init__(
        self,
        n_hidden=1,
        n_neurons=12,
        layer_act="relu",
        out_act="sigmoid",
        input_labels=None,
        output_labels=None,
        input_bounds=None,
        output_bounds=None,
        normalized=False,
        **kwargs
    ):

        super(mea_column_model, self).__init__()  # create callable object

        # add attributes from training settings
        self.n_hidden = n_hidden
        self.n_neurons = n_neurons
        self.layer_act = layer_act
        self.out_act = out_act

        # add attributes from model data
        self.input_labels = input_labels
        self.output_labels = output_labels
        self.input_bounds = input_bounds
        self.output_bounds = output_bounds
        self.normalized = True  # FOQUS will read this and adjust accordingly

        # create lists to contain new layer objects
        self.dense_layers = []  # hidden or output layers
        self.dropout = []  # for large number of neurons, certain neurons
        # can be randomly dropped out to reduce overfitting

        for layer in range(self.n_hidden):
            self.dense_layers.append(
                tf.keras.layers.Dense(self.n_neurons, activation=self.layer_act)
            )

        self.dense_layers_out = tf.keras.layers.Dense(2, activation=self.out_act)

    # define network layer connections
    def call(self, inputs):

        x = inputs  # single input layer, input defined in create_model()
        for layer in self.dense_layers:  # hidden layers
            x = layer(x)  # h1 = f(input), h2 = f(h1), ... using act func
        for layer in self.dropout:  # no dropout layers used in this example
            x = layer(x)
        x = self.dense_layers_out(x)  # single output layer, output = f(h_last)

        return x

    # attach attributes to class CONFIG
    def get_config(self):
        config = super(mea_column_model, self).get_config()
        config.update(
            {
                "n_hidden": self.n_hidden,
                "n_neurons": self.n_neurons,
                "layer_act": self.layer_act,
                "out_act": self.out_act,
                "input_labels": self.input_labels,
                "output_labels": self.output_labels,
                "input_bounds": self.input_bounds,
                "output_bounds": self.output_bounds,
                "normalized": self.normalized,
            }
        )
        return config


# method to create model
def create_model(data):

    inputs = tf.keras.Input(shape=(np.shape(data)[1],))  # create input layer

    layers = mea_column_model(  # define the rest of network using our custom class
        input_labels=xlabels,
        output_labels=zlabels,
        input_bounds=xdata_bounds,
        output_bounds=zdata_bounds,
        normalized=True,
    )

    outputs = layers(inputs)  # use network as function outputs = f(inputs)

    model = tf.keras.Model(inputs=inputs, outputs=outputs)  # create model

    model.compile(loss="mse", optimizer="RMSprop", metrics=["mae", "mse"])

    model.fit(xdata, zdata, epochs=500, verbose=0)  # train model

    return model


# Main code

# import data
data = pd.read_csv(r"MEA_carbon_capture_dataset_mimo.csv")

xdata = data.iloc[:, :6]  # there are 6 input variables/columns
zdata = data.iloc[:, 6:]  # the rest are output variables/columns
xlabels = xdata.columns.tolist()  # set labels as a list (default) from pandas
zlabels = zdata.columns.tolist()  #    is a set of IndexedDataSeries objects
xdata_bounds = {i: (xdata[i].min(), xdata[i].max()) for i in xdata}  # x bounds
zdata_bounds = {j: (zdata[j].min(), zdata[j].max()) for j in zdata}  # z bounds

# normalize data
xmax, xmin = xdata.max(axis=0), xdata.min(axis=0)
zmax, zmin = zdata.max(axis=0), zdata.min(axis=0)
xdata, zdata = np.array(xdata), np.array(zdata)
for i in range(len(xdata)):
    for j in range(len(xlabels)):
        xdata[i, j] = (xdata[i, j] - xmin[j]) / (xmax[j] - xmin[j])
    for j in range(len(zlabels)):
        zdata[i, j] = (zdata[i, j] - zmin[j]) / (zmax[j] - zmin[j])

model_data = np.concatenate(
    (xdata, zdata), axis=1
)  # Keras requires a Numpy array as input

# define x and z data, not used but will add to variable dictionary
xdata = model_data[:, :-2]
zdata = model_data[:, -2:]

# create model
model = create_model(xdata)
model.summary()

# save model
model.save("mea_column_model.h5")
