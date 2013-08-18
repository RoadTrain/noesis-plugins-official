from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Twelve Sky 2", ".tsmdl")
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
        
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(32*numVerts)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
        rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)
        
    def parse_animations(self, numAnims):
        
        self.inFile.readBytes(64*numAnims)
    
    def parse_bones(self, numBones):
        
        self.inFile.readBytes(32*numBones)
    
    def parse_faces(self, numIdx):
        
        idxBuff = self.inFile.readBytes(numIdx * 2)
        return idxBuff
        
    def parse_file(self):
        '''Main parser method'''

        rapi.rpgSetMaterial(self.basename)
        header, meshType = self.inFile.read('2L')       
        if meshType == 0:
            self.inFile.read('9f')
            self.inFile.read('76B')
            numBones, numVerts, numUnk = self.inFile.read('3L')
            numIdx = self.inFile.readUInt() * 3
            self.inFile.read('40B')            
            print(numVerts, numBones, numIdx)
            self.parse_vertices(numVerts)
            self.parse_bones(numBones)
            idxBuff = self.parse_faces(numIdx)
        
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        elif meshType == 1:
            print("mobject")
            self.inFile.read('9f')
            self.inFile.read('76B')
            numAnims, numVerts, numUnk = self.inFile.read('3L')
            numIdx = self.inFile.readUInt() * 3
            
            print(numAnims, numVerts, numIdx)
            
            #self.parse_animations(numAnims)
            #print(self.inFile.tell())
            self.parse_vertices(numVerts)
            self.plot_points(numIdx)
            #print(self.inFile.tell())
            #idxBuff = self.parse_faces(numIdx)
            
            #print(self.inFile.tell())
            
            