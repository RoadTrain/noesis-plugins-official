'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Otogi 1", ".mdl")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    bs = NoeBitStream(data)
    size = bs.readUInt()
    if size == bs.dataSize:
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
        self.texNames = []
        
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
            
        for i in range(numMat):
            self.inFile.read('5L')
            texNum = self.inFile.readInt()
            self.inFile.readUInt()
            self.inFile.readInt()
            self.inFile.read('12f')
            self.inFile.seek(32, 1)
            material = NoeMaterial("material[%d]" %i, "")
            if texNum > -1:
                texName = self.texNames[texNum]
                print(texName)
                material.setTexture(texName)
                
            self.matList.append(material)
        
    def parse_textures(self, numTex):
            
        for i in range(numTex):
            name = self.inFile.readString()
            self.texNames.append(name)
        
    def parse_vertices(self, numVerts, vertType):
        
        if vertType == 1:
            return self.inFile.readBytes(numVerts * 36)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 2)
    
    def parse_meshes(self, numMesh):
        
        pass
    
    def parse_bones(self, numBones):
        
        pass
        
    def parse_file(self):
        '''Main parser method'''
        
        filesize = self.inFile.readUInt()
        self.inFile.read('4L')
        numIdx, numVerts1, numVerts2, numVerts3, numVerts4, numMat, \
           numTex = self.inFile.read('7L')
        unkOfs, faceOfs, vert1Ofs, vert2Ofs, vert3Ofs, vert4Ofs = self.inFile.read('6L')
        matOfs, texOfs = self.inFile.read('2L')
        
        self.inFile.seek(texOfs)
        self.parse_textures(numTex)
        
        self.inFile.seek(matOfs)
        self.parse_materials(numMat)
        
        self.inFile.seek(faceOfs)
        idxBuff = self.parse_faces(numIdx)
        
        if vert1Ofs > 0:
            self.inFile.seek(vert1Ofs)
            vertBuff = self.parse_vertices(numVerts1, 1)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 0)
            #rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 60, 16)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 20)
        if vert2Ofs > 0:
            self.inFile.seek(vert2Ofs)
            vertBuff = self.parse_vertices(numVerts2, 2)
        if vert3Ofs > 0:
            self.inFile.seek(vert3Ofs)
            vertBuff = self.parse_vertices(numVerts3, 3)        

        #self.invert_faces()
        matName = self.matList[0].name
        rapi.rpgSetMaterial(matName)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE_STRIP, 1)