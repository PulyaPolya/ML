import tensorflow as tf
from keras.datasets import fashion_mnist
import keras
import functions as f
import numpy as np
from tensorflow.keras import layers

import keras_tuner as kt
from tensorflow import keras
import sys
import threading
from time import sleep

try:
    import thread
except ImportError:
    import _thread as thread
try:
    range, _print = xrange, print
    def print(*args, **kwargs):
        flush = kwargs.pop('flush', False)
        _print(*args, **kwargs)
        if flush:
            kwargs.get('file', sys.stdout).flush()
except NameError:
    pass
def quit_function(fn_name):
    # print to stderr, unbuffered in Python 2.
    print('{0} took too long'.format(fn_name), file=sys.stderr)
    sys.stderr.flush() # Python 3 stderr is likely buffered.
    thread.interrupt_main() # raises KeyboardInterrupt
def exit_after(s):
    '''
    use as decorator to exit process if
    function takes longer than s seconds
    '''
    def outer(fn):
        def inner(*args, **kwargs):
            timer = threading.Timer(s, quit_function, args=[fn.__name__])
            timer.start()
            try:
                result = fn(*args, **kwargs)
            finally:
                timer.cancel()
            return result
        return inner
    return outer

num_classes = 10
input_shape = (28, 28, 1)
tf.random.set_seed(1234)
(x_train, y_train), (x_test, y_test) = fashion_mnist.load_data()
x_train, y_train, x_test, y_test = f.edit_data(x_train, y_train, x_test, y_test)
size_data = x_train.shape[0]
batch_size = 64
epochs =9
class Epoch_Tracker:
  def __init__(self):
     self.epoch = 0
     self.change = True
  def increase(self):
    self.epoch +=1
    self.change = True

def random_invert_img(x):
  #print(epoch_track.epoch)
  if epoch_track.epoch >= epochs:
     return x
  x_temp = x.numpy()
  x_temp = x_temp.reshape(x_temp.shape[0], 28,28)
  x_shifted = []
  for image in x_temp:
       x_shifted.append(f.shift_image_np(image))
  x_shifted = np.array(x_shifted)

  x_result = x_shifted.reshape(x_temp.shape[0],28,28,1)

  return x_result
def random_invert():
  return layers.Lambda(lambda x: random_invert_img(x))

random_invert = random_invert()
class RandomInvert(layers.Layer):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)

  def call(self, x):
    return random_invert_img(x)

epoch_track = Epoch_Tracker()
tf.random.set_seed(92)
def model_builder(hp):
    model = keras.Sequential()
    hp_units1 = hp.Int('conv1', min_value=40, max_value=140, step=1)
    hp_units2 = hp.Int('conv2', min_value=40, max_value=100, step=1)
    hp_units3 = hp.Int('conv3', min_value=32, max_value=80, step=1)
    hp_drop1 = hp.Int('drop1', min_value=3, max_value=6, step=1)
    hp_drop2 = hp.Int('drop2', min_value=3, max_value=6, step=1)
    hp_kernel_size1 = hp.Int('kernel_size1', min_value=3, max_value=7, step=2)
    hp_kernel_size2 = hp.Int('kernel_size2', min_value=3, max_value=9, step=2)
    hp_kernel_size3 = hp.Int('kernel_size3', min_value=3, max_value=15, step=2)


    model.add(RandomInvert())
    model.add(keras.layers.Conv2D(filters = hp_units1,  kernel_size=(hp_kernel_size1, hp_kernel_size1), padding='same', activation='relu', input_shape=input_shape))
    model.add(keras.layers.Conv2D(filters = hp_units2,  kernel_size=(hp_kernel_size2, hp_kernel_size2), padding='same', activation='relu'))
    model.add(keras.layers.MaxPool2D())
    model.add(keras.layers.Dropout(hp_drop1/10))
    model.add(keras.layers.Conv2D(filters = hp_units3,  kernel_size=(hp_kernel_size3, hp_kernel_size3), padding='same', activation='relu'))
    model.add(keras.layers.Dropout(hp_drop2/10))
    model.add(keras.layers.Flatten())
    model.add(keras.layers.Dense(num_classes, activation = 'softmax'))
    hp_learning_rate = hp.Choice('learning rate', values=list(range(5,15)))

    hp_optimizer = hp.Choice('optimizer', values=['adam', 'nadam', 'rmsprop'])
    if hp_optimizer == 'adam':
        optimizer = tf.keras.optimizers.Adam(learning_rate=hp_learning_rate / 10000)
    elif hp_optimizer == 'nadam':
        optimizer = tf.keras.optimizers.Nadam(learning_rate=hp_learning_rate / 10000)
    elif hp_optimizer == 'rmsprop':
        optimizer = tf.keras.optimizers.RMSprop(learning_rate=hp_learning_rate / 10000)


    model.compile(optimizer= optimizer,
                loss='categorical_crossentropy',
                metrics=['acc'], run_eagerly=True)

    return model
@exit_after(28800)
def run_search():
    tuner = kt.RandomSearch(model_builder,
                         objective='val_acc',
                         max_trials= 100,
                         directory='random_search',
                         project_name='random_search')


    early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_acc', patience=5, baseline=0.7)
    tuner.search(x_train, y_train, epochs=9, validation_split=0.1, callbacks=[early_stop])

    # Get the optimal hyperparameters
    best_hps=tuner.get_best_hyperparameters(num_trials=1)[0]
run_search()
# print(f"""
# The hyperparameter search is complete. The optimal number of units in the first layer is conv1
# {best_hps.get('conv1')} and  conv2  {best_hps.get('conv2')} and
#   conv3  {best_hps.get('conv3')} and  dropu is  {best_hps.get('dense')}'.
# """)
# model = tuner.hypermodel.build(best_hps)
# history = model.fit(x_train, y_train, epochs=100, validation_split=0.1, callbacks = callbacks_list)
#
# test_loss, test_acc = model.evaluate(x_test, y_test)
#
# history_dict = history.history
# # Save it under the form of a json file
# json.dump(history_dict, open('saved_history_cnn_hyperband', 'w'))

