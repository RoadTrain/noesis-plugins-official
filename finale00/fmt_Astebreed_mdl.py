'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Astebreed", ".mdl")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    return 1

def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''
    
    ctx = rapi.rpgCreateContext()
    inputName = rapi.getInputName()
    file = open(inputName, 'r')
    parser = SanaeParser(file)
    parser.parse_file()
    file.close()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdl.setAnims(parser.animList)
    mdlList.append(mdl)
    return 1

class SanaeParser(SanaeObject):
    
    def __init__(self, inFile):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = inFile
        
    def parse_textures(self, numTex):
        
        print(numTex, "textures")
    
    def parse_materials(self, numMat):
        
        print(numMat, "materials")
        
    def parse_bones(self, numBones):
        
        print(numBones, "bones")
        
    def parse_face(self, numVerts):
        
        self.inFile.readline() #open brace
        faceIndices = self.inFile.readline.split()
        uvIndices = self.inFile.readline.split()
        self.inFile.readline() #close brace
        
    def parse_face_list(self, numFaces):
        
        line = self.inFile.readline().strip()
        while line != "}":
            args = line.split()
            if not args:
                pass
            else:
                struct = args[0]
                if struct == "Polygon":
                    numVerts = args[1]
                    self.parse_face(numVerts)
                    
    def parse_vertices(self, numVerts):
        
        self.inFile.readline() #open brace
        for i in range(numVerts):
            self.inFile.readline()
        self.inFile.readline() #close brace
    
    def parse_normals(self, numNorms):
        
        self.inFile.readline() #open brace
        for i in range(numNorms):
            self.inFile.readline()
        self.inFile.readline() #close brace
    
    def parse_weights(self, numWeights):
        
        self.inFile.readline() #open brace
        for i in range(numWeights):
            self.inFile.readline()
        self.inFile.readline() #close brace
    
    def parse_uvs(self, numUV):
        
        self.inFile.readline() #open brace
        for i in range(numUV):
            self.inFile.readline()
        self.inFile.readline() #close brace
    
    def parse_mesh_materials(self, numMat):
        
        self.inFile.readline() #open brace
        for i in range(numMat):
            self.inFile.readline()
        self.inFile.readline() #close brace
        
    def parse_mesh(self, meshName):
        
        line = self.inFile.readline().strip()
        while not line.startswith("}"):
            args = line.split()
            if not args:
                pass
            else:
                struct = args[0]
                if struct == "PolygonList":
                    numFaces = args[1]
                    self.parse_face_list(numFaces)
                elif struct == "VertexList":
                    numVerts = args[1]
                    self.parse_vertices(numVerts)
                elif struct == "WeightList":
                    numWeights = args[1]
                    self.parse_weights(numWeights)
                elif struct == "NormalList":
                    numNorms = args[1]
                    self.parse_normals(numNorms)
                elif struct == "UVList":
                    numUV = args[1]
                    self.parse_uvs(numUV)
                elif struct == "MaterialIndexList":
                    numMat = args[1]
                    self.parse_mesh_materials(numMat)

    def parse_meshlist(self, numMesh):
        
        print(numMesh, "meshes")
        line = self.inFile.readline().strip()
        while not line.startswith("}"):
            args = line.split()
            if not args:
                pass
            else:
                struct = args[0]
                if struct == "Mesh":
                    meshName = args[1]
                    self.parse_mesh(meshName)
            line = self.inFile.readline().strip()
        print(line)
        
    def parse_file(self):
        '''Main parser method'''
        
        line = self.inFile.readline()
        while line:
            args = line.split()
            if not args:
                pass
            else:
                struct = args[0]
                if struct == "TextureList":
                    numTex = args[1]
                    self.parse_textures(numTex)
                elif struct == "MaterialList":
                    numMat = args[1]
                    self.parse_materials(numMat)
                elif struct == "SkeltonList":
                    numBones = args[1]
                    self.parse_bones(numBones)
                elif struct == "MeshList":
                    numMesh = args[1]
                    self.parse_meshlist(numMesh)
                
                
            line = self.inFile.readline()
            