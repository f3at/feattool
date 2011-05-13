from feat.common import decorator

from feattool.interfaces import *


_components = dict()


@decorator.simple_class
def register(component):
    component = IGuiComponent(component)
    if component.name is None:
        raise AttributeError('%r has None as name' % (component, ))
    if component.name in _components:
        raise AttributeError(
            'Component with name %s already registered, pointing to %r' %
            (component.name, _components[component.name], ))

    _components[component.name] = component


def query(name):
    return _components.get(name, None)


def get_all():
    return _components.values()
