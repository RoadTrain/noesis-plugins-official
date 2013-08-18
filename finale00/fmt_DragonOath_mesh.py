from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Dragon Oath", ".mesh")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel) #see also noepyLoadModelRPG
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin.'''
    return 1

def noepyLoadModel(data, mdlList):
    '''Load the model'''
    
    ctx = rapi.rpgCreateContext()
    parser = DragonOath_MESH(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdlList.append(mdl)
    return 1

class DragonOath_MESH(SanaeObject):
    
    def __init__(self, data):    
        super(DragonOath_MESH, self).__init__(data)
        
    def read_name(self, n=0):
        
        b = bytes()
        char = self.inFile.readBytes(1)
        while (char != b'\n'):
            b += char
            char = self.inFile.readBytes(1)
        try:
            name = noeStrFromBytes(b)
            return name
        except:
            try:
                name = noeStrFromBytes(b, 'gb18030')
                return name
            except:
                return ""
            
    def parse_vertices(self, numVerts, vertSize):
        
        if vertSize == 24:
            vertBuff = self.inFile.readBytes(numVerts * 24)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 24, 0)
        elif vertSize == 32:
            vertBuff = self.inFile.readBytes(numVerts * 32)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
        else:
            print("Unknown Vert size: %d" %vertSize)
        
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 2)
    
    def parse_mesh(self):
        
        self.inFile.readUShort()
        self.inFile.readUInt()
        self.inFile.readByte()
        self.read_name()
        self.inFile.readByte()
        numIdx = self.inFile.readUInt()
        self.inFile.readByte()
        idxBuff = self.parse_faces(numIdx)
        self.inFile.readShort()
        self.inFile.readUInt()
        numVerts = self.inFile.readUInt()
        self.inFile.readBytes(62)
        vertSize = self.inFile.readUShort()
        self.inFile.readUShort()
        self.inFile.readUInt()
        self.parse_vertices(numVerts, vertSize)
        
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def parse_file(self):
        
        chunk = self.inFile.readUShort()
        header = self.read_name()
        print (header)
        self.inFile.readShort()
        self.inFile.readUInt()
        self.inFile.readByte()
        self.parse_mesh()
            