'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import os

MODE = 0

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Fantasy Earth: Zero", ".mdl;.oct")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(4))
        if idstring not in ["HED0", "OCT0"]:
            return 0
        return 1
    except:
        return 0

def load_all_models(mdlList):
    '''Load all models'''

    #carry over from previous models
    matList = []
    texList = []

    dirPath = rapi.getDirForFilePath(rapi.getInputName())
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".mdl")]
    for file in fileList:
        filename, ext = os.path.splitext(file)
        f = open(dirPath + file, 'rb')
        data2 = f.read()
        parser = SanaeParser(data2)
        parser.parse_file(filename)
        matList.extend(parser.matList)
        texList.extend(parser.texList)
        mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(texList, matList))
    mdlList.append(mdl)    
    
def load_single_model(data, mdlList):
    '''Loads a single model. For testing purposes'''
    
    filename, ext = os.path.splitext(rapi.getLocalFileName(rapi.getInputName()))
    parser = SanaeParser(data)
    parser.parse_file(filename)
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdlList.append(mdl)       

def noepyLoadModel(data, mdlList):
    '''Load the model'''
    
    ctx = rapi.rpgCreateContext()
    if MODE == 1:
        load_all_models(mdlList)
    else:
        load_single_model(data, mdlList)
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
        
    def read_name(self, n):
        
        string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
    
    def parse_textures(self, filename):
        
        try:
            dirpath = rapi.getDirForFilePath(rapi.getInputName())
            f = open(dirpath + filename + ".tex", 'rb')
            data = f.read()
            bs = NoeBitStream(data)
            
            header = bs.readBytes(4)
            size, numTex, null = bs.read('3L')
            for i in range(numTex):
                texSize = bs.readUInt()
                texFmt = noeStrFromBytes(bs.readBytes(4))
                if texFmt == "tex":
                    texFmt = "dds"
                bs.read('2L')
                texName = noeStrFromBytes(bs.readBytes(32))
                texData = bs.readBytes(texSize)
                
                tex = rapi.loadTexByHandler(texData, "." + texFmt)
                if tex is not None:
                    tex.name = texName
                    self.texList.append(tex)
        except:
            pass
        
    def parse_materials(self, numMat, filename):
        
        for i in range(numMat):
            self.inFile.seek(56, 1)
            texNum = self.inFile.readInt()
            texName = "none"
            if texNum != -1:
                try:
                    texName = self.texList[texNum].name
                except:
                    pass
            self.inFile.seek(36, 1)
            
            matName = "%s[%d]" %(filename, i)
            material = NoeMaterial(matName, texName)
            self.matList.append(material)
        
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_vertices(self, numVerts, vertSize):
        
        if vertSize == 52:
            vertBuff = self.inFile.readBytes(numVerts*52)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 28)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 44)
        elif vertSize == 56:
            vertBuff = self.inFile.readBytes(numVerts*56)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 28)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 48)
        rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, numVerts, noesis.RPGEO_POINTS, 1)
        
    def parse_frames(self, numFrames):
        
        for i in range(numFrames):
            frameName = self.read_name(32)
            self.inFile.seek(140, 1)
        
    def parse_header(self):
        
        self.inFile.seek(48, 1)
        
    def get_padding(self, start, size):
        '''Return the amount of padding left to read'''
        
        padSize = size
        if size % 16 != 0:
            padSize = size + (16 - (size % 16))
            
        #calculate current position relative to start of chunk
        relativeOfs = self.inFile.tell() - start
        
        #calculate the amount of bytes remaining in the chunk
        remain = padSize - relativeOfs
        self.inFile.seek(remain, 1)
        
    def parse_file(self, filename):
        '''Main parser method'''
        
        self.parse_textures(filename)
        while self.inFile.tell() != self.inFile.dataSize:
            chunk = self.read_name(4)
            size = self.inFile.readUInt()
            start = self.inFile.tell() + 8 #start of the chunk
            
            if chunk == "HED0":
                numMesh, unk2 = self.inFile.read('2L')
                self.parse_header()
            elif chunk == "MTR0":
                numMat, unk = self.inFile.read('2L')
                self.parse_materials(numMat, filename)
            elif chunk == "OBJ0":
                unk1, unk2 = self.inFile.read('2L')
            elif chunk == "WGP0":
                pass
            elif chunk == "GRP0":
                unk1, unk2 = self.inFile.read('2L')
                self.inFile.readUInt()
                matNum = self.inFile.readUInt()
            elif chunk == "PRM0":
                pass
            elif chunk == "VTX0":
                numVerts, unk = self.inFile.read('2L')
                vertSize = size // numVerts
                self.parse_vertices(numVerts, vertSize)
            elif chunk == "IDX0":
                numIdx, unk = self.inFile.read('2L')
                idxBuff = self.parse_faces(numIdx)
                matName = self.matList[matNum].name
                rapi.rpgSetMaterial(matName)
                rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
            elif chunk == "FRM0":
                numFrames, unk = self.inFile.read('2L')
                self.parse_frames(numFrames)
            else:
                pass
                
            self.get_padding(start, size)