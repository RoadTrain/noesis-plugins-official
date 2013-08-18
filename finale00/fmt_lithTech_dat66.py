'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("LithTech map v66", ".dat")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    bs = NoeBitStream(data)
    idstring = bs.readUInt()
    if idstring != 66:
        return 0
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

class Mesh(object):
    
    def __init__(self):
        
        self.triCount = 0
        self.quadCount = 0
        self.numVerts = 0
        self.vertBuff = bytes()
        self.triBuff = bytes()
        self.quadBuff = bytes()

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        
    def plot_points(self, numVerts):
            
        rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, numVerts, noesis.RPGEO_POINTS, 1)    
        
    def read_info(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)        
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUShort())
        return noeStrFromBytes(string)
    
    def build_mesh(self, mesh):
    
        rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 24, 0)
        rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 24, 12)
        #rapi.rpgSetName(mesh.name)
        #self.plot_points(mesh.numVerts)
        if mesh.triCount:
            rapi.rpgCommitTriangles(mesh.triBuff, noesis.RPGEODATA_USHORT,  mesh.triCount, noesis.RPGEO_TRIANGLE, 1)
        if mesh.quadCount:
            rapi.rpgCommitTriangles(mesh.quadBuff, noesis.RPGEODATA_USHORT, mesh.quadCount, noesis.RPGEO_QUAD_ABC_ACD, 1)
        
    def parse_materials(self, numMat):
            
        for i in range(numMat):
            name = self.inFile.readString()
            #print(name)
        
    def parse_textures(self, numTex):
            
        pass    
        
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts * 24)
    
    def parse_face_info(self, numFaces):
        
        faceInfo = []
        for i in range(numFaces):
            n = self.inFile.readByte()
            n += self.inFile.readByte()
            faceInfo.append(n)
        return faceInfo
        
    def parse_faces(self, mesh):
        
        triCount = 0
        quadCount = 0
        triBuff = bytes()
        quadBuff = bytes()        
        for numIdx in self.faceInfo:
            self.inFile.read('3f')
            count = self.inFile.readShort()
            if count:
                self.inFile.read('4H')
            else:
                self.inFile.readUInt()
            matNum = self.inFile.readUInt()
            
            if numIdx == 3:
                triCount += numIdx
                for i in range(numIdx):
                    triBuff = b''.join([triBuff, self.inFile.readBytes(2)])
                    self.inFile.seek(3, 1)
            elif numIdx == 4:
                quadCount += numIdx
                for i in range(numIdx):
                    quadBuff = b''.join([quadBuff, self.inFile.readBytes(2)])
                    self.inFile.seek(3, 1)                
            else:
                self.inFile.readBytes(numIdx * 5)
                
        mesh.triCount = triCount
        mesh.quadCount = quadCount
        mesh.triBuff = triBuff
        mesh.quadBuff = quadBuff
        
    def parse_unk3(self, count):

        for i in range(count):
            self.inFile.seek(50, 1)
            flag = self.inFile.readByte()
            if flag:
                pan = self.read_name()
                value = self.read_name()
            self.inFile.readShort()
        
    def parse_unk4(self, count):
        
        for i in range(count):
            portalName = self.read_name()
            self.inFile.seek(30, 1)
            
    def parse_unk6(self, count):
       
        for i in range(count):
            unk1 = self.inFile.readShort()
            if unk1 != -1:
                for j in range(unk1):
                    self.inFile.readShort()
                    count1 = self.inFile.readShort()
                    self.inFile.readBytes(count1)
            else:
                self.inFile.readShort()
            count2 = self.inFile.readUInt()
            self.inFile.readBytes(count2 * 4)
            self.inFile.readFloat()
            
    def parse_unk11(self, count):
        
        for numIdx in self.faceInfo:
            
            self.inFile.read('3f')
            self.inFile.seek(6, 1)
            self.inFile.readUInt()
            self.inFile.seek(20, 1)
            
    def parse_meshes(self, numMesh):
        
        #numMesh = 1
        for i in range(numMesh):
            mesh = Mesh()
            mesh.offset = self.inFile.tell()
            nextMeshOfs = self.inFile.readUInt()
            
            self.inFile.seek(32, 1)
            self.inFile.read('2L')
            meshName = self.read_name()
            numVerts, unk2, unk3, unk4, numFaces, unk6, numIdx, unk8, unk9, \
                unk10, unk11, unk12 = self.inFile.read("12L")
            self.inFile.read("9f")
            
            #get texture paths
            strLen, numTex = self.inFile.read('2L')
            self.inFile.seek(strLen, 1)
            
            # indices per face
            #print(self.inFile.tell(), "face info")
            self.faceInfo = self.parse_face_info(numFaces)
            
            # unk struct 6
            #print(self.inFile.tell(), 'struct 6')
            self.parse_unk6(unk6)
            
            # unk struct 2
            #print(self.inFile.tell(), 'struct 2')
            unkbuff = self.inFile.readBytes(unk2*16)
            
            # unk struct 3
            #print(self.inFile.tell(), 'struct 3')
            self.parse_unk3(unk3)
            
            # face struct
            #print(self.inFile.tell(), 'faces')
            self.parse_faces(mesh)
            
            # unk struct ...
            #self.parse_unk
                        
            # unk struct 10
            #print(self.inFile.tell(), 'struct 10')
            self.inFile.readBytes(unk10*14)
            
            # unk struct 4: portals?
            #print(self.inFile.tell(), "struct 4")
            self.parse_unk4(unk4)            
            
            # positions + something
            #print(self.inFile.tell(), "positions")
            vertBuff = self.parse_vertices(numVerts)

            mesh.name = meshName
            mesh.numVerts = numVerts
            mesh.vertBuff = vertBuff
            self.write_mesh(mesh)
            self.build_mesh(mesh)
            
            self.inFile.seek(nextMeshOfs)            
        print(self.inFile.tell())
        
    def skip_header_unk(self):
        
        skip = {0x15: 3, 0x85: 11, 0x155: 43, 0x129: 38, 0x49: 10,
                0x3ED: 126, 0x111: 35, 0x479: 144, 0x55: 11,
                0x1555 : 683, 0x2C9 : 90, 0x3AD: 118}
          
        unk1 = self.inFile.readUInt()
        unk2 = self.inFile.readUInt()
        
        self.inFile.seek(skip[unk1], 1)
        
    def parse_file(self):
        '''Main parser method'''
        
        with (open("test.txt", 'w'))as f:
            pass        
        #header
        version = self.inFile.readUInt()
        offsets = self.inFile.read('2L')
        self.inFile.seek(32, 1)
        info = self.read_info()

        self.inFile.read('13f')
        self.skip_header_unk()
        

        #mesh section
        numMesh = self.inFile.readUInt()
        print(numMesh)
        self.parse_meshes(numMesh)
        #self.parse_mesh2()
        
    #numMesh = 1
    def parse_mesh2(self):
    
        mesh = Mesh()
        nextMeshOfs = self.inFile.readUInt()
        
        self.inFile.seek(32, 1)
        self.inFile.read('2L')
        meshName = self.read_name()
        numVerts, unk2, unk3, unk4, numFaces, unk6, numIdx, unk8, unk9, \
            unk10, unk11, unk12 = self.inFile.read("12L")
        self.inFile.read("9f")
        
        #get texture paths
        strLen, numTex = self.inFile.read('2L')
        self.inFile.seek(strLen, 1)
        
        # indices per face
        print(self.inFile.tell(), "face info")
        self.faceInfo = self.parse_face_info(numFaces)
        
        # unk struct 6
        print(self.inFile.tell(), 'struct 6')
        self.parse_unk6(unk6)
        
        # unk struct 2
        print(self.inFile.tell(), 'struct 2')
        unkbuff = self.inFile.readBytes(unk2*16)
        
        # unk struct 3
        print(self.inFile.tell(), 'struct 3')
        self.parse_unk3(unk3)
        
        # face struct
        print(self.inFile.tell(), 'faces')
        self.parse_faces(mesh)
        
        # unk struct ...
        #self.parse_unk
                    
        # unk struct 10
        print(self.inFile.tell(), 'struct 10')
        self.inFile.readBytes(unk10*14)
        
        # unk struct 4: portals?
        print(self.inFile.tell(), "struct 4")
        self.parse_unk4(unk4)
        
        # positions + something
        print(self.inFile.tell(), "positions")
        vertBuff = self.parse_vertices(numVerts)
            
        
        mesh.name = meshName
        mesh.numVerts = numVerts
        mesh.vertBuff = vertBuff
        
        #self.build_mesh(mesh)
        self.inFile.seek(nextMeshOfs)            
        print(self.inFile.tell())        
        
    def write_mesh(self, mesh):
        
        write_verts = True
        write_tris = False
        write_quads = False
        
        with (open("test.txt", 'a'))as f:
            
            
            f.write("Offset: %d\n" %mesh.offset)
            if write_verts:
                data = NoeBitStream(mesh.vertBuff)
                while not data.checkEOF():
                    f.write("%f "  %data.readFloat())
                    f.write("%f "  %data.readFloat())
                    f.write("%f\n"  %data.readFloat())
                
            if write_tris:
                f.write("==Tris==\n")
                data = NoeBitStream(mesh.triBuff)
                while not data.checkEOF():
                    f.write("%d "  %data.readShort())
                    f.write("%d "  %data.readShort())
                    f.write("%d\n"  %data.readShort())        
            if write_quads:
                f.write("==Quads==\n")
                data = NoeBitStream(mesh.quadBuff)
                while not data.checkEOF():
                    f.write("%d "  %data.readShort())
                    f.write("%d "  %data.readShort())
                    f.write("%d "  %data.readShort())
                    f.write("%d\n"  %data.readShort())                
            f.write("==End==\n\n")