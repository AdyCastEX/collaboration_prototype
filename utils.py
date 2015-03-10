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
        create_directory(path) 
    filename = path + "/" + name
    
    bpy.ops.wm.collada_export(filepath=filename)
        
def load_state(path,name):
    ''' imports a scene from a collada(.dae) file 
    
    Parameters
    path         -- a string that contains the filepath of the folder where the file will be loaded
    name         -- a string that contains the filename of the collada file to load
    '''
    filename = path + "/" + name + ".dae"
    if os.path.isfile(filename):
        #clear the scene to remove objects that are not part of the state to load
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        bpy.ops.wm.collada_import(filepath=filename)
        
def check_file(path,name):
    '''checks if a file exists
    
    Parameters
    path        -- a string containing the filepath of the folder where the file is located
    name        -- a string containing the filename of the file to check
    
    Return Value
    exist_flag  -- a boolean value used to indicate a file's existence 
                -- True --> the file exists
                -- False --> the file does not exist
                
    '''
    
    filename = path + "/" + name + ".dae"
    if os.path.isfile(filename):
        exist_flag = True
    elif not os.path.isfile(filename):
        exist_flag = False
        
    return exist_flag

def check_dir(path):
    '''checks if a directory exists
    
    Parameters
    path        -- a string containing the filepath of the directory to check
    
    Return Value
    exist_flag    -- a boolean value used to indicate a directory's existence
    
    '''
    
    if os.path.isdir(path):
        exist_flag = True
    elif not os.path.isdir(path):
        exist_flag = False
        
    return exist_flag

def format_op_name(op_name):
    '''converts an operator name to a format that follows method naming conventions
    
    Parameters:
    op_name        -- the name of the operator from the info space
    
    Return Value
    formatted_name -- the properly formatted name of the operator
    
    '''
    #convert the op name to lowercase
    formatted_name = op_name.lower()
    #replace all spaces with underscores
    while " " in formatted_name:
        formatted_name = formatted_name.replace(" ","_")
    return formatted_name
    
def get_obj_names(target_objects):
    '''gets the names of multiple objects
    
    Parameters
    target_objects    -- a list containing target objects
    
    Return Value
    obj_names         -- a list of names of target objects in string format
    
    '''
    obj_names = []
    for obj in target_objects:
        obj_names.append(obj.name)
        
    return obj_names
    