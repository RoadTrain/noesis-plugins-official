from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Valkyie Sky", ".xml")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
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

class SanaeParser(SanaeObject):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        super(SanaeParser, self).__init__(data)
        
    def read_name(self):
        
        string = self.inFile.readString()
        padding = 80 - len(string) - 1
        self.inFile.seek(padding, 1)
        return string
    
    def parse_positions(self, numVerts):
        
        buff = self.inFile.readBytes(12*numVerts)
        rapi.rpgBindPositionBuffer(buff, noesis.RPGEODATA_FLOAT, 12)
        
    def parse_normals(self, numNorms):
        
        buff = self.inFile.readBytes(12*numNorms)
        rapi.rpgBindNormalBuffer(buff, noesis.RPGEODATA_FLOAT, 12)
        
    def parse_uv(self, numUV):
        
        buff = self.inFile.readBytes(8*numUV)
        rapi.rpgBindUV1Buffer(buff, noesis.RPGEODATA_FLOAT, 8)
        
    def parse_faces(self, numFaces):
        
        idxBuff = bytes()
        for i in range(numFaces):
            self.inFile.readUInt()
            idxBuff += self.inFile.readBytes(12)
            
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_UINT, numFaces * 3, noesis.RPGEO_TRIANGLE, 1)
            
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.read_name()
        self.inFile.read('4L')
        numSects = self.inFile.readUInt()
        self.inFile.read('4L')
        
        for i in range(numSects):
            self.read_name()
        self.inFile.readUInt()
        if numSects == 1:
            self.inFile.readUInt()
        self.inFile.read('9f')
        self.inFile.read('5L')
        
        self.inFile.seek(320, 1)
        self.inFile.read('9f')
        self.inFile.read('5L')        
        
        texName = self.read_name()
        self.inFile.seek(320, 1)
        self.inFile.seek(220, 1)
        prop = self.read_name()
        if prop == "Particle_View":
            self.inFile.seek(220, 1)
            editable = self.read_name()
        
        meshType = self.inFile.readUInt()
        if meshType in [1,2]:
            self.inFile.seek(184, 1)
            numVerts, numNorms, numUV, numIdx, numFaces, matNum, \
                numUnk1, numUnk2 = self.inFile.read('8L')
            self.parse_positions(numVerts)
            self.parse_normals(numNorms)
            self.parse_uv(numUV)
            self.parse_faces(numFaces)
            #self.parse_indices(numIdx)
            self.plot_points(numVerts)