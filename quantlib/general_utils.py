# This is a utility file that allow us to perform simple tasks such as I/O, disk writing, etc.

import pickle


def save_file(path, object):
    try:
        with open(path, "wb") as fp:
            pickle.dump(object, fp)
    except Exception as err:
        print("pickle error: ", str(err))


def load_file(path):
    try:
        with open(path, "rb") as fp:
            file = pickle.load(fp)
        return file
    except Exception as err:
        print("load error", str(err))
