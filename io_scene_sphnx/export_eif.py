import bpy
import os
import math
import datetime
from mathutils import *
from math import *
from pathlib import Path
from bpy_extras.io_utils import axis_conversion
from bpy import context
from pprint import pprint

def save(context,
         filepath,
         *,
         use_triangles=False,
         use_edges=True,
         use_normals=False,
         use_smooth_groups=False,
         use_smooth_groups_bitflags=False,
         use_uvs=True,
         use_materials=True,
         use_mesh_modifiers=True,
         use_mesh_modifiers_render=False,
         use_blen_objects=True,
         group_by_object=False,
         group_by_material=False,
         keep_vertex_order=False,
         use_vertex_groups=False,
         use_nurbs=True,
         use_selection=True,
         use_animation=False,
         global_matrix=None,
         path_mode='AUTO'
         ):

    #Open writer
    out = open(filepath, "w")
    
    print("[i] exporting", filepath)

    #Get scene info
    scn = bpy.context.scene 
    ow  = out.write
    Materials_Dict = dict()
    
    def GetMaterialIndex(MaterialName):
        for index, material in Materials_Dict.items():
            if material == MaterialName:
                print(index)
        return index
    
    def GetMaterials():
        MaterialIndex = 0
            
        ow("*MATERIALS {\n")
        
        for obj in bpy.context.scene.objects:
            for s in obj.material_slots:
                if s.material and s.material.use_nodes:
                    DiffuseColor = s.material.diffuse_color
                    for n in s.material.node_tree.nodes:
                        if n.type == 'TEX_IMAGE':                
                            ow("  *MATERIAL %d {\n" % (MaterialIndex))
                            ow("    *NAME \"%s\"\n" % (os.path.splitext(n.image.name)[0]))
                            ow("    *COL_DIFFUSE %.6f %.6f %.6f\n" % (DiffuseColor[0], DiffuseColor[1], DiffuseColor[2]))
                            ow("    *MAP_DIFFUSE \"%s\"\n" % (bpy.path.abspath(n.image.filepath)))      
                            #Check if the texture exists
                            if (os.path.exists(bpy.path.abspath(n.image.filepath))):
                                ow("    *TWOSIDED\n")
                            ow("    *MAP_DIFFUSE_AMOUNT 1.0\n")
                            
                            #Add data to dictionary
                            Materials_Dict[MaterialIndex] = os.path.splitext(n.image.name)[0]
                            
                            #Add 1 to the materials index
                            MaterialIndex +=1
        ow("  }\n")
        ow("}\n\n")
        
    def GetMesh():
        for ob in scn.objects:
            #Invert 'Y' 'Z'
            #m = axis_conversion("Y", "Z", "Z", "Y").to_4x4()
            #ob.matrix_world = m * ob.matrix_world
            
            if ob.hide_viewport:
                continue
            
            if ob.type == 'MESH':
                me = ob.data
                uv_layer = me.uv_layers.active.data

                VertexList = []
                UVList = []
                VertColList = []
                
                FaceFormat = "V"
                
                #==================GET VERTEX LIST==============================
                for vertex in me.vertices:
                    VertexList.append("%.6f,%.6f,%.6f" % (vertex.co.x,vertex.co.z,vertex.co.y))
 
                 #==================GET UV LIST==============================
                if len(me.vertex_colors):
                    for pl_count, poly in enumerate(me.polygons):
                        for li_count, loop_index in enumerate(poly.loop_indices):
                            #print(pl_count, li_count, loop_index, "uv_layer len:", len(uv_layer))
                            UVList.append("%.6f,%.6f" % (uv_layer[loop_index].uv.x,uv_layer[loop_index].uv.y))
                    UVList = list(dict.fromkeys(UVList))
                        
                 #==================GET Vertex Color LIST==============================               
                if len(me.vertex_colors):
                    for vertex in me.vertex_colors.active.data:
                        VertColList.append("%.6f,%.6f,%.6f,%.6f" % (vertex.color[0],vertex.color[1],vertex.color[2],vertex.color[3]))
                    VertColList = list(dict.fromkeys(VertColList))
                
                #===================COUNT TRIS======================
                for face in me.polygons:
                    vertices = face.vertices
                        
                #==================PRINT DATA==============================
                ow("*MESH {\n")    
                ow("  *NAME \"%s\"\n" % (me.name))
                ow("  *VERTCOUNT %d\n" % (len(VertexList)))
                ow("  *UVCOUNT %d\n" % (len(UVList)))
                if(len(VertColList) > 0):
                    ow("  *VERTCOLCOUNT %d\n" % (len(VertColList)))
                ow("  *FACECOUNT %d\n" % (len(me.polygons)))
                ow("  *FACELAYERSCOUNT %d\n" % len(me.uv_layers))
                
                #Check if there are more than one layer
                if (len(me.uv_layers) > 1):
                    ow("  *FACESHADERCOUNT %d\n" % len(me.uv_layers))
                
                #Print Vertex data
                ow("  *VERTEX_LIST {\n")
                for list_item in VertexList:
                    dataSplit = list_item.split(",")
                    ow("    %s %s %s\n" % (dataSplit[0], dataSplit[1], dataSplit[2]))
                ow("  }\n")
                
                #Print UV data
                if (len(UVList) > 0):
                    FaceFormat += "T"
                    ow("  *UV_LIST {\n")
                    for list_item in UVList:
                        dataSplit = list_item.split(",")
                        ow("    %s %s\n" % (dataSplit[0], dataSplit[1]))
                    ow("  }\n")
                
                #Check if the vertex colors layer is active
                if(len(VertColList) > 0):
                    FaceFormat +="C"
                    ow("  *VERTCOL_LIST {\n")
                    for list_item in VertColList:
                        dataSplit = list_item.split(",")
                        ow("    %s %s %s %s\n" % (dataSplit[0], dataSplit[1], dataSplit[2], dataSplit[3]))                    
                    ow("  }\n")
                
                if len(ob.material_slots) > 0:
                    FaceFormat +="M"
                    
                #Print Shader faces
                if (len(me.uv_layers) > 1):
                    ow("  *FACESHADERS {\n")
                    ow("  }\n")
                    
                #Get FaceFormat
                ow("  *FACEFORMAT %s\n" % FaceFormat)
                
                uv_index = 0
                co_index = 0
                
                #Print Face list
                ow("  *FACE_LIST {\n")
                for poly in me.polygons:
                    #Get polygon vertices
                    PolygonVertices = poly.vertices
                    
                    #Write vertices
                    ow("    %d " % (len(PolygonVertices)))
                    for vert in PolygonVertices:
                        ow("%d " % vert)
                    #Write UVs
                    if ("T" in FaceFormat):
                        for vert_idx, loop_idx in enumerate(poly.loop_indices):
                            uv_coords = me.uv_layers.active.data[loop_idx].uv
                            ow("%d " % UVList.index("%.6f,%.6f" % (uv_coords.x, uv_coords.y)))
                            
                    #Write Colors
                    if ("C" in FaceFormat):
                        for color_idx, loop_idx in enumerate(poly.loop_indices):
                            vertex = me.vertex_colors.active.data[loop_idx]
                            ow("%d " % VertColList.index("%.6f,%.6f,%.6f,%.6f" % (vertex.color[0],vertex.color[1],vertex.color[2],vertex.color[3])))
                    
                    #Write Material Index
                    if ("M" in FaceFormat):
                        for s in ob.material_slots:
                            if s.material and s.material.use_nodes:
                                for n in s.material.node_tree.nodes:
                                    if n.type == 'TEX_IMAGE':
                                        ow("%d " % GetMaterialIndex(os.path.splitext(n.image.name)[0]))
                    ow("\n")
                ow("  }\n")
                
                #Close Tag
                ow("}\n")

    time_now = datetime.datetime.utcnow()

    #Script header
    ow("*EUROCOM_INTERCHANGE_FILE 100\n")
    ow("*COMMENT Eurocom Interchange File Version 1.00 %s\n\n" % time_now.strftime("%A %B %d %Y %H:%M"))

    #print scene info
    ow("*SCENE {\n")
    ow("  *FIRSTFRAME  %d\n" % (scn.frame_start))
    ow("  *LASTFRAME   %d\n" % (scn.frame_end  ))
    ow("  *FRAMESPEED  %d\n" % (scn.render.fps ))
    ow("  *STATICFRAME 0\n")
    ow("  *AMBIENTSTATIC 1.0 1.0 1.0\n")
    ow("}\n\n")

    #Write materials
    GetMaterials()

    #Write Meshes
    GetMesh()

    #Close writer
    out.close()
    print('[i] done')
    
    return {'FINISHED'}
    
    
if __name__ == "__main__":
    save({}, str(Path.home()) + "/Desktop/testEIF_d.eif")