'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import os

MODE = 1

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Rusty Hearts", ".mgm")
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
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".mgm")]
    for filename in fileList:
        f = open(dirPath + filename, 'rb')
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
    
    inputName = rapi.getLocalFileName(rapi.getInputName())
    filename, ext = os.path.splitext(inputName)
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
        
        string = bytes()
        for i in range(n):
            string += self.inFile.readBytes(1)
            self.inFile.readBytes(1)
        return noeStrFromBytes(string)
    
    def read_ustring(self):
        
        string = bytes()
        char = self.inFile.readBytes(1)
        while char != b'\x00':
            string += char
            self.inFile.readBytes(1)
            char = self.inFile.readBytes(1)
        return noeStrFromBytes(string)
            
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(32*numVerts)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
        rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)
    
    def parse_faces(self, numIdx):
    
        return self.inFile.readBytes(numIdx*2)
        
    def parse_skinned_mesh(self):
        
        len1, len2, unk1, unk2 = self.inFile.read('4L')
        meshName = self.read_name(len1)
        name = self.read_name(len2)
        
        matNum = self.inFile.readUInt() - 1
        matName = self.read_name(self.inFile.readUInt())
        numVerts = self.inFile.readUInt()
        numIdx = self.inFile.readUInt() * 3
        self.inFile.seek(0xF, 1)
        meshType = self.inFile.readUInt()
        
        self.parse_vertices(numVerts)
        idxBuff = self.parse_faces(numIdx)
        try:
            matName = self.matList[matNum].name
            rapi.rpgSetMaterial(matName)
        except:
            pass
        rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
    
    def parse_static_mesh(self):
        
        len1, unk1, unk2, unk3 = self.inFile.read('4L')
        name1 = self.read_name(len1)
        numMesh = self.inFile.readUInt()
        
        for i in range(numMesh):
            len2 = self.inFile.readUInt()
            name2 = self.read_name(len2)
            numVerts = self.inFile.readUInt()
            numIdx = self.inFile.readUInt() * 3
            matNum = self.inFile.readUInt()
            self.inFile.seek(51, 1)
            self.parse_vertices(numVerts)
            idxBuff = self.parse_faces(numIdx)
            
            matName = self.matList[matNum].name
            rapi.rpgSetMaterial(matName)
            rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
            
    def parse_mat_property(self, numProps):
        
        for i in range(numProps):
            #propName = self.inFile.readString()
            #self.inFile.readString()
            #self.inFile.seek(36, 1)
            #print(propName)
            self.inFile.seek(52, 1)
    
    def parse_materials(self, filename):
        
        dirPath = rapi.getDirForFilePath(rapi.getInputName())
        unk, numMat = self.inFile.read('2L')
        for i in range(numMat):
            unk1, len1, len2, = self.inFile.read('3L')
            name1 = self.read_name(len1)
            matName = self.read_name(len2)
            matName = "%s[%d]" %(filename, i)
            
            self.inFile.seek(5, 1)
            numProps, unk, unk = self.inFile.read('3L')
            self.parse_mat_property(numProps)
            self.inFile.readString()
            self.inFile.seek(21, 1)
            
            self.inFile.seek(4, 1) #skip curdir
            texName = self.read_ustring()
            texPath = dirPath + texName
            material = NoeMaterial(matName, texPath)
            self.matList.append(material)
        
    def parse_file(self, filename):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(5)
        count1, count2 = self.inFile.read('2L')
        
        offsets = self.inFile.read('%dL' %count2)
        sizes = self.inFile.read('%dL' %count2)
        types = self.inFile.read('%dL' %count2)
        
        for i in range(count2):
            offset = offsets[i]
            self.inFile.seek(offset)
            type = types[i]
            
            if type == 1:
                self.parse_materials(filename)
            elif type == 5:
                self.parse_static_mesh()
            elif type == 6:
                self.parse_skinned_mesh()