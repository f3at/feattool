from zope.interface import Interface, Attribute

__all__ = ['IGuiComponent', 'IMainModel']


class IGuiComponent(Interface):
    '''
    Interface implemented by componenents of feattool (like simulation
    component for instnace.
    '''

    name = Attribute('Unique name of the component')

    def construct_window(main_model):
        '''
        Display main window.
        @param main_model: refrence to the main application controller
        @type main_controller: IMainModel
        '''

    def get_menu_presentation():
        '''
        Returns GTK element to display in main menu.
        @rtype: L{gtk.Widget} should have "clicked" event
        '''


class IMainModel(Interface):
    '''
    Interface implemented by main application controller by the components
    to communicate with it.
    '''

    def finished():
        '''Called when the components window gets closed to restore the
        main menu.'''
