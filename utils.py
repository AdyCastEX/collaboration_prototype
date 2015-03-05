import os
import bpy
    
def format_file_path(pathname):
    '''formats a path name to replace backslashes with forward slashes
    
    Parameters
    pathname             -- a string that contains the pathname to format
    
    Return Value
    formatted_pathname   -- a string that contains the properly formatted pathname
    '''
    
    formatted_pathname = pathname
    
    while "\\" in formatted_pathname:
        formatted_pathname = formatted_pathname.replace("\\","/")
    return formatted_pathname
        
def get_file_path():
    '''gets the filepath of the addon's scripts
    
    Return Value
    path                  -- a string containing the filepath of the addon's scripts
    '''
    
    path = os.path.dirname(os.path.abspath(__file__))
    return path

def create_directory(filepath):
    '''creates a directory in the given filepath 
    
    Parameters
    filepath          -- a string containing the filepath of the folder to create
    '''
    
    os.mkdir(filepath)

def save_state(path,name):
    ''' exports the current state of the scene to a collada (.dae) file 
    
    Parameters
    path         -- a string that contains the filepath to the folder where the file will be saved
    name         -- a string that contains the filename of the file to save
    '''
    
    if not os.path.isdir(path):
        utils.create_directory(path) 
    filename = path + "/" + name
    
    bpy.ops.wm.collada_export(filepath=filename)
        
def load_state(path,name):
    ''' imports a scene from a collada(.dae) file 
    
    Parameters
    path         -- a string that contains the filepath of the folder where the file will be loaded
    name         -- a string that contains the filename of the collada file to load
    '''
    
    #clear the scene to remove objects that are not part of the state to load
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    try:
        filename = path + "/" + name + ".dae"
        bpy.ops.wm.collada_import(filepath=filename)
    except IOError:
        pass