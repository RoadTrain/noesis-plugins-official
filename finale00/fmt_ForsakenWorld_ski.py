'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import os

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Forsaken World", ".ski")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 8:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(8))
        if idstring != "MOXBIKSA":
            return 0
        return 1
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

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        
    def read_name(self, n=0):
        
        if n:
            string = self.inFile.readBytes(n)
        else:
            string = self.inFile.readBytes(self.inFile.readUInt())
        try:
            return noeStrFromBytes(string)
        except:
            try:
                return noeStrFromBytes(string, 'gb2312')
            except:
                return ""
            
    def open_file(self, texName):
        
        dirpath = rapi.getDirForFilePath(rapi.getInputName())
        
        try:
            f = open(texName, 'rb')
            return f
        except:
            try:
                f = open(dirpath + "textures\\" + texName, 'rb')
                return f
            except:
                print("failed to open texture: %s" %texName)
        
    def parse_textures(self, numTex):
        
        for i in range(numTex):
            texName = self.read_name()
            ext = texName[-4:]
            f = self.open_file(texName)
            if f:
                try:
                    tex = rapi.loadTexByHandler(f.read(), ext)
                    if tex is not None:
                        tex.name = texName
                        self.texList.append(tex)
                except:
                    tex = NoeTexture("dummy", 0, 0, 0, 0)
                    self.texList.append(tex)
            else:
                tex = NoeTexture("dummy", 0, 0, 0, 0)
                self.texList.append(tex)                
        
    def parse_materials(self, numMat):
        
        for i in range(numMat):
            matHeader = self.read_name(11)
            self.inFile.read('16f')
            self.inFile.readFloat()
            self.inFile.readByte()
        
    def parse_vertices(self, numVerts, vertType):
        
        if vertType == 0:
            vertBuff = self.inFile.readBytes(48*numVerts)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 48, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 48, 28)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 48, 40)        
        elif vertType == 1:
            vertBuff = self.inFile.readBytes(32*numVerts)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)
            
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
        
        
    def create_material(self, matNum, texNum):
        
        matName = "material[%d]" %len(self.matList)
        texName = self.texList[texNum].name
        material = NoeMaterial(matName, texName)
        material.setDefaultBlend(0)
        self.matList.append(material)
        return matName
        
    def parse_meshes(self, numMesh, vertType):
        
        for i in range(numMesh):
            meshName = self.read_name()
            texNum, matNum = self.inFile.read('2l')
            if vertType == 1:
                self.inFile.readUInt()
            numVerts, numIdx = self.inFile.read('2L')
            matName = self.create_material(matNum, texNum)
            self.parse_vertices(numVerts, vertType)
            idxBuff = self.parse_faces(numIdx)

            rapi.rpgSetMaterial(matName)
            #rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
            
    def parse_bones(self, numBones):
        
        for i in range(numBones):
            boneName = self.read_name()
    
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(8)
        meshType = self.inFile.readUInt()
        numMesh1, numMesh2, unk1, unk2, numTex, numMat, numBones, unk3, \
           typeMask = self.inFile.read('9L')
        self.inFile.seek(60, 1)
        self.parse_bones(numBones)
        self.parse_textures(numTex)
        self.parse_materials(numMat)
        if numMesh1:
            self.parse_meshes(numMesh1, 0)
        elif numMesh2:
            self.parse_meshes(numMesh2, 1)