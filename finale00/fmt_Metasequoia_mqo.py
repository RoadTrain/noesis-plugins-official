from inc_noesis import *
import noesis
import rapi
from struct import *
import re
import codecs

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Metasequoia", ".mqo")
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
    inputName = rapi.getInputName()
    with codecs.open(inputName, 'rb', encoding="Shift-JIS") as file:
        parser = SanaeParser(file)
        parser.parse_file()
    #parser = SanaeParser(data)
    #parser.parse_file()        
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
        
        #self.inFile = NoeBitStream(data)
        self.inFile = data
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
        
    def split_field(self, field):
        '''Given a field of the form "name(values)", return a list of the form
        ["name", "values"]'''
        
        match = re.match(r'(\w[\w\d_]*)\((.*)\)$', field)
        return list(match.groups()) if match else [field]
    
    def tokenize(self, line):
        
        return re.split(r'\s+(?=[^()]*(?:\(|$))', line)
        
    def skip_lines(self, string):
        '''Skip lines until it starts with string'''
        
        line = self.inFile.readline()
        while not line.strip().startswith(string):
            line = self.inFile.readline()
        return line
    
    def build_mesh_tris(self, vertList, triBuffs):
        
        #iterate over all of the idxBuffs based on matNum
        for matNum in triBuffs:
            numIdx = 0 
            idxBuff = bytes()
            vertBuff = bytes()
            idxList = triBuffs[matNum]["idxList"]
            uvBuff = triBuffs[matNum]["uvBuff"]
            for index in idxList:
                coords = vertList[index]
                vertBuff += struct.pack("3f", *(map(float, coords)))
                idxBuff += struct.pack("L", numIdx)
                numIdx += 1
            
            matName = self.matList[matNum].name
            rapi.rpgSetMaterial(matName)
            rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
            if uvBuff:
                rapi.rpgBindUV1Buffer(uvBuff, noesis.RPGEODATA_FLOAT, 8)
            
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_UINT, numIdx, noesis.RPGEO_TRIANGLE, 1)
            
    def build_mesh_quads(self, vertList, quadBuffs):
        
        for matNum in quadBuffs:
            numIdx = 0 
            idxBuff = bytes()
            vertBuff = bytes()
            idxList = quadBuffs[matNum]["idxList"]
            uvBuff = quadBuffs[matNum]["uvBuff"]
            for index in idxList:
                coords = vertList[index]
                vertBuff += struct.pack("3f", *(map(float, coords)))
                idxBuff += struct.pack("L", numIdx)
                numIdx += 1
            
            matName = self.matList[matNum].name
            rapi.rpgSetMaterial(matName)
            rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
            
            if uvBuff:
                rapi.rpgBindUV1Buffer(uvBuff, noesis.RPGEODATA_FLOAT, 8)
            
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_UINT, numIdx, noesis.RPGEO_QUAD, 1)        
        
        
    def parse_materials(self, numMat):
        
        for i in range(numMat):
            line = self.tokenize(self.inFile.readline().strip())
            
            matName = line[0]
            material = NoeMaterial(matName, "")
            for field in line[1:]:
                attr, value = self.split_field(field)
                if attr == "tex":
                    material.setTexture(value.strip('"'))            
            self.matList.append(material)
    
    def parse_faces(self, numFaces):
        
        #I use a dictionary to store index buffers based on material index
        #The keys are the matNum, and the value is a bytes index buffer
        triBuffs = {}
        quadBuffs = {}
        for i in range(numFaces):
            line = self.tokenize(self.inFile.readline().strip())
            numVerts = int(line[0])
            verts = self.split_field(line[1])[1].split()
            
            if len(line) > 2:
                matNum = int(self.split_field(line[2])[1])
            else:
                matNum = -1
            
            uvs = []
            if len(line) > 3:
                uvs = self.split_field(line[3])[1].split()
                
            if numVerts == 3:
                if not matNum in triBuffs:
                    triBuffs[matNum] = {"idxList" : [], "uvBuff" : bytes()}
                triBuffs[matNum]["idxList"].extend(map(int, verts))
                if uvs:
                    triBuffs[matNum]["uvBuff"] += struct.pack("6f", *(map(float, uvs)))
            elif numVerts == 4:
                if not matNum in quadBuffs:
                    quadBuffs[matNum] = {"idxList" : [], "uvBuff" : bytes()}
                quadBuffs[matNum]["idxList"].extend(map(int, verts))
                if uvs:
                    quadBuffs[matNum]["uvBuff"] += struct.pack("8f", *(map(float, uvs)))
        return triBuffs, quadBuffs
        
    def parse_binary_vertices(self, numVerts):
        
        print("binary vertices", numVerts)
        self.inFile.readline()
        self.inFile.seek(numVerts*12, 1)
    
    def parse_vertices(self, numVerts):
        
        vertList = []
        for i in range(numVerts):
            coords = self.inFile.readline().strip().split()
            vertList.append(coords)
        return vertList
    
    def parse_weit(self):
        
        line = self.inFile.readline().strip()
        while not line.startswith("}"):
            line = self.inFile.readline().strip()
    
    def parse_mesh(self, line):

        line = self.tokenize(line)
        meshName = line[1]
        rapi.rpgSetName(meshName)
        line = self.inFile.readline().strip()
        while not line.startswith("}"):
            if not line:
                continue
            args = line.split()
            if args[0] == "BVertex":
                numVerts = int(args[1])
                self.parse_binary_vertices(numVerts)
            elif args[0] == "vertex":
                numVerts = int(args[1])
                vertList = self.parse_vertices(numVerts)        
            elif args[0] == "weit":
                self.parse_weit()
            line = self.inFile.readline().strip()

        line = self.skip_lines("face")
        numFaces = int(line.strip().strip('{').split()[1])
        triBuffs, quadBuffs = self.parse_faces(numFaces)
        self.build_mesh_tris(vertList, triBuffs)
        self.build_mesh_quads(vertList, quadBuffs)
        
    def parse_file(self):
        '''Main parser method'''
        
        line = self.inFile.readline()
        while line:
            line = line.strip()
            if line.startswith("Scene"):
                print("scene")
            elif line.startswith("Material"):
                numMat = int(line.strip().strip('{').split()[1])
                self.parse_materials(numMat)
            elif line.startswith("Object"):
                self.parse_mesh(line)
            line = self.inFile.readline()