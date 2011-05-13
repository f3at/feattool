import os

import feattool


def path(*path):
    return os.path.join(feattool.__path__[0], 'data', *path)
