'''
Noesis import plugin.
Author: Tsukihime (Finale)
Updated: Dec 15, 2012

Supported games
-War of Dragons
-Emblem Saga
-DK Online
-Yulgang 2 (Scions of Fate 2)
-Argos Online
-Valiant Online
-Crusader Kings 2
-ChunRyong
'''

from inc_noesis import *
import noesis
import rapi
import os
'''
MODE CONFIGURATION
0 = single model
1 = all models
'''
MODE = 0

def registerNoesisTypes():
    '''Register the plugin.'''
    
    handle = noesis.register("DK Online", ".xac")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(4))
        if idstring != "XAC ":
            return 0
        return 1
    except:
        return 0

def load_all_models(mdlList):
    '''Load all models in the selected model's directory'''

    #carry over from previous models
    matList = []
    texList = []
    boneList = []

    dirPath = rapi.getDirForFilePath(rapi.getInputName())
    fileList = [file for file in os.listdir(dirPath) if file.lower().endswith(".xac")]
    for filename in fileList:
        f = open(dirPath + filename, 'rb')
        data2 = f.read()
        parser = SanaeParser(data2)
        parser.parse_file(filename)
        matList.extend(parser.matList)
        texList.extend(parser.texList)
        boneList.extend(parser.boneList)
        mdl = rapi.rpgConstructModel()
        
    mdl.setModelMaterials(NoeModelMaterials(texList, matList))
    mdl.setBones(boneList)
    mdlList.append(mdl)    
    
def load_single_model(data, mdlList):
    '''Loads a single model. For testing purposes'''
    
    filename = rapi.getLocalFileName(rapi.getInputName())
    basename, ext = os.path.splitext(filename)
    
    parser = SanaeParser(data)
    parser.parse_file(basename)
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdlList.append(mdl)
    
def noepyLoadModel(data, mdlList):
    '''Load the model'''
    
    ctx = rapi.rpgCreateContext()
    if MODE == 1:
        load_all_models(mdlList)
    else:
        load_single_model(data, mdlList)
    return 1

class XACMesh(object):
    '''An XAC mesh object. Makes it easier to retrieve data'''
    
    def __init__(self):
        
        self.vertBuff = bytes()
        self.normBuff = bytes()
        self.uvBuff = bytes()
        self.weightBuff = bytes()
        self.numFaceGroups = 0
        self.idxBuffs = []
        
