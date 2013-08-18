from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
   handle = noesis.register("Crucis Fatal Fake", ".lmd")
   noesis.setHandlerTypeCheck(handle, noepyCheckType)
   noesis.setHandlerLoadModel(handle, noepyLoadModel) #see also noepyLoadModelRPG
   return 1

def noepyCheckType(data):
   return 1

def noepyLoadModel(data, mdlList):
   ctx = rapi.rpgCreateContext()
   
   #parse file
   parser = CrucisFatalFake_LMD(data)
   parser.parse_file()
   
   #build model
   mdl = rapi.rpgConstructModel()
   mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
   mdlList.append(mdl)
   
   rapi.rpgClearBufferBinds()  
   return 1

class CrucisFatalFake_LMD(object):
    
   def __init__(self, data):
       
      self.inFile = NoeBitStream(data)
      self.animList = []
      self.texList = []
      self.matList = []
      self.boneList = []

   def read_name(self):
     
      string = self.inFile.readBytes(self.inFile.readUShort())
      return noeStrFromBytes(string)

   def parse_submesh(self):
        
      unk = self.inFile.readUInt()
      self.inFile.read('%dL' %unk)
      unkbyte = self.inFile.readUByte()
      self.inFile.readUInt()
      if unkbyte:
         count = self.inFile.readUInt()
         for i in range(count):
            self.inFile.read('4f')
            self.inFile.readUInt()
            self.inFile.read('2B')
            unk1, unk2 = self.inFile.read('2L')
            for j in range(unk2):
               self.inFile.readUInt()
          
         count2 = self.inFile.readUInt()
         for i in range(count2):
            self.inFile.read('2L')
            self.inFile.read('5f')
            self.inFile.readUInt()
         self.inFile.seek(56, 1)
         
   def parse_vertices(self, numVerts):
      
      self.vertList = self.inFile.readBytes(numVerts * 48)
      rapi.rpgBindPositionBufferOfs(self.vertList, noesis.RPGEODATA_FLOAT, 48, 0)
      rapi.rpgBindNormalBufferOfs(self.vertList, noesis.RPGEODATA_FLOAT, 48, 28)
      rapi.rpgBindUV1BufferOfs(self.vertList, noesis.RPGEODATA_FLOAT, 48, 40)
      
      trans = NoeMat43((NoeVec3((-1.0, 0.0, 0.0)), NoeVec3((0.0, 1.0, 0.0)), NoeVec3((0.0, 0.0, 1.0)), NoeVec3((0.0, 0.0, 0.0))))
      rapi.rpgSetTransform(trans)
      
   def parse_faces(self, numIdx):
      
      idxList = self.inFile.readBytes(numIdx*2)
      return idxList     
         
   def parse_mesh(self, numMesh):
      
      for i in range(numMesh):
         self.inFile.readUInt()
         meshName = self.read_name()
         rapi.rpgSetName(meshName)
         self.inFile.read('16f')
         self.inFile.readUInt()
         numVerts = self.inFile.readUInt()
         self.inFile.readUByte()
         self.parse_vertices(numVerts)
         unk2, unk3, numIdx = self.inFile.read('3L')
         idxList = self.parse_faces(numIdx)
         matIndex = self.inFile.readUInt()
         matName = self.read_name()
         self.parse_submesh()
         
         #now create triangles
         rapi.rpgSetMaterial(matName)
         rapi.rpgCommitTriangles(idxList, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
         
   def parse_materials(self, numMat):
        
      offset = len(self.matList)
      for i in range(numMat):
         index = offset + i
         self.inFile.read('17f')
         matName = self.read_name()
         self.inFile.read('5L')
         numTex = self.inFile.readUInt()
         for j in range(numTex):
            texName = self.read_name()
         
         material = NoeMaterial(matName, "")
         material.setTexture(texName)
         self.matList.append(material)
                  
   def parse_textures(self, numTex):
      '''Parse textures'''
      
      for i in range(numTex):
         texName = self.read_name()
         size = self.inFile.readUInt()
         texture = self.inFile.readBytes(size)
         tex = rapi.loadTexByHandler(texture, ".dds")
         if tex is not None:
            tex.name = texName
            self.texList.append(tex)
            
   def parse_bones(self, numBones):
      
      for i in range(numBones):       
         count = self.inFile.readUInt()
         self.inFile.read('%df' %count*3)
         self.inFile.read('2L')
         boneName = self.read_name()
         self.inFile.read('16f')
         self.inFile.readUInt()
         
   def parse_file(self):

      self.inFile.readUInt()
      self.read_name()
      unk1, numMesh = self.inFile.read('2L')
      self.parse_mesh(numMesh)
      
      self.inFile.read('2L')
      self.read_name()
      numMat = self.inFile.readUInt()
      self.parse_materials(numMat)
      
      self.inFile.readUInt()
      self.read_name()
      numMat2 = self.inFile.readUInt()
      self.parse_materials(numMat2)
      
      numTex = self.inFile.readUInt()
      self.parse_textures(numTex)
      self.inFile.readByte()
      self.inFile.readUInt()
      self.read_name()
      
      numBones = self.inFile.readUInt()
      self.parse_bones(numBones)
