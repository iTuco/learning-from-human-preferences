import tensorflow as tf

from nn_layers import dense_layer, conv_layer
from utils import get_dot_position


def net_moving_dot_features(s, reuse):
    a = s[:, 0, 0, -1] - 100
    a = tf.cast(a, tf.float32) / 4.0

    xc, yc = get_dot_position(s)
    xc = tf.cast(xc, tf.float32) / 83.0
    yc = tf.cast(yc, tf.float32) / 83.0

    features = [a, xc, yc]
    x = tf.stack(features, axis=1)

    x = dense_layer(x, 64, "d1", reuse, activation='relu')
    x = dense_layer(x, 64, "d2", reuse, activation='relu')
    x = dense_layer(x, 64, "d3", reuse, activation='relu')
    x = dense_layer(x, 1, "d4", reuse, activation=None)
    x = x[:, 0]

    return x


def net_cnn(s, batchnorm, dropout, training, reuse):
    # Page 15:
    # "[The] input is fed through 4 convolutional layers of size 7x7, 5x5, 3x3,
    # and 3x3 with strides 3, 2, 1, 1, each having 16 filters, with leaky ReLU
    # nonlinearities (α = 0.01). This is followed by a fully connected layer of
    # size 64 and then a scalar output. All convolutional layers use batch norm
    # and dropout with α = 0.5 to prevent predictor overfitting"
    x = s / 255.0

    x = conv_layer(x, 16, 7, 3, batchnorm, training, "c1", reuse, 'relu')
    # NB specifying seed is important because both legs of the network should
    # dropout in the same way.
    # TODO: this still isn't completely right; we should set noise_shape for
    # same dropout on all steps
    x = tf.layers.dropout(x, dropout, training=training, seed=0)
    x = conv_layer(x, 16, 5, 2, batchnorm, training, "c2", reuse, 'relu')
    x = tf.layers.dropout(x, dropout, training=training, seed=1)
    x = conv_layer(x, 16, 3, 1, batchnorm, training, "c3", reuse, 'relu')
    x = tf.layers.dropout(x, dropout, training=training, seed=2)
    x = conv_layer(x, 16, 3, 1, batchnorm, training, "c4", reuse, 'relu')

    w, h, c = x.get_shape()[1:]
    x = tf.reshape(x, [-1, int(w * h * c)])

    x = dense_layer(x, 64, "d1", reuse, activation='relu')
    x = dense_layer(x, 1, "d2", reuse, activation=None)
    x = x[:, 0]

    return x


def reward_pred_net(network, s, dropout, batchnorm, reuse, training):
    if network == 'moving_dot_features':
        return net_moving_dot_features(s, reuse)
    elif network == 'cnn':
        return net_cnn(s, batchnorm, dropout, training, reuse)
    else:
        raise Exception("Unknown reward predictor network architecture",
                        network)