'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

_ENDIAN = 0 # 1 for big endian

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Bakemonogatari PSP", ".amo")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 0:
        return 0
    bs = NoeBitStream(data)
    idstring = noeStrFromBytes(bs.readBytes(4))
    if idstring == "#AMO":
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
        
    def read_name(self, n):
        
        string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
        
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts * 32)
    
    def parse_faces(self, numIdx):
        
        pass
    
    def write_mesh(self, mesh):
            
        write_verts = True
        write_tris = False
        write_quads = False
        
        with (open("test.txt", 'a'))as f:
            if write_verts:
                data = NoeBitStream(mesh.vertBuff)
                while not data.checkEOF():
                    for i in range(7):
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
    
    def parse_vertex_groups(self, numGroups):
        
        for i in range(numGroups):
            mesh = Mesh()
            self.inFile.read('3L')
            mesh.numVerts = self.inFile.readShort()
            self.inFile.readShort()
            mesh.vertBuff = self.parse_vertices(mesh.numVerts)
            #self.write_mesh(mesh)
            
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
            rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, mesh.numVerts, noesis.RPGEO_POINTS, 1)
    
    def parse_mesh(self, startOfs):
        
        self.inFile.seek(startOfs)
        tag = self.inFile.readBytes(4)
        self.inFile.readUInt()
        self.inFile.readUInt()
        self.inFile.readUInt()
        numBones = self.inFile.readUInt()
        self.inFile.readUInt()
        self.inFile.readUInt()
        boneOfs = self.inFile.readUInt() - startOfs
        
        for i in range(numBones):
            self.inFile.seek(80, 1)
        
        self.inFile.read('5L')
        unkOfs = self.inFile.readUInt()
        self.seek_padding()
        
        # unk
        self.inFile.seek(32, 1)
        
        # ??
        self.inFile.seek(48, 1)
        self.inFile.read('2L')
        self.inFile.readShort()
        numGroups = self.inFile.readUInt()
        self.inFile.readShort()
        
        self.parse_vertex_groups(numGroups)
    
    def seek_padding(self):
        
        curr = self.inFile.tell()
        pad = (16 - (curr % 16)) % 16
        self.inFile.seek(pad, 1)
        
    def parse_file(self):
        '''Main parser method. 16-byte padding'''
        
        # header
        idstring = self.inFile.readBytes(4)
        self.inFile.readUInt()
        self.inFile.readUInt()
        self.inFile.readUInt()
        numBones = self.inFile.readUInt()
        self.inFile.readUInt()
        numMesh = self.inFile.readUInt()
        self.inFile.readUInt()
        self.inFile.readUInt()
        BonesOfs = self.inFile.readUInt()
        self.seek_padding()
        
        
        
        # mesh offsets
        meshOffsets = []
        for i in range(numMesh):
            meshOffsets.append(self.inFile.readUInt())
        self.seek_padding()
        
        # bones info?
        for i in range(numBones):
            self.inFile.seek(32, 1)
            
        for offset in meshOffsets:
            self.inFile.seek(offset)
            self.parse_mesh(offset)
        #self.parse_mesh(meshOffsets[0])