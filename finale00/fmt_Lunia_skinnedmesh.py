'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Lunia Online", ".skinnedmesh")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    return 1

def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''
    
    #we need to load an xml and parse it to get the materials
    
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
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
    
    def read_name(self):
        
        string = bytes()
        n = self.inFile.readUInt()
        for i in range(n):
            string += self.inFile.readBytes(1)
            self.inFile.readByte()
        return noeStrFromBytes(string)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_vertices(self, numVerts):
        
        positions = self.inFile.readBytes(12*numVerts)
        rapi.rpgBindPositionBuffer(positions, noesis.RPGEODATA_FLOAT, 12)
        
    def parse_normals(self, numNorms):
        
        normals = self.inFile.readBytes(12*numNorms)
        rapi.rpgBindNormalBuffer(normals, noesis.RPGEODATA_FLOAT, 12)
        
    def parse_uv(self, numUV):
        
        uvs = self.inFile.readBytes(8*numUV)
        rapi.rpgBindUV1Buffer(uvs, noesis.RPGEODATA_FLOAT, 8)
        
    def parse_weights(self, numWeights):
        
        for i in range(numWeights):
            self.inFile.seek(20, 1)
        
    def parse_file(self):
        '''Main parser method'''
        
        meshName = self.read_name()
        numVerts, numIdx, unk1, unk2, unk3, unk4, unk5, unk6 = self.inFile.read('8L')
        idxBuff = self.parse_faces(numIdx)
        
        numVerts = self.inFile.readUInt()
        self.parse_vertices(numVerts)
        numNorms = self.inFile.readUInt()
        self.parse_normals(numNorms)
        numUV = self.inFile.readUInt()
        self.parse_uv(numUV)
        numWeights = self.inFile.readUInt()
        self.parse_weights(numWeights)
        
        rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
        
        