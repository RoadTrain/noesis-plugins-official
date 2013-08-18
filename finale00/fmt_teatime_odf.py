from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject

def registerNoesisTypes():
   handle = noesis.register("Teatime", ".odf")
   noesis.setHandlerTypeCheck(handle, noepyCheckType)
   noesis.setHandlerLoadModel(handle, noepyLoadModel) #see also noepyLoadModelRPG
   noesis.logPopup()
   
   return 1

#check if it's this type based on the data
def noepyCheckType(data):
   if len(data) < 3:
      return 0
   bs = NoeBitStream(data)
   if bs.readBytes(3).decode("ASCII") != "ODF":
      return 0
   return 1

#load the model
def noepyLoadModel(data, mdlList):
   ctx = rapi.rpgCreateContext()
   parser = Teatime_ODF(data)
   parser.parse_file()
   mdl = rapi.rpgConstructModel()
   mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
   mdlList.append(mdl)
   
   mdl2 = rapi.rpgConstructModel()
   mdlList.append(mdl2)
   return 1

class Teatime_ODF(SanaeObject):
    
   def __init__(self, data):
       
      super(Teatime_ODF, self).__init__(data)
      self.meshes = []
      self.matIDs = {}
      self.texIDs = {}
      self.tempFrame = {} #frame ID mappnig
      self.submeshList = [] #temp storage
      self.meshList = []
      self.tempMesh = {} #mesh ID mapping
      self.odfFormat = 0     
      
   def read_name(self, n):
        
      return self.read_string(n).split("\x00")[0]
   
   def load_texture(self, name, texID, path):
      
      ext = name[-4:]
      f = open(self.dirpath + name, 'rb')
      tex = rapi.loadTexByHandler(f.read(), ext)
      if tex is not None:
         tex.name = name
         self.texList.append(tex)
         self.texIDs[texID] = tex
      f.close()
         
   def parse_textures(self, sectLen):
        
      #check if it's HCT (after school custom time)
      if sectLen % 204 != 0:
         self.odfFormat = 2
         
         numTex = sectLen // 132
         for i in range(numTex):
            name = self.read_name(64)
            texID = self.inFile.readUInt()
            path = self.read_name(64)
            self.load_texture(name, texID, path)
              
      #most older ODF format
      else:
         numTex = sectLen // 204
         for i in range(numTex):
            name = self.read_name(64)
            texID = self.inFile.readUInt()
            path = self.read_name(136)
            self.load_texture(name, texID, path)
            
   def parse_materials(self, sectLen):
        
      numMat = sectLen // 140
      for i in range(numMat):
         name = self.read_name(64)
         matID = self.inFile.readUInt()
         ambient = self.inFile.read('4f')
         diffuse = self.inFile.read('4f')
         specular = self.inFile.read('4f')
         emissive = self.inFile.read('4f')
         self.inFile.readFloat()
         power = self.inFile.readFloat()
         
         material = NoeMaterial(name, "")
         self.matIDs[matID] = material
         self.matList.append(material)
         
   def parse_faces(self, meshName, numIdx, matName):
      
      self.faceList = self.inFile.readBytes(numIdx*2)
      rapi.rpgSetMaterial(matName)
      rapi.rpgCommitTriangles(self.faceList, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
      #for i in range(int(numI)):
         #v1, v2, v3 = self.inFile.read_short(3)
        
   def parse_vertices(self, meshName, numVerts):
      
      verts = self.inFile.readBytes(numVerts * 52)
      rapi.rpgBindPositionBufferOfs(verts, noesis.RPGEODATA_FLOAT, 52, 0)
      rapi.rpgBindNormalBufferOfs(verts, noesis.RPGEODATA_FLOAT, 52, 28)
      rapi.rpgBindUV1BufferOfs(verts, noesis.RPGEODATA_FLOAT, 52, 44)
      
      #for i in range(int(numVerts)):
         #vx, vy, vz, w1, w2, w3, w4, nx, ny, nz = self.inFile.read_float(10)
         #b1, b2, b3, b4 = self.inFile.read_byte(4)
         #tu, tv = self.inFile.read_float(2)
         
   def parse_LD_submesh(self, meshNum):
        
      meshCount = len(self.meshList)
      meshName = self.read_name(64)
      rapi.rpgSetName(meshName)
      self.submeshList[meshNum].append(meshName)
      
      meshID, matNum, null, matID, texID = self.inFile.read('5L')
      texInfo = self.inFile.read('13L')
      numVerts = self.inFile.readUInt()
      numIdx = self.inFile.readUInt()
      matFlag = self.inFile.read('4L')
      self.inFile.seek(432, 1)   # nulls
      if matID:
         material = self.matIDs[matID] 
         matName = material.name
         if texID != 0:
            #self.add_texture_name(matNum, self.tempTex[texID])
            texture = self.texIDs[texID]
            material.setTexture(texture.name)
      self.parse_vertices(meshName, numVerts)
      self.parse_faces(meshName, numIdx, matName)
      self.inFile.read('6L')               #nulls
      
      self.meshList.append(meshName)
      self.tempMesh[meshID] = meshCount
         
   def parse_meshes(self, sectLen):
        
      sectEnd = self.inFile.tell() + sectLen
      meshNum = 0
      while self.inFile.tell() != sectEnd:
         name = self.read_name(64)
         if self.odfFormat == 4:
            self.submeshList.append([])
            self.parse_yuki_submesh(name, meshNum)
         else:
            meshID, numSubMesh = self.inFile.read('2L')
            self.tempMesh[meshID] = meshNum
            
            self.submeshList.append([])
            for i in range(numSubMesh):
               if self.odfFormat == 2:
                  self.parse_HCT_submesh(meshNum)
               else:
                  self.parse_LD_submesh(meshNum)
         meshNum += 1
      
   def parse_file(self):
      
      fsize = self.inFile.dataSize

      self.inFile.readUInt()
      self.inFile.read('8B')
      
      while self.inFile.tell() != fsize:
         
         tag = self.read_string(4)
         sectLen = self.inFile.readUInt()
         if tag == "MAT ":
            self.parse_materials(sectLen)
         elif tag == "TEX ":
            self.parse_textures(sectLen)
         elif tag == "MESH":
            self.parse_meshes(sectLen)
            #self.inFile.seek(sectLen, 1)
         elif tag == "FRAM":
            #self.parse_frames(sectLen)
            self.inFile.seek(sectLen, 1)
         elif tag == "BANM":
            self.inFile.seek(sectLen + 264, 1)
         elif tag == "ENVL":
            self.inFile.seek(sectLen, 1)
            #self.parse_bones(sectLen)
         else:
            self.inFile.seek(sectLen, 1)