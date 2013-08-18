'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import os

MODE = 0

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Dark Blood", ".prt")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    return 1

def load_all_models(mdlList):
    '''Load all models'''

    #carry over from previous models
    matList = []
    texList = []

    dirPath = rapi.getDirForFilePath(rapi.getInputName())
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".prt")]
    for file in fileList:
        f = open(dirPath + file, 'rb')
        data2 = f.read()
        parser = SanaeParser(data2, file)
        parser.parse_file()
        matList.extend(parser.matList)
        texList.extend(parser.texList)
        mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(texList, matList))
    mdlList.append(mdl)    
    
def load_single_model(data, mdlList):
    '''Loads a single model. For testing purposes'''
    
    filename = rapi.getExtensionlessName(rapi.getInputName())
    parser = SanaeParser(data, filename)
    parser.parse_file()
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

class Mesh(object):
    
    def __init__(self):
        
        self.name = ""
        self.numIdx = 0
        self.numVerts = 0
        self.vertSize = 0
        self.vertBuff = bytes()
        self.idxBuffs = {}
        self.materials = []

class SanaeParser(object):
    
    def __init__(self, data, filename):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        self.modelName = filename
               
    def build_mesh(self):
        
        for mesh in self.meshList:
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
            rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
            rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)            
            
            for matNum in mesh.idxBuffs:
                
                matName = mesh.materials[matNum].name
                
                idxBuff = mesh.idxBuffs[matNum]
                numIdx = len(idxBuff) // 2
                rapi.rpgSetMaterial(matName)
                rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)               
        
    def read_name(self):
        
        length = self.inFile.readUByte() - 128
        string = self.inFile.readBytes(length)
        return noeStrFromBytes(string)
    
    def read_tag(self):
        
        tag = self.inFile.readUByte() #0x81
        high = tag & 0b11110000
        low = tag & 0b00001111
        return high, low
    
    def read_null(self):
        
        char = self.inFile.readByte()
        while char:
            char = self.inFile.readByte()
        
    def parse_materials(self, numMat):
            
        matList = []
        for i in range(numMat):
            matName = "%s[%d]" %(self.modelName, len(self.matList))
            self.inFile.read('17f')
            
            material = NoeMaterial(matName, "")
            matList.append(material)
            self.matList.append(material)
        return matList
        
        #matName = texName[0]
        
        #material = NoeMaterial(matName, "")
        
        #diffName = ".".join([texName[0], texName[1]])
        #material.setTexture(diffName)
        
        #normName = ".".join([texName[0] + "_dye", texName[1]])
        #material.setNormalTexture(normName)
        #self.matList.append(material)
        
        return matList
    
    def parse_textures(self, numMat, mesh):
        
        for i in range(numMat):
            texName = self.read_name()
            mesh.materials[i].setTexture(texName)   
            
            name, ext = os.path.split(texName)
            normName = name + "_dye" + ext
            mesh.materials[i].setNormalTexture(normName)
        
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts*32)
                        
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_unk2(self, count):
        
        self.inFile.readBytes(count*12)
        
    def parse_unk3(self, num):
        
        LIMIT = 128
        for i in range(num):
            tag, value = self.read_tag()
            self.inFile.readBytes(value)
            count = self.inFile.readUInt()
            if count > LIMIT:
                self.parse_unk4(count, 1)
            else:
                self.parse_unk4(count)                
                
    def parse_unk4(self, count, large=0):
        
        if large:
            self.inFile.readShort()
            self.inFile.readBytes(count*4) #integers
            self.inFile.readShort()
            self.inFile.readBytes(count*4)
        else:
            self.inFile.readByte()
            self.inFile.readBytes(count*4)
            self.inFile.readByte()
            self.inFile.readBytes(count*4)
        self.inFile.read('16f') #matrix?
        
    def parse_face_materials(self, numFaces, idxBuff):
        
        idxBuffs = {}
        self.inFile.readBytes(numFaces * 4)
        tag, value = self.read_tag()
        for i in range(value):
            matNum, faceStart, faceCount, unk, unk = self.inFile.read('5L')
            start = faceStart * 6
            end = start + (faceCount)*6
            tempBuff = idxBuff[start:end]
            idxBuffs[i] = tempBuff
        return idxBuffs
                
    def parse_mesh(self):
        
        self.inFile.seek(6, 1)
        
        mesh = Mesh()            
        mesh.numVerts = self.inFile.readUInt()
        numFaces = self.inFile.readUInt()
        
        mesh.vertBuff = self.parse_vertices(mesh.numVerts)
        mesh.numIdx = numFaces * 3
        mesh.idxBuff = self.parse_faces(mesh.numIdx)
        #face material indices
        mesh.idxBuffs = self.parse_face_materials(numFaces, mesh.idxBuff)
        
        numMat = self.inFile.readUInt()
        self.inFile.readByte() #0x80
        mesh.materials = self.parse_materials(numMat)
        self.inFile.readByte()
        self.parse_textures(numMat, mesh)
        self.parse_unk2(numFaces)
        
        #unk 3
        numSect = self.inFile.readUInt()
        self.inFile.readUInt()
        self.parse_unk3(numSect)
        self.meshList.append(mesh)
    
    def parse_bones(self, numBones):
        
        pass
        
    def parse_file(self):
        '''Main parser method'''
        
        self.inFile.readUShort()
        self.read_null()
        while not self.inFile.checkEOF():
            tag = self.inFile.readUByte()
            if tag == 0x01:        
                self.parse_mesh()
            elif tag == 0x80:
                break
        
        self.build_mesh()