import os
import tempfile


def detex(file_path: str):

    tf = tempfile.NamedTemporaryFile()
    print('filename: ' + tf.name)
    os.popen('detex' + ' ' + file_path + ' > ' + tf.name)
    os.popen('touch ' + tf.name)

    return tf
