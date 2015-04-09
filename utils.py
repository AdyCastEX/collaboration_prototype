import os
import bpy
import bmesh
    
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
    
    #convert the string filepath into a path object
    path = os.path.abspath(filepath)
    #split the path into a list of directory names
    path_list = path.split(os.sep)
    #the path walk will start from the root directory (e.g "C:/" for windows or "/" for linux)
    path_walk = path_list[0]
    path_length = len(path_list)
 
    #for each subdirectory from the root, add it to the path walk  
    for i in range(1,path_length):
        path_walk += "/" + path_list[i]
        #if the current subdirectory does not exist, create it
        if not os.path.isdir(path_walk):
            os.mkdir(path_walk)
    
def create_file(path,name):
    '''creates an empty .dae file with a specified name in the specified path
    
    Parameters
    path              -- a string containing the path to the directory where the file is to be saved
    name              -- a string containing the filename of the file to create
    '''
    
    filename = path + "/" + name + ".dae"
    output_file = open(filename,'wb')
    output_file.close()
    

def save_state(path,name):
    ''' exports the current state of the scene to a collada (.dae) file 
    
    Parameters
    path         -- a string that contains the filepath to the folder where the file will be saved
    name         -- a string that contains the filename of the file to save
    '''
    
    if not os.path.isdir(path):
        create_directory(path) 
    filename = path + "/" + name
    
    bpy.ops.wm.collada_export(filepath=filename,triangulate=False)
        
def load_state(path,name):
    ''' imports a scene from a collada(.dae) file 
    
    Parameters
    path         -- a string that contains the filepath of the folder where the file will be loaded
    name         -- a string that contains the filename of the collada file to load
    
    Return Value
    load_flag    -- a boolean value used to indicate whether a file was loaded (True) or not (False)
    '''
    filename = path + "/" + name + ".dae"
    if os.path.isfile(filename):
        #clear the scene to remove objects that are not part of the state to load
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        bpy.ops.wm.collada_import(filepath=filename)
        format_obj_names("_",".")
        load_flag = True
    else:
        load_flag = False
        
    return load_flag
        
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

def get_obj_index(name,mode,collection):
    '''gets the index of a particular object in the scene
    
    Parameters
    name           -- the name of the object or type of object (e.g. Cube, Sphere, Monkey)
    mode           -- an integer value representing the mode of traversal (0 -> from index 0..n-1, 1 -> from index n-1..0)
    collection     -- an array of objects to traverse
    
    Return Value
    index          -- the integer index of the object
    '''
    
    n = len(collection)
    
    for i in range(0,n):
        if name in collection[i].name and mode == 0:
            index = i
            return index
        elif name in collection[n-1-i].name and mode == 1:
            index = n-1-i
            return index
        

def format_obj_names(remove_char,replace_char):

    '''converts certain charcters to a specified replacement character
    
    Parameters
    remove_char       -- the character to remove
    replace_char      -- the character that will replace the removed character
 
    '''
    
    for obj in bpy.data.objects:
        while remove_char in obj.name:
            obj.name = obj.name.replace(remove_char,replace_char)

def shift_name(name,concat_char,distance,max_num):
    '''shifts numbered object names (e.g. Cube.001) by a certain increment/decrement
    
    Parameters
    name          -- the original name (string) of the object
    concat_car    -- character to use when concatenating two strings
    distance      -- an int value that indicates how far to increment/decrement
    max_num       -- the maximum number that can be attached to the name
    
    Return value
    shifted_name  -- the shifted name (string)
    '''
    
    #ASSUMPTION: the name consists of only two parts {"Cube","001"} separated by '.'
    split_name = name.split(".")
    try:
        #convert the number_part (str) into an int
        number_part = int(split_name[1])
        #increment/decrement by the distance
        number_part += distance
    #this error will be raised in cases where there is no number part (e.g. "Cube","Sphere")
    except IndexError:
        #set to the max num (e.g Cube becomes Cube.003)
        number_part = max_num
        
    if number_part != 0:
        #convert the number part (int) to a string with leading zeroes (e.g. 5 becomes "005")
        number_part = str(number_part).zfill(3)
        #concatenate back with the concat_char instead of '.'
        shifted_name = split_name[0] + concat_char + number_part
    elif number_part == 0:
        shifted_name = split_name[0]

    return shifted_name
            
def get_internals(active_object,select_mode):
    '''gets the set of selected vertices, edges and faces
    
    Parameters
    active_object     -- a string containing the name of the object that contains the internals
    select_mode       -- a dictionary of three boolean values indicating the selection mode    
    
    Return Value
    internals         -- a dictionary object that contains the following:
        verts         -- a list containing the indices of selected vertices
        edges         -- a list containing the indices of selected edges
        faces         -- a list containing the indices of selected faces
    
    '''
    
    #create a bmesh object to access the internals of the object
    bm = bmesh.from_edit_mesh(bpy.data.objects[active_object].data)
    
    verts = []
    edges = []
    faces = []
    
    if select_mode['vertex_select'] == True:
        verts = [i.index for i in bm.verts if i.select]
    if select_mode['edge_select'] == True:
        edges = [i.index for i in bm.edges if i.select]
    if select_mode['face_select'] == True:
        faces = [i.index for i in bm.faces if i.select]
    
    internals = {
        'verts' : verts,
        'edges' : edges,
        'faces' : faces
    }
    
    return internals

def create_bmesh(object_name):
    '''creates a bmesh of a given object
    
    Parameters
    object_name      -- a string containing the name of the target object
    
    Return Value
    mesh             -- the created bmesh object
    '''
    
    mesh = bmesh.from_edit_mesh(bpy.data.objects[object_name].data)
    return mesh

def lock_object_selection(excluded_objects,flag):
    '''locks (or unlocks) all objects from selection, excluding specified objecs
    
    Parameters
    excluded_objects        --a list containing the names of objects not to lock
    flag                    -- a boolean value representing lock (True) and unlock (False)
    '''
    
    for obj in bpy.data.objects:
        if obj.name not in excluded_objects:
            obj.hide_select = flag
            
            
def op_equivalent(op1,op2):
    '''checks if two operations are equivalent
    
    Parameters
    op1       -- a dict object representing the first operation
    op2       -- a dict object representing the second operation
    
    Return Value
    equivalence  -- a boolean value that indicates if the operations are equivalent (True) or not (False)
    '''
    
    if op1 == op2:
        equivalence = True
    else:
        equivalence = False
        
    return equivalence

def get_select_mode():
    
    mode = {}
    
    mode['vertex_select'] = bpy.context.tool_settings.mesh_select_mode[0]
    mode['edge_select'] = bpy.context.tool_settings.mesh_select_mode[1]
    mode['face_select'] = bpy.context.tool_settings.mesh_select_mode[2]
    
    return mode