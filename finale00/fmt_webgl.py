'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import struct
import ast

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Webgl", ".webgl")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    return 1

def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''
    
    inputName = rapi.getInputName()
    with open(inputName) as f:
        data = f.read()
    
    ctx = rapi.rpgCreateContext()
    parser = SanaeParser(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdl.setAnims(parser.animList)
    mdlList.append(mdl)
    return 1

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = ast.literal_eval(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        
    def plot_points(self, numVerts):
            
        rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, numVerts, noesis.RPGEO_POINTS, 1)    
        
    def read_name(self):
        
        #string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
    
    def build_mesh(self, numIdx, idxBuff):
        
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_UINT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def parse_materials(self, numMat):
            
        pass
        
    def parse_textures(self, numTex):
            
        pass    
    
    def parse_uvs(self, uvs):
        
        pass
    
    def parse_normals(self, normals):
        
        pass
        
    def parse_vertices(self, verts):

        vertList = verts[0]
        numVerts = len(vertList) // 3
        vertBuff = struct.pack('%df' %len(vertList), *vertList)
        rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
        self.plot_points(numVerts)
        return numVerts
    
    def parse_faces(self, faces):
        
        faceList = faces[0]
        count = len(faceList)
        numFaces = count // 11
        idxBuff = bytes()
        for i in range(numFaces):
            idx = faceList[11*i + 1: 11*i+4]
            idxBuff += struct.pack('3L', *idx)
        print(idx)
        numIdx = numFaces * 3
        #idxBuff = struct.pack('%dL' %count, *faceList)
        #numIdx = (count // 11) * 3
        return numIdx, idxBuff 
        #return 0, []
    
    def parse_meshes(self, numMesh):
        
        pass
    
    def parse_bones(self, numBones):
        
        pass
        
    def parse_file(self):
        '''Main parser method'''
        
        for key in self.inFile.keys():
            value = self.inFile[key]
            if key == "uvs":
                self.parse_uvs(value)
            elif key == "normals":
                self.parse_normals(value)
            elif key == "vertices":
                numVerts = self.parse_vertices(value)
            elif key == "faces":
                numIdx, idxBuff = self.parse_faces(value)
                
        self.build_mesh(numIdx, idxBuff)