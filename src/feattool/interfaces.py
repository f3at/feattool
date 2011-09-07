# F3AT - Flumotion Asynchronous Autonomous Agent Toolkit
# Copyright (C) 2010,2011 Flumotion Services, S.A.
# All rights reserved.

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# See "LICENSE.GPL" in the source distribution for more information.

# Headers in this file shall remain intact.
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
