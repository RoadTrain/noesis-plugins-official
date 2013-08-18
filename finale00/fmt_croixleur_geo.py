'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import struct

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Croixleur", ".geo")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    bs = NoeBitStream(data)
    idstring = noeStrFromBytes(bs.readBytes(4))
    version = bs.readUInt()
    if idstring == "geo" and version == 4100:
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
        
        string = self.inFile.readBytes(32)
        return noeStrFromBytes(string)
        
    def parse_materials(self, numMat):
        for i in range(numMat):
            matName = self.read_name()
            self.inFile.readInt()
            self.inFile.read('4f')
            texNum = self.inFile.readByte()
            self.inFile.seek(39, 1)
            material = NoeMaterial(matName, "")
            #if texNum != -1:
                #texName = self.texList[texNum].name
                #material.setTexture(texName)
            self.matList.append(material)
        
    def parse_texture(self):
            
        size = self.inFile.dataSize - self.inFile.tell()
        data = self.inFile.readBytes(size)
        tex = rapi.loadTexByHandler(data, ".rin")
        print(tex)
        if tex:
            self.texList.append(tex)
        
    def parse_vertices(self, numVerts, numNorms, numWeights):
        
        vertBuff = self.inFile.readBytes(numVerts*12)
        normBuff = self.inFile.readBytes(numNorms*12)
        uvBuff = self.inFile.readBytes(numVerts*8)
        unkBuff = self.inFile.readBytes(numVerts*4)
        weightBuff = self.inFile.readBytes(numWeights*8)
            
        if numVerts:
            rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
            #rapi.rpgBindNormalBuffer(normBuff, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgBindUV1Buffer(uvBuff, noesis.RPGEODATA_FLOAT, 8)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*4)
        
    def parse_mesh(self):
            
        meshName = self.read_name()
        null, matNum = self.inFile.read("2L")
        numMat = self.inFile.readUInt()
        if numMat:
            self.inFile.readUInt()
            if numMat > 1:
                self.inFile.readUInt()
        
        self.parse_materials(numMat)
        self.inFile.readUInt()
        self.inFile.read('2f')
        self.inFile.read('3L')
        flag1 = self.inFile.readUInt()
        numVerts = self.inFile.readUInt()
        numNorms = self.inFile.readUInt()
        numIdx = self.inFile.readUInt() * 3
        numBones = self.inFile.readUInt()
        numWeights = self.inFile.readUInt()
        self.inFile.read('50f')
        self.parse_vertices(numVerts, numNorms, numWeights)
        idxBuff = self.parse_faces(numIdx)
        #idxBuff2 = self.parse_faces(numIdx)
        
        if numIdx:
            matName = self.matList[matNum].name
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_UINT, numIdx, noesis.RPGEO_TRIANGLE, 1)        
    
    def parse_bones(self, numBones):
        
        pass
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(4)
        self.inFile.read('2L')
        numMesh = self.inFile.readUInt()
        self.inFile.readUInt()
        numTex = self.inFile.readUInt()
        self.inFile.read('27f')
        self.inFile.readUInt()
        
        #get tex offsets
        skip = self.inFile.tell() + 64
        texOffsets = []
        for i in range(numTex):
            texOffsets.append(self.inFile.readUInt())
        self.inFile.seek(skip)
        
        #get mesh offsets
        meshOffsets = []
        for i in range(numMesh):
            meshOffsets.append(self.inFile.readUInt())
            
        for texOfs in texOffsets:
            self.inFile.seek(texOfs)
            self.parse_texture()
            
        for meshOfs in meshOffsets:
            self.inFile.seek(meshOfs)
            self.parse_mesh()