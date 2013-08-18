'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Kungfu Strike", ".a3d")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    bs = NoeBitStream(data)
    try:
        idstring = noeStrFromBytes(bs.readBytes(4))
        if idstring == "A3D":
            return 1
        return 0
    except:
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
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)
        
    def parse_materials(self, numMat):
            
        pass
        
    def parse_textures(self, numTex):
            
        pass    
        
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts * 12)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 2)
    
    def parse_meshes(self, numMesh):
        
        for i in range(numMesh):
            self.inFile.read('2L')
            numVerts, numIdx = self.inFile.read("2L")
            
            idxBuff = self.parse_faces(numIdx)
            numSections = self.inFile.readUInt()
            
            for i in range(numSections):
                chunkType, unk2 = self.inFile.read('2L')
                size = self.inFile.readUInt()
                
                if chunkType == 2:
                    vertBuff = self.parse_vertices(numVerts)
                elif chunkType == 3:
                    self.inFile.seek(size, 1)
                elif chunkType == 4:
                    self.inFile.seek(size, 1)
                elif chunkType == 1:
                    self.inFile.seek(size, 1)
            
            self.inFile.readInt()
            count = self.inFile.readUInt()
            self.parse_unk1(count)
            count2 = self.inFile.readUInt()
            self.parse_unk2(count2)
            count3 = self.inFile.readUInt()
            self.parse_unk3(count3)
            
            print (self.inFile.tell())
            rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    
    def parse_bones(self, numBones):
        
        pass
    
    def parse_unk1(self, count):
        
        self.inFile.readBytes(count * 68)
        
    def parse_unk2(self, count):
        
        self.inFile.readBytes(count * 8)
        
    def parse_unk3(self, count):
        
        self.inFile.readBytes(count)
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(4)
        unk = self.inFile.readUInt()
        numMesh = self.inFile.readUInt()
        
        if numMesh == 1:
            self.inFile.seek(60, 1)
        elif numMesh == 2:
            self.inFile.seek(120, 1)
        
        self.inFile.readUInt()
        for i in range(numMesh):
            self.read_name()
        
        self.parse_meshes(numMesh)