from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject
import os

MODE = 0

def registerNoesisTypes():
    handle = noesis.register("Silkroad Online", ".bms")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel) #see also noepyLoadModelRPG
    noesis.logPopup()

    return 1

#check if it's this type based on the data
def noepyCheckType(data):
    
    if len(data) < 12:
        return 0
    bs = NoeBitStream(data)
    if bs.readBytes(12).decode("ASCII") != "JMXVBMS 0110":
        return 0
    return 1

def load_all_models(mdlList):
    '''Load all models'''

    #carry over from previous models
    matList = []
    texList = []

    dirPath = rapi.getDirForFilePath(rapi.getInputName())
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".bms")]
    for file in fileList:
        f = open(dirPath + file, 'rb')
        data2 = f.read()
        parser = SanaeParser(data2)
        parser.parse_file()
        matList.extend(parser.matList)
        texList.extend(parser.texList)
        mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(texList, matList))
    mdlList.append(mdl)    
    
def load_single_model(data, mdlList):
    '''Loads a single model. For testing purposes'''
    
    parser = SanaeParser(data)
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
class SanaeParser(SanaeObject):
    
    def __init__(self, data):
       
        super(SanaeParser, self).__init__(data)
        
    def read_name(self):
        
        return self.read_string(self.inFile.readUInt())
    
    def parse_vertices(self, numVerts, vertType):
        
        if vertType == 0:
            vertBuff = self.inFile.readBytes(44*numVerts)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 24)            
        elif vertType == 1024:
            vertBuff = self.inFile.readBytes(52*numVerts)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 24)
            
    def parse_faces(self, numIdx):
        
        idxBuff = self.inFile.readBytes(2*numIdx)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def parse_bones(self, numBones, numVerts):
        
        for i in range(numBones):
            boneName = self.read_name()
        if numBones:
            for i in range(numVerts):
                b1 = self.inFile.readByte()
                w1 = self.inFile.readUShort()
                b2 = self.inFile.readByte()
                w2 = self.inFile.readUShort()
                
    def load_texture(self, matName):
        
        #texPath, ext = os.path.splitext(self.abspath.replace("mesh", "mtrl"))
        #f = open(texPath + ".ddj")
        try:
            f = open(self.basename + ".ddj", 'rb')
            f.seek(20)
            tex = rapi.loadTexByHandler(f.read(), ".dds")
            if tex is not None:
                tex.name = matName
                self.texList.append(tex)           
                
            material = NoeMaterial(matName, matName)
            self.matList.append(material)             
        except:
            pass        

    def parse_file(self):
        
        idstring = self.inFile.readBytes(12)
        offVerts, offBones, offFaces, unkOff1, unkOff2, ofsbbox, unkOff4, \
                 unk1, unk2, unkOff5, unk3, unk4, unk5, vertType, unk7 \
                 = self.inFile.read('15L')
        meshName = self.read_name()
        matName = self.read_name()
        
        self.inFile.readUInt()
        
        self.inFile.seek(offVerts)
        numVerts = self.inFile.readUInt()
        self.parse_vertices(numVerts, vertType)
        
        self.inFile.seek(offBones)
        numBones = self.inFile.readUInt()
        self.parse_bones(numBones, numVerts)
        
        self.inFile.seek(offFaces)
        numFaces = self.inFile.readUInt()
        
        rapi.rpgSetMaterial(matName)
        self.parse_faces(numFaces*3)

        self.load_texture(matName)