'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import os

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Seven Souls", ".bsb")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    bs = NoeBitStream(data)
    idstring = noeStrFromBytes(bs.readBytes(4))
    if idstring == "BSOB":
        return 1
    return 0

def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''
    
    ctx = rapi.rpgCreateContext()
    parser = SanaeParser(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdl.setAnims(parser.animList)
    mdlList.append(mdl)
    return 1

class Mesh(object):
    '''A generic mesh object, for convenience'''
    
    def __init__(self):
        
        self.positions = bytes()
        self.normals = bytes()
        self.uvs = bytes()
        self.numVerts = 0
        self.numIdx = 0
        self.idxBuff = bytes()
        self.matNum = -1
        self.matName = ""
        self.meshName = ""
        self.faceGroups = []
        
class Material(object):
    '''A single material contains multiple textures, each used by difference
    face groups in the mesh'''
    
    def __init__(self):
        
        self.texNames = []

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        self.extraList = []  # extra meshes?
        self.tempMats = [] #temporary storage
        
        
    def build_meshes(self):
        
        matCount = 0
        for i in range(len(self.meshList)):
            mesh = self.meshList[i]
            if mesh.matNum != -1:
                mat = self.tempMats[mesh.matNum]
            rapi.rpgSetName(mesh.meshName)
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 56, 0)
            rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 56, 12)
            rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 56, 24)
            
            for j in range(len(mesh.faceGroups)):
                numIdx, idxBuff = mesh.faceGroups[j]
                if numIdx == 0:
                    continue
                matName = "Material[%d]" %matCount
                texName = mat.texNames[i]
                
                material = NoeMaterial(matName, texName)
                self.matList.append(material)
                rapi.rpgSetMaterial(matName)
                rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)         
                
    def build_extras(self):
        
        for i in range(len(self.extraList)):
            mesh = self.extraList[i]
            rapi.rpgBindPositionBuffer(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgCommitTriangles(mesh.idxBuff, noesis.RPGEODATA_USHORT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)
    
    def parse_materials(self, numMat):
        
        mat = Material()
        for i in range(numMat):
            print("material %d" %i)
            mat.matNum = self.inFile.readUInt()
            self.inFile.read('9f')
            numTex = self.inFile.readUInt()
            if numTex == 0:
                self.read_name() #null
            else:
                for j in range(numTex):
                    texNum = self.inFile.readUInt()
                    texName =self.read_name()
                    maskName = self.read_name()
                    normName = self.read_name()
                    mat.texNames.append(texName)
            self.tempMats.append(mat)
        
    def parse_vertices(self, numVerts):
    
        return self.inFile.readBytes(numVerts*56)
    
    def parse_faces(self, numFaceGroups):
        
        faceGroups = []
        for i in range(numFaceGroups):
            numIdx = self.inFile.readUInt() * 3
            idxBuff = self.inFile.readBytes(numIdx*2)
            faceGroups.append([numIdx, idxBuff])
        return faceGroups
            
    def parse_mesh(self, numMesh):
        
        for i in range(numMesh):
            mesh = Mesh()
            
            self.inFile.readUInt()
            mesh.meshName = self.read_name()
            self.read_name() # NULL
            self.inFile.readByte()
            self.read_name()
            
            unk, numVerts, totalFaces = self.inFile.read('3L')
            #light map related
            bLightMap = self.inFile.readByte()
            self.read_name()
            self.inFile.readByte()
            
            self.inFile.read('3L')
            self.inFile.read('48f')
            self.inFile.readByte()
            self.inFile.read('10f')
            mesh.numVerts = self.inFile.readUInt()
            mesh.vertBuff = self.parse_vertices(mesh.numVerts)
            print(self.inFile.tell(), "vertbuff end")
            
            # a bunch of face groups per mesh
            numFaceGroups = self.inFile.readUInt()
            mesh.faceGroups = self.parse_faces(numFaceGroups)
            print(self.inFile.tell(), "idxBuff end")
            self.meshList.append(mesh)
            
            unk, mesh.matNum = self.inFile.read('2L')
            self.inFile.readInt()
            print(self.inFile.tell(), "mesh end")
            
    def parse_extra_mesh(self, numMesh):
            
        for i in range(numMesh):
            mesh = Mesh()
            mesh.matNum = self.inFile.readUInt()
            mesh.meshName = self.read_name()
            mesh.numIdx = self.inFile.readUInt() * 3
            mesh.numVerts = self.inFile.readUInt()
            
            self.inFile.read('48f')
            mesh.vertBuff = self.inFile.readBytes(mesh.numVerts * 12)
            mesh.idxBuff = self.inFile.readBytes(mesh.numIdx * 2)
            self.extraList.append(mesh)
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(4)
        self.inFile.readUInt()
        modelName = self.read_name()
        self.inFile.read('5L')
        self.inFile.readByte()
        numMesh = self.inFile.readUInt()
        self.parse_materials(numMesh)
        
        self.inFile.readUInt()
        numMesh = self.inFile.readUInt()
        self.inFile.read('6L')
        self.parse_mesh(numMesh)
        
        numExtra = self.inFile.readUInt()
        print(self.inFile.tell())
        self.parse_extra_mesh(numExtra)
        
        self.build_meshes()
        #self.build_extras()