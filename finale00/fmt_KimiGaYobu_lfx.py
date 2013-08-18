'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

_ENDIAN = 0 # 1 for big endian

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Kimi ga Yobu", ".lfx")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 0:
        return 0
    bs = NoeBitStream(data)
    try:
        idstring = noeStrFromBytes(bs.readBytes(3))
        if idstring == "LFX":
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
            
    def build_mesh(self, mesh):
        
        for matNum, numFaces, idxBuff in mesh.faceGroups:
            rapi.immBegin(noesis.RPGEO_TRIANGLE)
            #rapi.immBegin(noesis.RPGEO_POINTS)
            for i in range(numFaces):
                numIdx = idxBuff[i*13]
                
                for j in range(numIdx):
                    idx = (13 * i) + (j * 4)
                    normIdx = idxBuff[idx + 3]
                    vertIdx = idxBuff[idx + 1]
                    rapi.immNormal3f(mesh.normBuff, normIdx*12)
                    rapi.immVertex3f(mesh.vertBuff, vertIdx*12)
            rapi.immEnd()
            
    def read_name(self, n):
        
        string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)

    def read_tex_name(self):
        
        data = self.inFile.readBytes(28)
        return noeStrFromBytes(data.split(b"\x00")[0])
    
    def parse_materials(self, numMat):
        
        for i in range(numMat):
            self.inFile.read('19f')
            numTex = self.inFile.readByte()
            matName = self.read_name(40)
            for i in range(numTex):
                texName = self.read_tex_name()
            self.inFile.seek(48, 1)
            
            #print(matName, texName)
        
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts * 12)
    
    def parse_faces(self, numFaces):
        
        #return self.inFile.readBytes(numFaces * 26)
        return self.inFile.read("%dH" %(numFaces*13))
    
    def parse_face_groups(self, numGroups):

        faceGroups = []
        print(numGroups)
        for i in range(numGroups):
            matNum, unk = self.inFile.read('2H')
            numFaces = self.inFile.readUShort()
            idxBuff = self.parse_faces(numFaces)        
            
            faceGroups.append([matNum, numFaces, idxBuff])
        return faceGroups
    
    def parse_mesh(self):
        '''Can be a mesh or a bone'''

        mesh = Mesh()
        self.inFile.readShort()
        mesh.numVerts = self.inFile.readUShort()
        mesh.vertBuff = self.parse_vertices(mesh.numVerts)

        mesh.numNorms = self.inFile.readUShort()
        mesh.normBuff = self.inFile.readBytes(mesh.numNorms * 12)
        
        mesh.numUV = self.inFile.readUShort()
        mesh.uvBuff = self.inFile.readBytes(mesh.numUV * 8)
    
        unk = self.inFile.readUShort()
        self.inFile.readBytes(unk * 4)
        
        self.inFile.readByte()
        unk2 = self.inFile.readShort()
        self.inFile.readBytes(unk2 * 24)
        
        self.inFile.readShort()
        self.inFile.read('16f')
        self.inFile.seek(58, 1)
        
        print(self.inFile.tell())
        numGroups = self.inFile.readUShort()
        size = self.inFile.readUInt()
        mesh.faceGroups = self.parse_face_groups(numGroups)
        self.build_mesh(mesh)
        self.inFile.read('2H')
            
    def parse_bone(self):
        
        self.inFile.read('5H')
        self.inFile.readByte()
        self.inFile.readShort()
        self.inFile.read('16f')
        self.inFile.read('10f')
        
        count = self.inFile.readUInt()
        self.parse_unk(count)
        
        count2 = self.inFile.readUInt()
        self.parse_unk2(count2)
        
        count3 = self.inFile.readUInt()
        self.parse_unk3(count3)
        
        self.inFile.readUInt()
        unk1 = self.inFile.readShort()
        if unk1:        
            self.inFile.read('16f')
            self.inFile.read('2H')
            count4 = self.inFile.readUShort()
            self.parse_unk4(count4)
        self.inFile.read('4H')
        
    def parse_unk(self, count):
        
        return self.inFile.readBytes(count * 16)
    
    def parse_unk2(self, count):
        
        return self.inFile.readBytes(count * 16)
    
    def parse_unk3(self, count):
        
        return self.inFile.readBytes(count * 20)
    
    def parse_unk4(self, count):
        
        #self.inFile.readUInt()
        #self.inFile.readFloat()
        return self.inFile.readBytes(count * 8)
    
    def parse_object(self):
        '''Determine whether it's a mesh, bone, or something else'''
        
        while 1:
            self.inFile.readShort()
            if self.inFile.tell() == self.inFile.dataSize:
                break
            
            objName = self.read_name(40)
            self.inFile.readShort()
            check = self.inFile.readShort()
            if check:
                print("%s mesh" %objName)
                self.inFile.seek(-4, 1)
                self.parse_mesh()
            else:
                print("%s bone" %objName)
                self.inFile.seek(-2, 1)
                self.parse_bone()
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(3)
        modelType, unk, unk, numMat, unk = self.inFile.readBytes(5)
        
        size = self.inFile.readShort()
        #self.parse_materials(numMat)
        #self.inFile.seek(73, 1)
        self.inFile.seek(size)
        
        if modelType == 0x01:
            self.inFile.seek(51, 1)
            self.parse_mesh()
        elif modelType == 0x81:
            self.inFile.seek(9, 1)
            self.parse_object()
            
        
        
               