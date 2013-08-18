'''Noesis import plugin. Written by Tsukihime

Game: Meng Jing Zhi Cheng
HP: http://mj.baiyou100.com/1600000.asp
'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("City of Dreams", ".gcf")
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
    parser = SanaeParser(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdl.setAnims(parser.animList)
    mdlList.append(mdl)
    return 1

class Mesh(object):
    
    def __init__(self):
        
        self.name = ""
        self.numIdx = 0
        self.numVerts = 0
        self.vertSize = 0
        self.idxBuff = bytes()
        self.vertBuff = bytes()

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.filename = rapi.getExtensionlessName(rapi.getLocalFileName(rapi.getInputName()))
        
    def invert_faces(self):
        '''Negates the x-coord of all vertices in the mesh'''
        
        trans = NoeMat43((NoeVec3((-1, 0, 0)),
                         NoeVec3((0, 1, 0)),
                         NoeVec3((0, 0, 1)),
                         NoeVec3((0, 0, 0))))
        rapi.rpgSetTransform(trans)    
        
    def read_name(self):
        
        #string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
        
    def parse_materials(self, numMat):
            
        pass
        
    def parse_textures(self, numTex):
            
        pass    
        
    def parse_vertices(self, numVerts):
        
        vertBuff = b'\x00'*12 # it's 1-based indices
        return b''.join([vertBuff, self.inFile.readBytes(numVerts * 12)])
    
    def parse_faces(self, numFaces):
        
        idxBuff = bytes()
        for i in range(numFaces):
            idxBuff = b''.join([idxBuff, self.inFile.readBytes(12)])
            self.inFile.readBytes(36)
            self.inFile.readBytes(12)
        return idxBuff
    
    def parse_meshes(self, numMesh):
        
        pass
    
    def parse_bones(self, numBones):
        
        pass
        
    def parse_file(self):
        '''Main parser method'''
        
        numFaces = self.inFile.readUInt()
        idxBuff = self.parse_faces(numFaces)
        
        numVerts = self.inFile.readUInt()
        vertBuff = self.parse_vertices(numVerts)
        
        numUV = self.inFile.readUInt()
        self.inFile.readBytes(numUV * 8)
        
        matName = self.filename + ".dds"
        self.invert_faces()
        rapi.rpgSetMaterial(matName)
        rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_UINT, numFaces * 3, noesis.RPGEO_TRIANGLE, 1)