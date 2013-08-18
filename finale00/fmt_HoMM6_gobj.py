'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Heroes of Might and Magic VI", ".gobj")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    bs = NoeBitStream(data)
    idstring = bs.readUInt()
    if idstring != 3992875215:
        return 0
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
        
        string = self.inFile.readBytes(self.inFile.readUByte())
        return noeStrFromBytes(string)

    def plot_points(self, numVerts):
            
        rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, numVerts, noesis.RPGEO_POINTS, 1)    
        
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(numVerts*64)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_HALFFLOAT, 64, 0)
        #rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_HALFFLOAT, 64, 13)
        #rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_HALFFLOAT, 64, 12)
        
    def parse_faces(self, numIdx):
        
        idxBuff = self.inFile.readBytes(numIdx*2)
        rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
        
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def parse_vertChunk(self):
        
        size = self.inFile.readUInt()
        tag = self.inFile.readByte()
        if tag == 0x10:
            self.inFile.seek(3, 1)
        elif tag == 0x20:
            self.inFile.readUInt()
        
        numVerts = size // 64
        self.parse_vertices(numVerts)
        
    def parse_faceChunk(self):
        
        size = self.inFile.readUInt()
        tag = self.inFile.readByte()
        if tag == 0x10:
            self.inFile.seek(3, 1)
        elif tag == 0x20:
            self.inFile.readUInt()
        
        numIdx = size // 2
        self.parse_faces(numIdx)
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(4)
        self.inFile.readUInt()
        self.inFile.readBytes(4)
        self.inFile.seek(18, 1)
        
        while not self.inFile.checkEOF():
            tag = self.inFile.readUShort()
            size = self.inFile.readUInt()
            flag = self.inFile.readByte()
            if tag == 0x2010:
                self.inFile.seek(size, 1)
            elif tag == 0x5010:
                self.inFile.readUShort()
                self.parse_vertChunk()
                self.inFile.readUShort() #hardcode
            elif tag == 0x5020:
                self.inFile.readUShort()
                self.parse_faceChunk()
                break
            elif flag == 0x35:
                pass #read another chunk
            elif flag == 0x00:
                self.inFile.readUShort()
                self.inFile.readUInt()
            elif flag == 0x04:
                tag2 = self.inFile.readUShort()
                if tag2 == 0x3010:
                    self.read_name()
                    self.inFile.readByte()
                elif tag2 == 0x4010:   
                    self.read_name()
                    self.inFile.readByte()                    
            else:
                self.inFile.seek(size, 1)
            
            

        
        #count = self.inFile.readUByte()
        #self.inFile.readBytes(count)
        #self.inFile.seek(6, 1)
        
        #chunkSize = self.inFile.readUInt()
        #self.inFile.seek(9, 1)
        #chunkSize = self.inFile.readUInt()
        #self.inFile.seek(3, 1)
        
        #name = self.read_name()
        #print(name)
        #self.inFile.seek(3, 1)
        #chunkSize = self.inFile.readUInt()
        #self.inFile.seek(9, 1)
        #chunkSize = self.inFile.readUInt()
        #self.inFile.seek(3, 1)
        #name = self.read_name()
        #print(name)
        #self.inFile.seek(3, 1)
        #chunkSize = self.inFile.readUInt()
        #self.inFile.seek(9, 1)
        #chunkSize = self.inFile.readUInt()
        #self.inFile.seek(3, 1)
        #chunkSize = self.inFile.readUInt()
        #self.inFile.seek(3, 1)
        #print(self.inFile.tell())
        #sectSize = self.inFile.readUInt()
        #numVerts = sectSize // 64
        #print(numVerts)
        #tag = self.inFile.readUInt()
        #self.parse_vertices(numVerts)
        
        #self.inFile.readBytes(4)
        #self.inFile.readUInt()
        #self.inFile.seek(3, 1)
        #sectSize = self.inFile.readUInt()
        #numIdx = sectSize // 2
        #self.inFile.readBytes(4)
        #self.parse_faces(numIdx)
        #print(self.inFile.tell())