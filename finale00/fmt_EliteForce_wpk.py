'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Elite Force", ".wpk")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    bs = NoeBitStream(data)
    idstring = noeStrFromBytes(bs.readBytes(4))
    if idstring == "apgw":
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
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readByte())
        try:
            return noeStrFromBytes(string)
        except:
            return string # non-ascii?
        
    def parse_materials(self, numMat):
            
        for i in range(numMat):
            count = self.inFile.readByte()
            self.inFile.read('3B')
            self.inFile.read('%dL' %count)
            self.inFile.readByte()
            fxName = self.read_name()
            numProp = self.inFile.readUInt()
            for j in range(numProp):
                propName = self.read_name()
                numValues = self.inFile.readByte() // 4
                self.inFile.read('%df' %numValues)
            self.inFile.readUInt()
            numTex = self.inFile.readUInt()
            for j in range(numTex):
                texType = self.read_name()
                texName = self.read_name()
            
    def parse_textures(self, numTex):
            
        pass    
        
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts * 32)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 2)
    
    def parse_meshes(self, numMesh):
        
        self.inFile.seek(5351079)
        idstring = self.inFile.readString()
        while idstring == "MSD0":
            self.inFile.read('4L')
            self.inFile.readShort()
            self.inFile.read('6f')
            numMat = self.inFile.readUInt()
            self.parse_materials(numMat)
            
            numIdx = self.inFile.readUInt()
            idxBuff = self.parse_faces(numIdx)
            
            count = self.inFile.readUInt()
            self.inFile.read("%dL" %count)
            numVerts = self.inFile.readUInt()
            vertBuff = self.inFile.readBytes(numVerts*12)
            
            numUV = self.inFile.readUInt()
            uvBuff = self.inFile.readBytes(numUV * 8)
            
            numNorms = self.inFile.readUInt()
            normBuff = self.inFile.readBytes(numNorms * 12)
            
            unk = self.inFile.readUInt()
            self.inFile.seek(unk * 16, 1)
            
            self.inFile.read('2L')
            
            numBones = self.inFile.readUInt()
            self.parse_bones(numBones)

            unk2 = self.inFile.readUInt()
            self.parse_unk2(unk2)

            rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgBindNormalBuffer(normBuff, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)   
            idstring = self.inFile.readString()
    
    def parse_bones(self, numBones):
        
        for i in range(numBones):
            boneName = self.read_name()
            
    def parse_unk2(self, count):
        
        self.inFile.seek(20 * count, 1)
        
    def parse_file(self):
        '''Main parser method'''
        
        self.inFile.readBytes(4)
        self.inFile.read('4L')
        self.inFile.read('4f')
        modelName = noeStrFromBytes(self.inFile.readBytes(self.inFile.readShort()))
        unk1, unk2 = self.inFile.read('2L')
        self.inFile.seek(unk1, 1)
        
        self.parse_meshes(1)
        