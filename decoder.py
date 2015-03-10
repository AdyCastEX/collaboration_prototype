import bpy
import bmesh

class Decoder:
    
    def format_op_name(self,op_name):
        '''converts an operator name to a format that follows method naming conventions
        
        Parameters:
        op_name -- the name of the operator from the info space
        
        Return Value
        formatted_name -- the properly formatted name of the operator
        
        '''
        #convert the op name to lowercase
        formatted_name = op_name.lower()
        #replace all spaces with underscores
        while " " in formatted_name:
            formatted_name = formatted_name.replace(" ","_")
        return formatted_name
    
    def get_obj_names(self,target_objects):
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
    
    def refocus_object_mode(self,target_objects,flag):
        '''moves the selection to a collection of objects, in object mode
        
        Parameters
        target_objects      -- a list of names of target objects
        flag                -- a boolean value that indicates the operation
                            -- True -> select objects
                            -- False -> deselect objects
                            
        Return Value
        deselected_objects  -- a list of object names that were deselected (empty if flag == True)
        '''
        
        deselected_objects = []
        
        for target in target_objects:
            try:
                bpy.data.objects[target].select = flag
                if flag == False:
                    deselected_objects.append(target)
            except KeyError:
                pass
            
        return deselected_objects
    
    def refocus_edit_mode(self,active_object,internals,flag):
        '''moves the selection to a collection of internals (e.g vertices, edges, faces), in edit mode
        
        Parameters
        active_object     -- a string containing the name of the active object
        internals         -- a dictionary object containing the following:
            verts         -- a list containing the indices of vertices
            edges         -- a list containing the indices of edges
            faces         -- a list containing the indices of faces
        flag              -- a boolean value indicating the operation
                          -- True -> select internals
                          -- False -> deselect internals    
        '''
        
        deselected_internals = {}
        deselected_verts = []
        deselected_edges = []
        deselected_faces = []
        
        #create a bmesh to store the edit mode data of the object
        bm = bmesh.from_edit_mesh(bpy.data.objects[active_object].data)
        for i in internals['verts']:
            try:
                bm.verts[i].select = flag
                if flag == False:
                    deselected_verts.append(i)
            except IndexError:
                pass
        for i in internals['edges']:
            try:
                bm.edges[i].select = flag
                if flag == False:
                    deselected_edges.append(i)
            except IndexError:
                pass
        for i in internals['faces']:
            try:
                bm.faces[i].select = flag
                if flag == False:
                    deselected_faces.append(i)
            except IndexError:
                pass
                
        deselected_internals['verts'] = deselected_verts
        deselected_internals['edges'] = deselected_edges
        deselected_internals['faces'] = deselected_faces
        
        if flag == False:
            return deselected_internals
        elif flag == True:
            return {}
            
    def remove_focus(self,op):
        '''moves the selection from the currently selected object to target object/s 
        
        Parameters
        op -- a dict object containing the information of an operation
        
        Return Type
        focus             -- a dict containing the following:
           selected       -- a list containing the names of the objects that were selected before shifting focus
           active         -- a string containing the name of the active object
           mode           -- a string containing the current mode ('EDIT_MESH','OBJECT')
           internals      -- a dictionary object containing lists of indices of selected vertices, edges and faces
        '''
        
        current_active = bpy.context.active_object.name
        current_mode = bpy.context.mode
        current_selected = ''
        current_internals = ''
        
        #deselect objects if in object mode
        if current_mode in ('OBJECT'):
            selected_objs = self.get_obj_names(bpy.context.selected_objects)
            current_selected = self.refocus_object_mode(selected_objs,False)
            
        #deselect internals if in edit mode
        elif current_mode in ('EDIT_MESH'):
            selected_internals = self.get_internals(current_active)
            current_internals = self.refocus_edit_mode(current_active,selected_internals,False)
        
        #if the mode of the received operation is different from the current mode, shift the mode
        if op['mode'] != current_mode:
            print("From: {0}".format(bpy.context.mode))
            bpy.ops.object.editmode_toggle()
            print("To: {0}".format(bpy.context.mode))
            
            new_mode = bpy.context.mode
            
            #from EDIT_MESH to OBJECT - deselect currently selected objects as well
            if new_mode in ('OBJECT'):
                selected_objs = self.get_obj_names(bpy.context.selected_objects)
                current_selected = self.refocus_object_mode(selected_objs,False)
                
            #from OBJECT to EDIT_MESH - deselect currently selected internals as well
            elif new_mode in ('EDIT_MESH'):
                selected_internals = self.get_internals(current_active)
                current_internals = self.refocus_edit_mode(current_active,selected_internals,False)
                
        
            
        #if the mode of the received operation is OBJECT, move the selection of objects selected in the operation
        if op['mode'] in ('OBJECT'):
            self.refocus_object_mode(op['targets'], True)
            try:
                #shift the active object to the active object in the received operation
                bpy.context.scene.objects.active = bpy.data.objects[op['active_object']]
            except KeyError:
                pass
                 
        #if the mode of the received operation is EDIT_MESH, move the selection 
        elif op['mode'] in ('EDIT_MESH'):
            
            #move back to object to change the active object correctly
            bpy.ops.object.editmode_toggle()
            try:
                #shift the active object to the active object in the received operation
                bpy.context.scene.objects.active = bpy.data.objects[op['active_object']]
            except KeyError:
                pass
            
            #shift back to edit mode as this is an edit mode case
            bpy.ops.object.editmode_toggle()
            internals = {'verts': op['verts'], 'edges' : op['edges'], 'faces' : op['faces']}
            self.refocus_edit_mode(op['active_object'],internals,True)
            
        
            
        focus = {
            'selected' : current_selected,
            'active' : current_active,
            'mode' : current_mode,
            'internals' : current_internals
        }
        
        return focus
    
    def return_focus(self,op,focus):
        '''moves the selection back to the previously selected object/s 
        Parameters
        
        op      -- a dict object containing info of an operation
        focus         -- a dictionary object containing the following:
            selected  -- a list containing the names of selected objects
            active    -- a string containing the name of the active object
            mode      -- a string containing the mode ('OBJECT','EDIT_MESH')
            internals -- a dictionary object containing the indices of selected vertices, edges and faces 
        
        '''
        current_mode = bpy.context.mode
        
        try:
            #if the operation was for OBJECT mode, deselect the objects that were selected for the received operation
            if op['mode'] in ('OBJECT'):
                self.refocus_object_mode(op['targets'], False)
            #if the operation was for EDIT_MESH mode, deselect the internals that were selected for the received operation
            elif op['mode'] in ('EDIT_MESH'):
                internals = {'verts' : op['verts'],'edges' : op['edges'],'faces' : op['faces']}
                self.refocus_edit_mode(op['active_object'], internals,False)
        except KeyError:
            #handle Key errors in cases like delete where previous objects are removed
            pass
        
        if current_mode != focus['mode']:
            
            #if currently in object mode, reselect all objects that were previously selected
            if current_mode in ('OBJECT'):
                try:
                    #return the active object to the object that was previously active
                    bpy.context.scene.objects.active = bpy.data.objects[focus['active']]
                except KeyError:
                    pass
                self.refocus_object_mode(focus['selected'],True)
            
            #if currently in edit mode, reselect all the internals that were previously selected
            elif current_mode in ('EDIT_MESH'):
                
                bpy.ops.object.editmode_toggle()
                try:
                    #return the active object to the object that was previously active
                    bpy.context.scene.objects.active = bpy.data.objects[focus['active']]
                except KeyError:
                    pass
                bpy.ops.object.editmode_toggle()
                self.refocus_edit_mode(focus['active'], focus['internals'], True)
            
            #change the mode back to what it was before shifting focus
            print("From: {0}".format(bpy.context.mode))
            bpy.ops.object.editmode_toggle()
            print("To: {0}".format(bpy.context.mode))
        
        try:        
            #if the focus was in object mode, reselect all objects in the focus 
            if focus['mode'] in ('OBJECT'):
                self.refocus_object_mode(focus['selected'], True)
            #if the focus was in edit mode, reselect all the internals in the focus
            elif focus['mode'] in ('EDIT_MESH'):
                self.refocus_edit_mode(focus['active'], focus['internals'],True)
        except KeyError:
            pass
        
        
        
        
    def get_internals(self,active_object):
        '''gets the set of selected vertices, edges and faces
        
        Parameters
        active_object     -- a string containing the name of the object that contains the internals
        
        Return Value
        internals         -- a dictionary object that contains the following:
            verts         -- a list containing the indices of selected vertices
            edges         -- a list containing the indices of selected edges
            faces         -- a list containing the indices of selected faces
        
        '''
        
        #create a bmesh object to access the internals of the object
        bm = bmesh.from_edit_mesh(bpy.data.objects[active_object].data)
        
        verts = [i.index for i in bm.verts if i.select]
        edges = [i.index for i in bm.edges if i.select]
        faces = [i.index for i in bm.faces if i.select]
        
        internals = {
            'verts' : verts,
            'edges' : edges,
            'faces' : faces
        }
        
        return internals
        
    
    def translate(self,op):
        
        previous_selected = self.remove_focus(op)
        
        #get necessary parameters and translate the target object/s
        val = (op['x'],op['y'],op['z'])
        c_axis = (bool(op['caxis_x']),bool(op['caxis_y']),bool(op['caxis_z']))
        bpy.ops.transform.translate(value=val,constraint_axis=c_axis)
        
        self.return_focus(op,previous_selected)
        
    def rotate(self,op):
        
        previous_selected = self.remove_focus(op)
        
        val = op['value']
        c_axis = (bool(op['caxis_x']),bool(op['caxis_y']),bool(op['caxis_z']))
        axis = (op['axis_x'],op['axis_y'],op['axis_z'])
        bpy.ops.transform.rotate(value=val,axis=axis,constraint_axis=c_axis)
        
        self.return_focus(op, previous_selected)
    
    def resize(self,op):
        
        previous_selected = self.remove_focus(op)
        
        val = (op['x'],op['y'],op['z'])
        c_axis = (bool(op['caxis_x']),bool(op['caxis_y']),bool(op['caxis_z']))
        bpy.ops.transform.resize(value=val,constraint_axis=c_axis)
        
        self.return_focus(op, previous_selected)
        
    def add_cube(self,op):
        
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_cube_add(location=loc)
        
        self.return_focus(op, previous_selected)
        
    def add_circle(self,op):
        
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_circle_add(location=loc)
        
        self.return_focus(op, previous_selected)
    
    def add_plane(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_plane_add(location=loc)
        
        self.return_focus(op, previous_selected)
    
    def add_uv_sphere(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_uv_sphere_add(location=loc)
        
        self.return_focus(op, previous_selected)
    
    def add_ico_sphere(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_ico_sphere_add(location=loc)
        
        self.return_focus(op, previous_selected)
    
    def add_cylinder(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_cylinder_add(location=loc)
        
        self.return_focus(op, previous_selected)
    
    def add_cone(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_cone_add(location=loc)
        
        self.return_focus(op, previous_selected)
    
    def add_grid(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_grid_add(location=loc)
        
        self.return_focus(op, previous_selected)

    def add_monkey(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_monkey_add(location=loc)
        
        self.return_focus(op, previous_selected)
        
    def add_torus(self,op):
        previous_selected = self.remove_focus(op)
        
        loc = (op['loc_x'],op['loc_y'],op['loc_z'])
        bpy.ops.mesh.primitive_torus_add(location=loc)
        
        self.return_focus(op, previous_selected)
        
    def delete(self,op):
        previous_selected = self.remove_focus(op)
        
        if op['mode'] in ('OBJECT'):
            bpy.ops.object.delete(use_global=op['use_global'])
        elif op['mode'] in ('EDIT_MESH'):
            bpy.ops.mesh.delete(type=op['type'])
        
        self.return_focus(op, previous_selected)
        