from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject
import os

#if you want to load all models in file, set it to 1
#otherwise, set it to 0
MODE = 0

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Age of Wushu", ".xmod")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel) #see also noepyLoadModelRPG
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin.'''
    return 1

def load_all_models(mdlList):
    '''Load all models'''

    #carry over from previous models
    matList = []
    texList = []
    
    ##load face
    #facePath = "E:\\My Documents\\Workspace\\sample\\Age of Wushu\\g_face.xmod"
    #f = open(facePath, 'rb')
    #data2 = f.read()
    #parser = AgeOfWushu_XMOD(data2)
    #parser.parse_file()
    #material = NoeMaterial("g_face", "E:\\My Documents\\Workspace\\sample\\Age of Wushu\\g_face_1.dds")
    #matList.append(material)
    
    #load the outfit
    
    dirPath = rapi.getDirForFilePath(rapi.getInputName())
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".xmod")]    
    for file in fileList:
        f = open(dirPath + file, 'rb')
        data2 = f.read()
        parser = AgeOfWushu_XMOD(data2)
        parser.parse_file()
        matList.extend(parser.matList)
        texList.extend(parser.texList)
        mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(texList, matList))
    mdlList.append(mdl)    
    
def load_single_model(data, mdlList):
    '''Loads a single model. For testing purposes'''
    
    parser = AgeOfWushu_XMOD(data)
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

class AgeOfWushu_XMOD(SanaeObject):
    
    def __init__(self, data):    
        super(AgeOfWushu_XMOD, self).__init__(data)
        
    def check_padding(self):
        
        unk = self.inFile.readUInt()
        while unk == -1:
            unk = self.inFile.readUInt()
        return unk

    def read_name(self):
        
        length = self.inFile.readUInt()
        string = self.inFile.readBytes(length)
        try:
            return noeStrFromBytes(string)
        except:
            return "mesh"
        
    def parse_textures(self, numTex):
        
        for i in range(numTex):
            label = self.read_name()
            texName = self.read_name()
    
    def parse_materials(self, matName, mb):

        if mb[0] == 0x05 and mb[1] in [0x14, 0x54, 0x74, 0x94]:
            self.inFile.read('7f')
        elif mb[0] == 0x05 and mb[1] == 0x10:
            self.inFile.read('6f')
        elif mb[0] == 0x05 and mb[1] == 0x15:
            self.inFile.read('8f')
        elif mb[0] == 0x15:
            self.inFile.read('10f')
        elif mb[1] == 0x34:
            self.inFile.read('13f')
        elif mb[1] == 0x95:
            self.inFile.read('8f')
        else:
            print("unknown mb")        
        if mb[1] == 0x04:
            pass
        else:
            material = NoeMaterial(matName, "")
            label = self.read_name()
            texName = self.read_name()            
            #f = open(self.dirpath + texName, 'rb')
            #tex = rapi.loadTexByHandler(f.read(), ".dds")
            #if tex is not None:
                #tex.name = texName
                #self.texList.append(tex)
            #f.close()
            
            material.setTexture(texName)
            self.matList.append(material)            
            if mb[1] == 0x54:
                self.parse_textures(1)
            elif mb[1] == 0x74:
                self.parse_textures(2)
            elif mb[1] in [0x94, 0x95]:
                self.parse_textures(1)
                self.inFile.read('2L')
            elif mb[1] == 0x34:
                self.parse_textures(3)
                                
    def parse_unskinned_materials(self, matName):
        
        self.inFile.read('6f')        
        material = NoeMaterial(matName, "")
        self.read_name()
        texName = self.read_name()
        
        material.setTexture(texName)
        self.matList.append(material)
    
    def parse_faces(self, numIdx):
        
        idxBuff = self.inFile.readBytes(numIdx * 2)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
    
    def parse_vertices(self, numVerts, mb, vb):
        
        print(mb)
        if mb[0] == 0x05  and mb[1] == 0x04:
            #print("vertSize: 24")
            vertBuff = self.inFile.readBytes(numVerts*24)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 24, 0)
        elif mb[0] == 0x15 and vb[1] == 0x15:
            #print("vertSize: 56")
            vertBuff = self.inFile.readBytes(numVerts*56)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 48)
        elif mb[0] in [0x05, 0x0A, 0x15]:
            #print("vertSize: 32")
            vertBuff = self.inFile.readBytes(numVerts * 32)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)        
        elif mb[0] == 0:
            #print("vertSize: 36")
            vertBuff = self.inFile.readBytes(numVerts*36)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 0)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 2)      
        elif mb[0] == 1:
            #print("vertSize: 40")
            vertBuff = self.inFile.readBytes(numVerts * 40)
        elif mb[0] == 0x55:
            vertBuff = self.inFile.readBytes(numVerts*64)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 64, 0)    
        else:
            print("Unknown")
            
    def parse_unskinned_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(numVerts*32)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
        rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)           
            
    def parse_weights(self, numVerts):
        
        weightBuff = self.inFile.readBytes(numVerts*32)
        
    def parse_bones(self, size):
        
        self.inFile.seek(size, 1)
           
    def parse_unskinned_mesh(self):
        
        meshName = "mesh"
        matName = meshName
        rapi.rpgSetMaterial(matName)
        check = self.inFile.readInt() #important?
        while check != -1:
            print(self.read_name())
            self.inFile.readUInt()
            self.inFile.readUInt()
            self.inFile.read('9f')
            print(self.inFile.tell())
            check = self.inFile.readInt()
        print(self.inFile.tell())
        self.inFile.read('6f')
        unk2 = self.inFile.readUInt()
        if unk2:
            self.read_name()
        self.inFile.read('2L')        
        numVerts = self.inFile.readUInt()
        print("%d verts" %numVerts)
        self.parse_unskinned_vertices(numVerts)
        numIdx = self.inFile.readUInt()
        self.parse_faces(numIdx)
        #if bBones == 1:
            #self.parse_weights(numVerts)
            #sectionSize = self.inFile.readUInt()
            #self.parse_bones(sectionSize)
        print(self.inFile.tell())
        self.parse_unskinned_materials(matName)           
                    
    def parse_skinned_mesh(self, unk2):
        
        check = self.inFile.readInt()
        meshName = self.read_name()
        matName = meshName
        rapi.rpgSetMaterial(matName)        
        #rapi.rpgSetName(meshName)
        self.inFile.readUInt()
        vb = self.inFile.read('4B')
        #print(vb[1])
        if vb[1] == 0x20:
            self.inFile.seek(40 + unk2*40, 1)
        elif vb[1] in [0x10, 0x15]:
            self.inFile.seek(40, 1)
        check = self.inFile.readInt()
        while check != -1:
            self.read_name()
            self.inFile.readUInt()
            vb = self.inFile.read('4B')
            self.inFile.read('10f')
            check = self.inFile.readInt()
            
        self.inFile.read('6f')
        numMesh = self.inFile.readUInt()
        for i in range(numMesh):
            print(self.inFile.tell())
            self.read_name()
            self.inFile.readUInt()
            mb = self.inFile.read('4B')
            print(self.inFile.tell())
            numVerts = self.inFile.readUInt()
            print("%s: %d verts, bones: " %(meshName, numVerts), vb[3] == 1)
            self.parse_vertices(numVerts, mb, vb)
            print(self.inFile.tell())
            numIdx = self.inFile.readUInt()
            self.parse_faces(numIdx)
            
            if vb[2] == 1:
                self.parse_weights(numVerts)
                sectionSize = self.inFile.readUInt()
                self.parse_bones(sectionSize)
            print(self.inFile.tell())
            self.parse_materials(matName, mb)
            
            #rapi.rpgClearBufferBinds()
        
                
    def parse_file(self):

        idstring = self.inFile.readBytes(4)
        meshType = self.inFile.readUByte()
        self.inFile.readUByte()
        self.inFile.readUShort()
        self.inFile.readUInt()
        self.inFile.readUInt()
        modelName = self.read_name()
        self.inFile.readUInt()
        unk2 = self.inFile.readUInt()
        self.inFile.read('7f')        
        print("Detected mesh type: %d" %meshType)
        if meshType in [0, 1]:
            self.parse_unskinned_mesh()
        elif meshType == 2:
            self.parse_skinned_mesh(unk2)
        else:
            print("Unknown mesh type: %d" %meshType)