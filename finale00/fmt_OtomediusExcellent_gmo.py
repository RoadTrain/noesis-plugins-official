from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Otomedius Excellent", ".gmo")
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
        if idstring != "GXXM0301":
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
        
    def read_name(self):
        
        string = self.inFile.readBytes(64)
        return noeStrFromBytes(string)
    
    def parse_material(self, numMat):
        
        for i in range(numMat):
            
            #name = self.inFile.readString()
            #self.inFile.seek(38, 1)
            self.inFile.seek(64, 1)
            
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(96*numVerts)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 96, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 96, 12)
        #rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 96, 28)
        
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_frames(self, numMesh):
        
        for i in range(numMesh):
            name = self.read_name()
            self.inFile.readUInt()
            self.inFile.read('2l')
            self.inFile.seek(100, 1)
            self.inFile.read('16f')
            self.inFile.read('16f')
            self.inFile.read('16f')
            self.inFile.read('16f')
                
    def parse_meshes(self, numMesh):
        
        for i in range(numMesh):
            meshNum = self.inFile.readUInt()
            print(meshNum, self.inFile.tell())
            self.inFile.seek(28, 1)
            unk, numMat, unk, unk = self.inFile.read('4L')
            unk, numVerts, unk1, numIdx = self.inFile.read('4L')
            self.inFile.read('12f')
            self.inFile.seek(16, 1)
            
            self.parse_material(numMat)
            self.read_name()
            self.inFile.read('8L')
            self.inFile.read('16f')
            self.inFile.read('16f')
            self.inFile.seek(116, 1)
            
            count1, count2 = self.inFile.read('2L')
            self.inFile.seek(52, 1)
            self.parse_vertices(numVerts)
            idxBuff = self.parse_faces(numIdx)
            rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
            
            
            count = self.inFile.readUInt()
            while count > abs(meshNum + 2) or count == 0:
                count = self.inFile.readUInt()
                if self.inFile.tell() == self.inFile.dataSize:
                    break
            self.inFile.seek(-4, 1)
            
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.read_name()
        self.inFile.seek(16, 1)
        self.inFile.readUInt()
        numFrames = self.inFile.readUInt()
        self.inFile.readUInt()
        numMesh = self.inFile.readUInt()
        self.inFile.read('12f')
        self.parse_frames(numFrames)
        self.parse_meshes(numMesh)
        
        