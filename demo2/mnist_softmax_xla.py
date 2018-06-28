import argparse
import sys
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
from tensorflow.python.client import timeline

FLAGS = None

def main(_):
    # Import data
    mnist = input_data.read_data_sets(FLAGS.data_dir)

    x = tf.placeholder(tf.float32, [None, 784])
    W = tf.Variable(tf.zeros([784, 10]))
    b = tf.Variable(tf.zeros([10]))
    y = tf.matmul(x, W) + b

    y_ = tf.placeholder(tf.int64, [None])

    cross_entropy = tf.losses.sparse_softmax_cross_entropy(labels=y_, logits=y)
    train_step = tf.train.GradientDescentOptimizer(0.5).minimize(cross_entropy)

    config = tf.ConfigProto()
    jit_level = 0
    if FLAGS.xla:
        jit_level = tf.OptimizerOptions.ON_1

    config.graph_options.optimizer_options.global_jit_level = jit_level
    run_metadata = tf.RunMetadata()
    sess = tf.Session(config=config)
    tf.global_variables_initializer().run(session=sess)

    # Train
    train_loops = 1000
    for i in range(train_loops):
        batch_xs, batch_ys = mnist.train.next_batch(100)
        if i == train_loops - 1:
            sess.run(
                train_step,
                feed_dict={
                    x:batch_xs,
                    y_:batch_ys
                },
                options=tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE),
                run_metadata=run_metadata
            )
            trace = timeline.Timeline(step_stats=run_metadata.step_stats)
            with open('timeline.ctf.json', 'w') as trace_file:
                trace_file.write(trace.generate_chrome_trace_format())
        else:
            sess.run(train_step, feed_dict={x:batch_xs, y_:batch_ys})

    # Test
    correct_prediction = tf.equal(tf.argmax(y, 1), y_)
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
    print(sess.run(
        accuracy,
        feed_dict={
            x:mnist.test.images,
            y_:mnist.test.labels
        }
    ))
    sess.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--data_dir',
        type=str,
        default='/tmp/tensorflow/mnist/input_data',
        help='Directory for storing input data'
    )
    parser.add_argument(
        '--xla',
        type=bool,
        default=True,
        help='Turn xla via JIT on'
    )
    FLAGS, unparsed = parser.parse_known_args()
    tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)