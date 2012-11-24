from inc_noesis import *
import noesis
import rapi
import binascii,struct,os,time
from Sanae3D.Sanae import SanaeObject
def registerNoesisTypes():
	handle = noesis.register("TitanQuest", ".msh")
	noesis.setHandlerTypeCheck(handle, noepyCheckType)
	noesis.setHandlerLoadModel(handle, noepyLoadModel)
	return 1
	
def noepyCheckType(data):
	data = NoeBitStream(data)
	mesh=data.readBytes(4) 
	if mesh != b'\x4d\x53\x48\x0a' or mesh != b'\x4d\x53\x48\x0b':
		return 1
	return 1
	
def noepyLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	parser = SanaeParser(data)
	mdlL=parser.parse_file(data)
	for mdl in mdlL: mdlList.append(mdl)
	rapi.rpgClearBufferBinds()
	return 1



class SanaeParser(SanaeObject):
	def __init__(self,data):
		super(SanaeParser,self).__init__(data)
		
	def Animations(self):
		dirPath = rapi.getDirForFilePath(rapi.getInputName())
		animFile = open(dirPath+"/anm/automatoi_walk.anm","rb").read()
		animFile = NoeBitStream(animFile)
		animFile.seek(4)
		numBones=animFile.readUInt()
		numFrames=animFile.readUInt()
		FPS=animFile.readUInt()
		animation = []
		for i in range(numBones):
			length = animFile.readUInt()
			name = noeStrFromBytes(animFile.readBytes(length))
			animation.append((name,[]))
			for t in range(numFrames):
				pos =x,y,z = animFile.read("3f")
				rot = animFile.read("4f")
				scale = animFile.read("3f")
				rot2 = animFile.read("4f")
				#if i<5 and t == 0:print(scale)
				pos=NoeMat44(((1,0,0,0,),(0,1,0,0),(0,0,1,0),(x,y,z,1)))
				#rot = rot[3],rot[0],rot[1],rot[2]
				rotate=NoeQuat(rot)
				rotate=rotate.toMat43()
				#rotate= NoeMat44(((rotate.mat43[0],0),(rotate.mat43[1],0),(rotate.mat43[2],0),(rotate.mat43[3],1)))
				rotate = rotate.toMat44()
				rotate.__setitem__(3,(x,y,z,1))
				anim = rotate
				#anim = pos.__mul__(rotate)
				#anim.__setitem__(3,(x,y,z))
				animation[i][1].append(anim)
				#animation[i][1].append(pos)
				"""
				if i<5 and t==0 :
                                        print(anim.mat43[0],rotate.mat43[0])
                                        print("",anim.mat43[1],rotate.mat43[1])
                                        print("",anim.mat43[2],rotate.mat43[2])
                                        print("",anim.mat43[3])
                                """
		
		for i in range(numBones):
			for t in range(numFrames):
				if t==0 or t>0 :
					bone = self.bones[i]._matrix.toMat44()
					animation[i][1][t] = bone.__mul__(animation[i][1][t])
					animation[i][1][t] =animation[i][1][t].toMat43()
					#animation[i][1][t] = self.bones[i]._matrix.__mul__(animation[i][1][t])
					if i <2 and t==0:
						print(self.bones[i]._matrix)
						print(animation[i][1][t])
					#if i<5:print(self.bones[i]._matrix[3],animation[i][1][t][3])
					#tmp = list(animation[i][1][t][3])
					#tmp = self.bones[i]._matrix[3].__mul__(animation[i][1][t][3])
					#tmp[0] = self.bones[i-1]._matrix[3][0] + animation[i][1][t][3][0]
					#tmp[1] = self.bones[i-1]._matrix[3][1] + animation[i][1][t][3][1]
					#tmp[2] = self.bones[i-1]._matrix[3][2] + animation[i][1][t][3][2]
					#animation[i][1][t].__setitem__(3,tuple(tmp))
					#if i<5:print(animation[i][1][t][3])
					
				else:
					#animation[i][1][t] = animation[i][1][t].__mul__(animation[i][1][t-1])
					pass
				# animation[i][1][t] = child.__mul__(parent)
		
		# print(self.bones[0],self.bones[1])
		frameMat=[]
		for t in range(numFrames):
			for i in range(numBones):
				frameMat.append(animation[i][1][t])
		# print(animation[0][0],animation[1][1][1])
		# print(numBones,len(self.bones))
		return (NoeAnim("walk", self.bones, 1, frameMat, 1),)
		return (NoeAnim("walk", self.bones, numFrames, frameMat, 1),)
	def Section(self,ID):
		if ID == 0: #MIF : material 
			self.inFile.readUInt()
			size = self.inFile.readUInt()
			self.mif = self.read_string(size)
		elif ID == 4: #vertex
			size            = self.inFile.readUInt()
			numInt          = self.inFile.readUInt()
			self.vertLength = self.inFile.readUInt()
			self.numVerts   = self.inFile.readUInt()
			self.vertOrder  =[]
			vertOrderSize   ={0:12,1:12,2:12,3:12,4:8,5:16,6:4,14:4}
			for i in range(numInt): 
				self.vertOrder.append(self.inFile.readUInt())
			self.vertBuff = self.inFile.readBytes(self.vertLength*self.numVerts)
			Offset = 0
			for i in range(numInt):
				if self.vertOrder[i] == 0:
					self.vertOffset = Offset
					Offset+=vertOrderSize[0]
				elif self.vertOrder[i]==4:
					self.uvOffset = Offset
					Offset+=vertOrderSize[4]
				elif self.vertOrder[i]==1:
					self.normalOffset = Offset
					Offset+=vertOrderSize[1]
				elif self.vertOrder[i]==5:
					self.boneWeightOffset = Offset
					Offset+=vertOrderSize[5]
				elif self.vertOrder[i]==6:
					self.boneIndexOffset = Offset
					Offset+=vertOrderSize[6]
				else:
					Offset+=vertOrderSize[self.vertOrder[i]]
			
			rapi.rpgBindPositionBufferOfs(self.vertBuff, noesis.RPGEODATA_FLOAT, self.vertLength, self.vertOffset)
			rapi.rpgBindUV1BufferOfs(self.vertBuff, noesis.RPGEODATA_FLOAT, self.vertLength, self.uvOffset)
			rapi.rpgBindNormalBufferOfs(self.vertBuff, noesis.RPGEODATA_FLOAT, self.vertLength, self.normalOffset)
			
			
			
		elif ID == 5: #triangles/faces/drawcall
			size = self.inFile.readUInt()
			self.numIdx = self.inFile.readUInt()
			self.numDrawCall = self.inFile.readUInt()
			self.idxBuff = self.inFile.readBytes(self.numIdx*2*3)
			
			###
			self.Triangles=[]
			for i in range(self.numIdx*3):
				self.Triangles.append(struct.unpack_from('h',self.idxBuff,offset=2*i)[0])
			self.drawCallIndex = []
			self.drawCall = []
			###
			
			for i in range(self.numDrawCall):
				self.drawCallIndex.append([])
				shader,startFace,faceCount,word=self.inFile.read('4i')
				if mesh_type ==10:
					for t in range(word):
						self.drawCallIndex[i].append(self.inFile.readUInt())
				elif mesh_type==11:
					self.inFile.read('6f')
					ints=self.inFile.readUInt()
					for t in range(ints):
						self.drawCallIndex[i].append(self.inFile.readUInt())
				
				self.drawCall.append((shader,startFace,faceCount))
			
		elif ID == 6: #bones
			
			size = self.inFile.readUInt()
			numBones = self.inFile.readUInt()
			self.bones=[]
			bonenames=[]
			boneIndex=[]
			boneCIndex=[]
			numChild=[]
			boneMat=[]
			bonelinks={}
			
			for i in range(numBones):
				boneName = self.read_string(32)
				boneIndex.append(i)
				boneCIndex.append(self.inFile.readUInt())
				numChild.append(self.inFile.readUInt())
				
				if i ==0 and boneCIndex[i] != 1:
					rooting = 1-boneCIndex[i]
				boneBuff=self.inFile.readBytes(48)
				
				(a1,a2,a3),(a4,a5,a6),(a7,a8,a9),(x,y,z) = NoeMat43.fromBytes(boneBuff)
				
				tuple=(a1,a2,a3,0),(a4,a5,a6,0),(a7,a8,a9,0),(x,y,z,1)
				
				boneMat.append(NoeMat44(tuple))
				# boneMat.append(NoeMat43.fromBytes(boneBuff))
				bonenames.append(boneName)
				self.bonenames=bonenames
			for i in range(numBones):
				for t in range(numChild[i]):
					child = bonenames[boneCIndex[i]+t]
					bonelinks[child]=(i,bonenames[i])
				if not bonenames[i] in bonelinks:
					bonelinks[bonenames[i]]= (-1,None)
			self.bonelinks=bonelinks
			for i in range(numBones):
				Parent = bonelinks[bonenames[i]][1]
				if Parent != None:
					BoneMat = boneMat[i]
					BoneMatP= boneMat[bonelinks[bonenames[i]][0]]
					BoneMat = BoneMat.__mul__(BoneMatP)
					boneMat[i] = NoeMat44(list(BoneMat))
				
			

			for i in range(numBones):
				BoneMat = boneMat[i]
				for t in range(len(BoneMat)):
					BoneMat[t] = NoeVec3(BoneMat[t][:-1])
				boneMat[i] = NoeMat43(list(BoneMat))
			
			for i in range(numBones):
				try:
					self.bones.append(NoeBone(i,bonenames[i],boneMat[i],bonelinks[bonenames[i]][1]))
				except:
					print(i)
					raise
					return 0
		elif ID == 7: #textures
			size = self.inFile.readUInt()
			numTex = self.inFile.readUInt()
			
			texLength=[]
			texMat=[]
			texString=[]
			texType=[]
			self.matList=[]
			self.texList=[]
			for t in range(numTex):
				shaderLength = self.inFile.readUInt()
				shader = self.read_string(shaderLength)
				numParam = self.inFile.readUInt()
				texLength.append([])
				texMat.append([])
				texType.append([])
				texString.append([])
				for i in range(numParam):
					texLength[t].append(self.inFile.readUInt())
					texMat[t].append(self.read_string(texLength[t][i]))
					texType[t].append(self.inFile.readUInt())
			
					if texType[t][i] ==7:
						length=self.inFile.readUInt()
						texString[t].append(self.read_string(length))
					elif texType[t][i] ==8:
						texString[t].append(self.inFile.read('2f'))
					elif texType[t][i] ==9:
						texString[t].append(self.inFile.read('3f'))
					elif texType[t][i] ==10:
						texString[t].append(self.inFile.read('f'))
			idxBuff = self.idxBuff
			for i in range (self.numDrawCall):
				# RuntimeError: The buffer you provided is not larger enough to provide an index list in the given data type
				matID,faceStart,faceStop=self.drawCall[i]
				idxBuff = self.idxBuff[faceStart*6:]
				numIdx=faceStop
				for t in range(len(texType[matID])):
					if texType[matID][t] ==7:
						texName = texString[matID][t].replace('/','\\').split('\\')
						texName = texName[-1]
						material = NoeMaterial(texName,texName)
						if texMat[matID][t] == "baseTexture":
							rapi.rpgSetMaterial(texName)
						self.matList.append(material)
				if len(self.bones) >0:
					rapi.rpgSetBoneMap(self.drawCallIndex[i])
					rapi.rpgBindBoneIndexBufferOfs(self.vertBuff, noesis.RPGEODATA_UBYTE, self.vertLength, self.boneIndexOffset, 4)
					rapi.rpgBindBoneWeightBufferOfs(self.vertBuff, noesis.RPGEODATA_FLOAT, self.vertLength, self.boneWeightOffset, 4)
				rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
				rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx*3, noesis.RPGEO_TRIANGLE, 1)
		elif ID == 888888: #attributes
			pass
		elif ID ==10: #3D Extends
			self.inFile.readUInt()
			extend = self.inFile.read('6f')
		else:
			size=self.inFile.readUInt()
			self.inFile.readBytes(size)

		
		
	def parse_file(self,data):
		mesh = self.read_string(3)
		global mesh_type
		mesh_type = self.inFile.read('b')[0]
		start=time.time()
		data= NoeBitStream(data)
		data.readBytes(4)
		self.sections={}
		self.bones=[]
		while data.tell()<data.getSize():
			section=data.readUInt()
			size = data.readUInt()
			data.readBytes(size)
			self.sections[section]=size
		print(self.sections)
		for i in range(len(self.sections)):
			try:
				section = self.inFile.readUInt()
				print('[**]%s'%section)
				timed=time.time()
				self.Section(section)
				# print("Time:",time.time()-timed)
			except:
				print("@Error")
				raise
		

		mdl=rapi.rpgConstructModel()
		# if not mdl.meshes[0].weights: print("you fail")
		mdl.setModelMaterials(NoeModelMaterials(self.texList, self.matList))
		mdl.setBones(self.bones)
		mdl.setAnims(self.Animations())
		mdlList=[]
		mdlList.append(mdl)
		print("Total time:",time.time()-start)
		return mdlList
				
