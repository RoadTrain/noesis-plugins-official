'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
#from Sanae3D import Sanae


def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Settlers 7", ".s7m")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 0:
        return 0
    bs = NoeBitStream(data)
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
    '''A generic mesh object, for convenience'''
    
    def __init__(self):
        
        self.vertBuff = bytes()
        self.normBuff = bytes()
        self.uvBuff = bytes()
        self.numVerts = 0
        self.numIdx = 0
        self.idxBuff = bytes()
        self.matName = ""
        self.meshName = ""

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data, 0)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        self.meshInfo = []
        self.filename = rapi.getLocalFileName(rapi.getInputName())
        
    def build_meshes(self):
        
        for mesh in self.meshList:
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_HALFFLOAT, 24, 0)
            rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_HALFFLOAT, 24, 8)
            
            for idxStart, numIdx, matName in self.meshInfo:
                
                start = idxStart * 2
                end = start + (numIdx * 2)
                idxBuff = mesh.idxBuff[start:end]
                
                rapi.rpgSetMaterial(matName)
                rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def read_name(self, n):
        
        string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
    
    def parse_textures(self, chunkSize):
        
        self.inFile.seek(chunkSize, 1)
            
    def parse_VST0(self, numVerts, structSize):
        
        return self.inFile.readBytes(numVerts*structSize)
    
    def parse_VST1(self, numVerts, structSize):
        
        return self.inFile.readBytes(numVerts * structSize)
    
    def parse_VST2(self, numVerts, structSize):
        
        self.inFile.readBytes(numVerts * structSize)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 2)
    
    def parse_tex_name(self, bs, offset):
        
        bs.seek(offset)
        return bs.readString()
    
    def parse_mesh_info(self, numMesh, texChunk):
        
        bs = NoeBitStream(texChunk)
        for i in range(numMesh):
            matName = self.parse_tex_name(bs, self.inFile.readShort())
            diffName = self.parse_tex_name(bs, self.inFile.readShort())
            normName = self.parse_tex_name(bs, self.inFile.readShort())
            matteName = self.parse_tex_name(bs, self.inFile.readShort())
            backName = self.parse_tex_name(bs, self.inFile.readShort())
            
            self.inFile.readShort()
            numIdx = self.inFile.readUInt()
            idxStart = self.inFile.readUInt()
            
            material = NoeMaterial(matName, diffName)
            self.matList.append(material)
            
            self.meshInfo.append([idxStart, numIdx, matName])
    
    def seek_padding(self, size):
        ''' 16-byte chunk alignment'''
        
        pad = (16 - (size % 16)) % 16
        self.inFile.seek(pad, 1)
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(4)
        mesh = Mesh()
        unk, unk, mesh.numVerts, mesh.numIdx = self.inFile.read('4L')
        self.inFile.read('2H')
        self.inFile.read('6f')
        
        # chunk based parsing
        while not self.inFile.checkEOF():
            chunkType, unk = self.inFile.read('2H')
            chunkSize = self.inFile.readUInt()
            structSize = self.inFile.readUInt()
            chunkID = noeStrFromBytes(self.inFile.readBytes(4))
            if chunkType == 1:
                mesh.vertBuff = self.parse_VST0(mesh.numVerts, structSize)
            elif chunkType == 2:
                self.parse_VST1(mesh.numVerts, structSize)
            elif chunkType == 3:
                self.parse_VST2(mesh.numVerts, structSize)
            elif chunkType == 4:
                mesh.idxBuff = self.parse_faces(mesh.numIdx)
            elif chunkType == 6:
                texChunk = self.inFile.readBytes(chunkSize)
            elif chunkType == 7:
                numMesh = chunkSize // 20
                self.parse_mesh_info(numMesh, texChunk)
            else:
                self.inFile.seek(chunkSize, 1)
            self.seek_padding(chunkSize)

        self.meshList.append(mesh)
        self.build_meshes()