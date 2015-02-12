# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

#--- ### Header
bl_info = {
        "name": "Collaboration Prototype",
        "author": "Carl Adrian P. Castueras",
        "version" : (1,1,0),
        "blender" : (2,7,2),
        "category" : "Development",
        "description" : "Used for Collaborative 3D Modeling",
        "warning" : "Experimental"
    }

#--- ### Imports
import bpy
import socket
from bpy.utils import register_module,unregister_module

if "init_data" in locals():
    import imp
    imp.reload(operators)
    imp.reload(ui)
    imp.reload(encoder)
    imp.reload(decoder)
    imp.reload(server)
else:
    from . import operators
    from . import ui
    from . import encoder
    from . import decoder
    from . import server

#--- ### Register
def register():
    '''registers all classes in this module'''
    register_module(__name__)
    #a boolean property used to check if the listening thread is active
    bpy.types.Scene.thread_flag = bpy.props.BoolProperty(default=False)
    #a boolean property used to check if the session operator is in modal mode
    bpy.types.Scene.modal_flag = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.active_obj_name = bpy.props.StringProperty()
    #a string property that stores the ip address of the server. By default, it has the ip address of the host machine
    bpy.types.Scene.server_ip_address = bpy.props.StringProperty(default=socket.gethostbyname(socket.gethostname()))
    #an int property that stores the port of the server. By default it has the value 5050
    bpy.types.Scene.server_port = bpy.props.IntProperty(default=5050)

def unregister():
    '''unregisters all classes in this module'''
    unregister_module(__name__)
    del bpy.types.Scene.modal_flag
    del bpy.types.Scene.thread_flag
    del bpy.types.Scene.active_obj_name
    del bpy.types.Scene.server_ip_address
    del bpy.types.Scene.server_port
    
#--- ### Main code
if __name__ == '__main__':
    register() 
