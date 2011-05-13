import gtk

from zope.interface import classProvides

from feat.common import log

from feattool.core import driver, component
from feattool.gui import simulation

from feattool.interfaces import *


@component.register
class SimulationComponent(log.LogProxy, log.Logger):
    classProvides(IGuiComponent)

    def __init__(self, main):
        log.Logger.__init__(self, main)
        log.LogProxy.__init__(self, main)

        self.main = main

        #load driver
        self.driver = driver.GuiDriver()
        self.driver.initiate()

        #Setup GUI
        self.controller = simulation.Controller(self)

    def finished(self):
        '''
        Called after the simulation window has been closed.
        '''
        self.main.finished()

    ### IGuiComponent ###

    name = 'simulation'

    @classmethod
    def construct_window(cls, main_model):
        instance = cls(main_model)
        return instance

    @classmethod
    def get_menu_presentation(cls):
        button = gtk.Button(label='Simulation driver')
        return button
