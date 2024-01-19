import pickle


def save_file(path, object):
    """
    This function is used to save(serialize) an object to a file
    using the 'pickle' module in Python
    """
    try:
        with open(path, "wb") as fp:
            pickle.dump(object, fp)
    except Exception as err:
        print("pickle error: ", str(err))


def load_file(path):
    """
    This function is used to load(deserialize) an
    object from a file using 'pickle' module
    """
    try:
        with open(path, "rb") as fp:
            file = pickle.load(fp)
        return file
    except Exception as err:
        print("load error", str(err))
