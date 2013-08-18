'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

_ENDIAN = 0 # 1 for big endian

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Gensou Rondou", ".dgo")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 0:
        return 0
    bs = NoeBitStream(data)
    try:
        idstring = noeStrFromBytes(bs.readBytes(4))
        if idstring == "L3DO":
            return 1
        return 0
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

class Mesh(object):
    '''A generic mesh object, for convenience'''
    
    def __init__(self):
        
        self.positions = bytes()
        self.normals = bytes()
        self.uvs = bytes()
        self.numVerts = 0
        self.numIdx = 0
        self.idxBuff = bytes()
        self.matName = ""
        self.meshName = ""

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data, _ENDIAN)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        self.filename = rapi.getLocalFileName(rapi.getInputName())
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)
        
    def parse_vertices(self, numVerts):
        
        pass
    
    def parse_faces(self, numIdx):
        
        pass
    
    def parse_submeshes(self, numSubmesh):
        
        for i in range(numSubmesh):
            name1 = self.read_name()
            self.inFile.readUInt()
            name2 = self.read_name()
            self.inFile.readUInt()
            
            numFaces = self.inFile.readUInt()
            numIdx = self.inFile.readUInt()
            self.parse_faces(numIdx)
            count7 = self.inFile.readUInt()
            idxBuff = self.parse_unk7(count7)
            
            self.inFile.readUInt()
            numVerts = self.inFile.readUInt()
            vertBuff = self.inFile.readBytes(numVerts * 12)
            numNorms = self.inFile.readUInt()
            normBuff = self.inFile.readBytes(numNorms * 12)
            self.inFile.read('3f')
            print(count7)
            #with(open("out.txt", 'a')) as f:
                #f.write("==%d %d==\n " %(numVerts, numNorms))
                #data = NoeBitStream(idxBuff)
                #while not data.checkEOF():
                    #f.write("%d " %(data.readInt()))
                    #f.write("%d " %(data.readInt()))
                    #f.write("%d\n" %(data.readInt()))
            rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
            #rapi.rpgCommitTriangles(None, noesis.RPGEODATA_UINT, numVerts, noesis.RPGEO_POINTS, 1)
            #rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_UINT, count7 // 3, noesis.RPGEO_TRIANGLE, 1)
            
    def parse_meshes(self, numMesh):
        
        for i in range(1):
            meshName = self.read_name()
            shaderInfo = self.read_name()
            count2 = self.inFile.readUInt()
            self.parse_unk2(count2)
            
            count3 = self.inFile.readUInt()
            self.parse_unk3(count3)
            numSubmesh = self.inFile.readUInt()
            self.parse_submeshes(numSubmesh)
                
    def parse_unk1(self):
        
        self.inFile.readUInt() #null
        count = self.inFile.readUInt()
        
        if count == 6:
            self.inFile.seek(416, 1)
        elif count == 5:
            self.inFile.seek(352, 1)
        self.inFile.readUInt()
    
    def parse_unk2(self, count):
        
        self.inFile.readBytes(count * 4)
        
    def parse_unk3(self, count):
        
        self.inFile.readBytes(count * 8) # 2 floats
        
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 4)
        
    def parse_unk7(self, count):
        
        idxBuff = bytes()
        for i in range(count):
            idxBuff += self.inFile.readBytes(4)
            self.inFile.readBytes(12)
        return idxBuff
#        return self.inFile.readBytes(count * 16)
        
    def parse_file(self):
        '''Main parser method'''
        
        self.inFile.readBytes(4)
        self.inFile.readUInt()
        self.inFile.readUInt()
        texInfo = self.read_name()
        self.parse_unk1()
        
        #skip
        #self.inFile.seek(144)
        numMesh = self.inFile.readUInt()
        self.parse_meshes(numMesh)
        
        print(self.inFile.tell())