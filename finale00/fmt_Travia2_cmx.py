'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject
import os
import struct

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Travia 2", ".cmx;.blk;.msh")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 3:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(3))
        if idstring not in ["CMX", "BLK", "SIN"]:
            return 0
        return 1
    except:
        return 0

def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''
    
    ctx = rapi.rpgCreateContext()
    inputName = rapi.getLocalFileName(rapi.getInputName())
    filename, ext = os.path.splitext(inputName)
    if ext == ".blk":
        parser = BLKParser(data)
    elif ext == ".cmx":
        parser = CMXParser(data)
    elif ext == ".msh":
        parser = MSHParser(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdl.setAnims(parser.animList)
    mdlList.append(mdl)
    return 1

class MSHParser(SanaeObject):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
            
        super(MSHParser, self).__init__(data)    
        
    def read_name(self):
            
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)    
        
    def parse_materials(self, numMat):
        
        for i in range(numMat):
            matName = self.read_name()
            material = NoeMaterial(matName, matName)
            self.matList.append(material)
            
    def parse_faces(self, numIdx):
        
        idxBuff = bytes()
        for j in range(numIdx):
            idxBuff += struct.pack('L', j)        
        return idxBuff
        
    def parse_meshes(self, numMesh):
        
        for i in range(numMesh):
            numVerts = self.inFile.readUInt()
            numNorms, numUV, unk4 = self.inFile.read('3L')
            vertBuff = self.inFile.readBytes(numVerts*12)
            uvBuff = self.inFile.readBytes(numUV*12)
            normBuff = self.inFile.readBytes(numNorms*12)
            matNum = self.inFile.readUInt()
            
            rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgBindNormalBuffer(normBuff, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgBindUV1BufferOfs(uvBuff, noesis.RPGEODATA_FLOAT, 12, 0)
            
            idxBuff = self.parse_faces(numVerts)
            matName = self.matList[matNum].name
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_UINT, numVerts, noesis.RPGEO_TRIANGLE, 1)
    
    def parse_file(self):
        
        idstring = self.inFile.readBytes(3)
        self.inFile.read('10f')
        self.inFile.seek(152, 1)
        numMesh, numMat, unk = self.inFile.read('3L')
        self.parse_materials(numMat)
        self.parse_meshes(numMesh)
        

class BLKParser(SanaeObject):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        super(BLKParser, self).__init__(data)
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)
    
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(12*numVerts)
        rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
        self.plot_points(numVerts)
        
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(4*numIdx)
        
    def parse_unk1(self, count):
        
        self.inFile.readBytes(48*count)
        
    def parse_unk2(self, count):
        
        self.inFile.readBytes(24*count)
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(3)
        self.inFile.read('10f')
        self.inFile.seek(152, 1)
        
        self.inFile.read('2L')
        matName = self.read_name()
        self.inFile.seek(8, 1)
        numVerts = self.inFile.readUInt()
        self.parse_vertices(numVerts)
        numIdx = self.inFile.readUInt() * 3
        idxBuff = self.parse_faces(numIdx)
        self.parse_unk1(numIdx)
        self.inFile.seek(numIdx*4)
        self.parse_unk2(numIdx)
        
        rapi.rpgSetMaterial(matName)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_UINT, numIdx, noesis.RPGEO_TRIANGLE, 1)

class CMXParser(SanaeObject):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        super(CMXParser, self).__init__(data)
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        try:
            return noeStrFromBytes(string)    
        except:
            return ""
        
    def parse_bones(self, numBones):
        
        for i in range(numBones):
            self.read_name()
            
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 4)
    
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(numVerts*36)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 4)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 16)
        rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 28)        
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(3)
        self.inFile.read('10f')
        numBones = self.inFile.readUInt()
        self.parse_bones(numBones)
        
        modelName = self.read_name()
        matName = self.read_name()
        
        unk = self.inFile.readUInt()
        numIdx = self.inFile.readUInt() * 3
        numVerts = self.inFile.readUInt()
        
        idxBuff = self.parse_faces(numIdx)
        self.parse_vertices(numVerts)
        
        rapi.rpgSetMaterial(matName)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_UINT, numIdx, noesis.RPGEO_TRIANGLE, 1)