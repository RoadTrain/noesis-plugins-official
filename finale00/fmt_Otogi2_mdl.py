'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Otogi 2", ".mdl")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    bs = NoeBitStream(data)
    size = bs.readUInt()
    idstring = noeStrFromBytes(bs.readBytes(4))
    if size == bs.dataSize and idstring == "MDL ":
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
        self.faceInfo = []
        
    def build_mesh(self, numVerts):
        
        idxBuff, idxCount = self.faceInfo.pop()
        print(len(idxBuff), idxCount)
        material = self.matList[0]
        material.setTexture(self.texNames[0])
        material.setDefaultBlend(0)
        rapi.rpgSetMaterial(material.name)
        #rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, numVerts, noesis.RPGEO_POINTS, 1)
        #rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, idxCount, noesis.RPGEO_TRIANGLE, 1)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, idxCount, noesis.RPGEO_TRIANGLE_STRIP, 1)
        
    def read_name(self):
        
        #string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
    
    def invert_faces(self):
        '''Negates the x-coord of all vertices in the mesh'''
        
        trans = NoeMat43((NoeVec3((-1, 0, 0)),
                         NoeVec3((0, 1, 0)),
                         NoeVec3((0, 0, 1)),
                         NoeVec3((0, 0, 0))))
        rapi.rpgSetTransform(trans)    
        
    def parse_materials(self, numMat):
            
        for i in range(numMat):
            self.inFile.read('5L')
            diffTex = self.inFile.readUInt()
            self.inFile.read('2l')
            self.inFile.read('12f')
            self.inFile.seek(48, 1)
            
            material = NoeMaterial("mat[%d]" %i, "")
            self.matList.append(material)
        
    def parse_textures(self, numTex):
            
        for i in range(numTex):
            texName = self.inFile.readString()
            self.texNames.append(texName)
        
    def parse_vertices(self, numVerts, vertType):
        
        if vertType == 1:
            return self.inFile.readBytes(60*numVerts)
        elif vertType == 2:
            return self.inFile.readBytes(64*numVerts)
        elif vertType == 3:
            return self.inFile.readBytes(72*numVerts)
    
    def parse_faces(self, numIdx):
        
        faceInfo = []
        idxBuff = bytes()
        total = 0
        count = 0
        while total < numIdx:
            idx = self.inFile.readBytes(2)
            if idx == b'\x00\x00' and count > 0:
                faceInfo.append([idxBuff, count])
                count = 0
                idxBuff = bytes()
            idxBuff = b''.join([idxBuff, idx])
            count += 1
            total += 1
        else:
            faceInfo.append([idxBuff, numIdx])
        return faceInfo 
        #return self.inFile.readBytes(numIdx * 2)
    
    def parse_bones(self, numBones):
        
        pass
    
    def parse_unk1(self, count):
        
        for i in range(count):
            self.inFile.seek(144, 1)
            
    def parse_unk2(self):
        
        pass
            
    def parse_unk3(self, count):
        
        for i in range(count):
            self.inFile.seek(32, 1)
        
    def parse_file(self):
        '''Main parser method'''
        
        filesize = self.inFile.readUInt()
        idstring = self.inFile.readBytes(4)
        self.inFile.read('2H')
        meshType = self.inFile.readUInt()
        self.inFile.read('2L')
        count1 = self.inFile.readUInt()
        numIdx = self.inFile.readUInt()
        numVerts1 = self.inFile.readUInt()
        numVerts2 = self.inFile.readUInt()
        numVerts3 = self.inFile.readUInt()
        numVerts4 = self.inFile.readUInt()
        count3 = self.inFile.readUInt()
        numMat = self.inFile.readUInt()
        numTex = self.inFile.readUInt()
        unk1Ofs, faceOfs, vert1Ofs, vert2Ofs, vert3Ofs, vert4Ofs, unk3Ofs, \
            matOfs, texOfs = self.inFile.read('9L')
        
        self.inFile.seek(unk1Ofs)
        self.parse_unk1(count1)
        self.parse_unk2()
        
        self.inFile.seek(unk3Ofs)
        self.parse_unk3(count3)
        
        self.inFile.seek(matOfs)
        self.parse_materials(numMat)
        
        self.inFile.seek(texOfs)
        self.parse_textures(numTex)
        
        self.inFile.seek(faceOfs)
        self.faceInfo = self.parse_faces(numIdx)
        
        if vert1Ofs > 0:
            self.inFile.seek(vert1Ofs)
            vertBuff = self.parse_vertices(numVerts1, 1)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 60, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 60, 36)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 60, 28)
            self.build_mesh(numVerts1)
            
        if vert2Ofs > 0:
            vertBuff = self.parse_vertices(numVerts2, 2)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 64, 0)
            self.build_mesh(numVerts2)
        if vert3Ofs > 0:
            print('here')
            vertBuff = self.parse_vertices(numVerts3, 3)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 72, 0)
            
            self.build_mesh(numVerts3)
        if vert4Ofs > 0:
            vertBuff = self.parse_vertices(numVerts4, 3)
        
        