class XACMaterial(object):
    '''XAC material object'''
    
    def __init__(self):
        
        self.name = ""
        self.power = 0.0
        self.ambient = ()
        self.specular = ()
        self.emissive = ()
        self.diffTex = ""
        self.bumpTex = ""
        self.maskTex = ""

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.meshes = []
        self.boneID = 0
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.abspath = rapi.getInputName()
        self.dirpath = rapi.getDirForFilePath(rapi.getInputName())

    def build_meshes(self):
        '''Build the meshes. For the buffers in each mesh, we have to 
        partition it based on the number of vertices a particular face group
        has'''
        
        for mesh in self.meshes:

            vertStart = 0
            vertEnd = 0
            uvStart = 0
            uvEnd = 0
            
            for i in range(mesh.numFaceGroups):
                idxBuff, numIdx, numVerts, matNum, numBones = mesh.idxBuffs[i]
                
                #partition verts and normals
                vertEnd += numVerts * 12
                vertBuff = mesh.vertBuff[vertStart:vertEnd]
                normBuff = mesh.normBuff[vertStart:vertEnd]
                rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
                rapi.rpgBindNormalBuffer(normBuff, noesis.RPGEODATA_FLOAT, 12)
                vertStart += numVerts * 12
                
                #partition uv, if any
                if mesh.uvBuff:
                    uvEnd += numVerts * 8
                    uvBuff = mesh.uvBuff[uvStart:uvEnd]
                    rapi.rpgBindUV1Buffer(uvBuff, noesis.RPGEODATA_FLOAT, 8)
                    uvStart += numVerts * 8
                    
                rapi.rpgSetTransform(NoeMat43(((1, 0, 0),
                                              (0, 1, 0),
                                              (0, 0, 1),
                                              (0, 0, 0))))
                
                #commit triangles
                mat = self.matList[matNum]
                rapi.rpgSetMaterial(mat.name)
                rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_UINT, numIdx, noesis.RPGEO_TRIANGLE, 1)
    
    def build_skeleton(self):
        
        if self.boneList:
            self.boneList = rapi.multiplyBones(self.boneList)
                
    def parse_bones(self):
        floats = self.inFile.read('16f')
        x = floats[8]
        y = floats[9]
        z = floats[10]
        self.inFile.readUInt()
        self.inFile.readUInt()
        parent = self.inFile.readUInt()
        self.inFile.readUInt()
        boneName = self.read_name()
        qx,qy,qz,qw=floats[0:4]
        mat = NoeQuat((qx,qy,qz,qw))
        mat = mat.toMat43()
        mat = mat.inverse()
        mat.__setitem__(3, (x,y,z))
        self.boneList.append(NoeBone(self.boneID,boneName,mat,None,parent))
        self.boneID+=1
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        try:
            return noeStrFromBytes(string)
        except:
            return ""
        
    def parse_material_extra(self):
        
        self.inFile.seek(24, 1)
        self.read_name()
        
    def parse_header(self):
        
        self.inFile.read('2l')
        self.inFile.read('4B')
        self.inFile.readUInt()
        maxVersion = self.read_name()
        modelName = self.read_name()
        modelDate = self.read_name()
        self.inFile.readUInt()
        
    def parse_unk1(self, count):
        
        self.inFile.read('%dL' %count)
        
    def parse_vertices(self, numVerts, mesh):
        
        vertBuff = self.inFile.readBytes(12*numVerts)
        mesh.vertBuff = vertBuff
        
    def parse_normals(self, numVerts, mesh):
        
        normBuff = self.inFile.readBytes(12*numVerts)
        mesh.normBuff = normBuff
        
    def parse_weights(self, numVerts, mesh):
        
        weightBuff = self.inFile.readBytes(16*numVerts)
        mesh.weightBuff = weightBuff
        
    def parse_uvs(self, numVerts, mesh):
        
        uvBuff = self.inFile.readBytes(8*numVerts)
        mesh.uvBuff = uvBuff
        
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*4)
        
    def parse_mesh(self):
        
        mesh = XACMesh()
        unk1, unk2, numVerts, unk3, numFaceGroups, structs, unk4, unk5, unk6, \
            unk7 = self.inFile.read('10L')
        self.parse_unk1(numVerts)            
        
        for i in range(structs - 1):
            struct, structSize, unk = self.inFile.read('3L')
            if struct == 0:
                self.parse_vertices(numVerts, mesh)
            elif struct == 1:
                self.parse_normals(numVerts, mesh)
            elif struct == 2:
                self.parse_weights(numVerts, mesh)
            elif struct == 3:
                self.parse_uvs(numVerts, mesh)
            
        #each mesh contains a list of index buffers for each face group 
        mesh.numFaceGroups = numFaceGroups
        for i in range(numFaceGroups):
            numIdx, numVerts, matNum, numBones = self.inFile.read('4L')
            idxBuff = self.parse_faces(numIdx)
            self.inFile.read("%dl" %numBones)
            mesh.idxBuffs.append([idxBuff, numIdx, numVerts, matNum, numBones])
        self.meshes.append(mesh)
        
    def parse_material3(self, count):
        '''Chunk 3: Materials'''
            
        self.inFile.read('16f')
        power = self.inFile.readFloat()
        self.inFile.read('3f')
        self.inFile.read('3B')
        numTex = self.inFile.readByte()
        matName = self.read_name()
    
        for i in range(numTex):
            self.inFile.read('6f')
            self.inFile.read('2H')
            self.read_name()
        
        material = NoeMaterial(matName, "")
        self.matList.append(material)        
            
    def parse_material5(self):
        '''Chunk 5: materials'''
        
        fxCount, count1, count2, count3, count4, texMaps = self.inFile.read('6L')
        print(fxCount, count1, count2, texMaps)
        mat = XACMaterial()
        mat.name = self.read_name()
        
        for i in range(fxCount):
            fx = self.read_name()
            self.read_name()
            self.inFile.readUInt()
            
        for i in range(count1):
            prop = self.read_name()
            self.inFile.readFloat()
        
        for i in range(count2):
            prop = self.read_name()
            self.inFile.read('4f')
        
        for i in range(count3):
            prop = self.read_name()
            self.inFile.readByte() # bool?
        
        # is glow?
        name = self.read_name()
        
        for i in range(texMaps):
            propName = self.read_name()
            name = self.read_name()
            
            if propName == "DIFFUSECOLOR" or propName == "diffuseTexture":
                mat.diffName = name
            elif propName == "BUMP" or propName == "normalTexture":
                mat.bumpName = name
            elif propName == "specTexture":
                mat.specName = name
            elif propName == "MASK" or propName == "maskTexture":
                mat.maskName = name
            elif propName == "glowTexture":
                mat.glowName = name
        
        tempPath = self.dirpath + "texture\\" + mat.diffName
        material = NoeMaterial(mat.name, tempPath)
        self.matList.append(material)
        
    def parse_mat_texture(self):
        
        self.inFile.read('6f')
        matNum, unk = self.inFile.read('2H')
        texName = self.read_name()
        if "_d" in texName or "_D" in texName:
            self.matList[matNum].setTexture(texName)      
        elif "_n" in texName or "_N" in texName:
            self.matList[matNum].setNormalTexture(texName)
        #else:
            ##some games don't use normal maps
            #self.matList[matNum].setTexture(texName)      
        
    def parse_mat_block(self):
        '''Some formats store their materials in a different chunk'''
        
        numMat, count2, count3 = self.inFile.read('3L')
        for i in range(numMat):
            chunk, size, count = self.inFile.read('3L')
            if chunk == 3:
                self.parse_material3(count)
            elif chunk == 5:
                self.parse_material5()
                #print("here, chunk %d" %chunk, self.inFile.tell())
                #self.inFile.seek(size, 1)
                
        
    def parse_file(self, filename):
        
        idstring = self.inFile.readBytes(4)
        unks = self.inFile.readBytes(4)
        while self.inFile.tell() != self.inFile.dataSize:
            chunk, size, count = self.inFile.read('3L')
            if chunk == 0:
                self.parse_bones()                
            elif chunk == 1:
                self.parse_mesh()
            elif chunk == 2:
                self.inFile.seek(size, 1)
            elif chunk == 3:
                self.parse_material3(count)
            elif chunk == 4:
                self.parse_mat_texture()
            elif chunk == 5:
                self.parse_material5() #yulgang 2 mat chunk
            elif chunk == 6:
                # unk
                self.inFile.seek(size, 1)
            elif chunk == 7:
                self.parse_header()            
            elif chunk == 8:
                # unk
                self.inFile.seek(size, 1)
            elif chunk == 0xB:
                self.inFile.seek(size, 1)
            elif chunk == 0xD:
                print('mat block', self.inFile.tell())
                self.parse_mat_block()
            else:
                print("chunk %d" %chunk, self.inFile.tell())
                self.inFile.seek(size, 1)
        self.build_meshes()
        self.build_skeleton()