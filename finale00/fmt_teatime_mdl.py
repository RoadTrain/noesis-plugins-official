'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import struct

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Teatime", ".mdl;.txt")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    bs = NoeBitStream(data)
    idstring = bs.readline().strip()
    if idstring == "3D_MODEL_FILE":
        return 1
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

class TTMaterial(object):
    
    pass

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.tempMats = []
        
    def build_materials(self):
        
        for mat in self.tempMats:
            
            material = NoeMaterial(mat.name, "")
            material.setTexture(mat.texturefile)
            self.matList.append(material)
        
    def readline(self):
        
        return self.inFile.readline().strip()
    
    def get_data(self):
        
        return self.inFile.readline().strip().split(":")[1]
    
    def get_fields(self):
        '''Get the fields in the model. Newer mdl formats have additional
        fields'''
        
        # save start of section
        curPos = self.inFile.tell()
        
        fields = []        
        line = self.readline()
        while line:
            data = line.split(":")
            field_name = data[0].lower()
            fields.append(field_name)
            line = self.readline()
            
        # go back to start of section
        self.inFile.seek(curPos)
        return fields
        
    def parse_materials(self, numMat):
        
        fields = self.get_fields()
        for i in range(numMat):
            mat = TTMaterial()
            for field in fields:
                field_name, value = self.readline().split(":")
                mat.__setattr__(field, value)
            self.tempMats.append(mat)
            self.readline() #empty line
            
    def parse_vertices(self, numVerts):
        
        #fields = self.get_fields()
        vertBuff = bytes()
        normBuff = bytes()
        uvBuff = bytes()
        for i in range(numVerts):
            verts = map(float, self.get_data().split(" "))
            norms = map(float, self.get_data().split(" "))
            uvs = map(float, self.get_data().split(" "))
            bones = map(int, self.get_data().split(" "))
            weights = map(float, self.get_data().split(" "))
            self.readline()
            
            vertBuff = b''.join([vertBuff, struct.pack('3f', *verts)])
            normBuff = b''.join([normBuff, struct.pack('3f', *norms)])
            uvBuff = b''.join([uvBuff, struct.pack('2f', *uvs)])
            
        rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
        rapi.rpgBindNormalBuffer(normBuff, noesis.RPGEODATA_FLOAT, 12)
        rapi.rpgBindUV1Buffer(uvBuff, noesis.RPGEODATA_FLOAT, 8)          
    
    def parse_faces(self):
        
        total_faces = int(self.get_data())
        numFaceGroups = int(self.get_data())
        for i in range(numFaceGroups):
            matNum = int(self.get_data())
            numFaces = int(self.get_data())
            
            numIdx = numFaces * 3
            idxBuff = bytes()
            for j in range(numFaces):
                indices = map(int, self.readline().split(" "))
                idxBuff = b''.join([idxBuff, struct.pack('3L', *indices)])
            
            matName = self.matList[matNum].name
            rapi.rpgSetName("mesh[%d]" %i)
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_UINT, numIdx, noesis.RPGEO_TRIANGLE, 1)
            
            # empty line
            self.readline()
            
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readline()
        line = self.inFile.readline() 
        while line:
            line = line.strip()
            if line == "[Material]":
                numMat = int(self.readline())
                self.parse_materials(numMat)
                self.build_materials()
            elif line == "[Vertex]":
                numVerts = int(self.readline())
                self.parse_vertices(numVerts)
            elif line == "[Index]":
                self.parse_faces()
            elif line == "[Shader]":
                print('shader')
            line = self.inFile.readline() 
        
        