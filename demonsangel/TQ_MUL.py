from inc_noesis import *
import noesis
import rapi
import binascii,struct,os,time,configparser

def registerNoesisTypes():
	handle = noesis.register("TitanQuest Loader", ".mshini")
	noesis.setHandlerTypeCheck(handle, noepyCheckType)
	noesis.setHandlerLoadModel(handle, noepyLoader)
	return 1
	
def noepyCheckType(data):
	return 1
	
def noepyLoader(data, mdlList):
	ctx = rapi.rpgCreateContext()
	config = configparser.ConfigParser()
	config.read(rapi.getInputName())
	dirPath = rapi.getDirForFilePath(rapi.getInputName())
	vertBuff=[]
	faceBuff=[]
	boneBuff=[]
	texBuff=[]
	matBuff=[]
	AttachPoint=[]
	shaderBuff=[]
	MIF=configparser.ConfigParser()
	for section in config.sections():
		model = config[section]['path']
		data = open(dirPath+model,'rb').read()
		parser= Parser(data)
		parser.parser(section,vertBuff,faceBuff,boneBuff,texBuff,matBuff,shaderBuff)
		if config.has_option(section,"ap"):
			AttachPoint.append(config[section]["AP"])
		else: AttachPoint.append(None)
	TQMesh=ConstructModel()
	mdl = TQMesh.CreateTQ(vertBuff,faceBuff,boneBuff,texBuff,matBuff,shaderBuff,AttachPoint,MIF)
	mdlList.append(mdl)
	rapi.rpgClearBufferBinds()
	return 1

class ConstructModel:
	def __init__(self):
		pass
	def CreateTQ(self,vertBuff=[],faceBuff=[],boneBuff=[],texBuff=[],matBuff=[],shaderBuff=[],AttachPoint=[],MIF=[]):
		###Correct Bone indexes for ShaderCall###
		boneReference = boneBuff[0][1]
		
		for mesh in range(len(vertBuff)):
			if mesh >0:
				boneNames = boneBuff[mesh][1]
				for i in range(len(shaderBuff[mesh][0])):
					boneIndex = shaderBuff[mesh][0][i]
					for bone in boneIndex:
						boneName = boneNames[bone]
						try:
							boneIndex[boneIndex.index(bone)]= boneReference.index(boneName)
						except: pass
					shaderBuff[mesh][0][i] = boneIndex
		
		vertOrderSize   ={0:12,1:12,2:12,3:12,4:8,5:16,6:4,14:4}
		matList=[]
		for mesh in range(len(vertBuff)):
			Offset = 0
			for i in range(len(vertBuff[mesh][1])):
				if vertBuff[mesh][1][i] == 0:
					vertOffset = Offset
					Offset+=vertOrderSize[0]
				elif vertBuff[mesh][1][i]==4:
					uvOffset = Offset
					Offset+=vertOrderSize[4]
				elif vertBuff[mesh][1][i]==1:
					normalOffset = Offset
					Offset+=vertOrderSize[1]
				elif vertBuff[mesh][1][i]==5:
					boneWeightOffset = Offset
					Offset+=vertOrderSize[5]
				elif vertBuff[mesh][1][i]==6:
					boneIndexOffset = Offset
					Offset+=vertOrderSize[6]
				else:
					Offset+=vertOrderSize[vertBuff[mesh][1][i]]
			rapi.rpgBindPositionBufferOfs(vertBuff[mesh][0], noesis.RPGEODATA_FLOAT, vertBuff[mesh][2], vertOffset)
			rapi.rpgBindUV1BufferOfs(vertBuff[mesh][0], noesis.RPGEODATA_FLOAT, vertBuff[mesh][2], uvOffset)
			rapi.rpgBindNormalBufferOfs(vertBuff[mesh][0], noesis.RPGEODATA_FLOAT, vertBuff[mesh][2], normalOffset)
			if AttachPoint[mesh] != None:
				(a1,a2,a3),(a4,a5,a6),(a7,a8,a9),(x,y,z) =boneBuff[0][0][38]._matrix
				rapi.rpgSetPosScaleBias((a1,a5,a9),(x,y,z))
			for drawcall in range(len(shaderBuff[mesh][1])):
				matID,faceStart,faceStop=shaderBuff[mesh][1][drawcall]
				idxBuff = faceBuff[mesh][faceStart*6:]
				numIdx = faceStop
				for i in range(len(texBuff[mesh][2][matID])):
					if texBuff[mesh][2][matID][i] ==7:
						texName = texBuff[mesh][0][matID][i].replace('/','\\').split('\\')
						texName = texName[-1]
						material= NoeMaterial(texName,texName)
						if texBuff[mesh][1][matID][i] =='baseTexture':
							rapi.rpgSetMaterial(texName)
						matList.append(material)
				if len(boneReference)>0:
					if len(shaderBuff[mesh][0][drawcall])>0:
						rapi.rpgSetBoneMap(shaderBuff[mesh][0][drawcall])
						rapi.rpgBindBoneIndexBufferOfs(vertBuff[mesh][0], noesis.RPGEODATA_UBYTE, vertBuff[mesh][2], boneIndexOffset, 4)
						rapi.rpgBindBoneWeightBufferOfs(vertBuff[mesh][0], noesis.RPGEODATA_FLOAT, vertBuff[mesh][2], boneWeightOffset, 4)
				rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
				rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx*3, noesis.RPGEO_TRIANGLE, 1)
		mdl=rapi.rpgConstructModel()
		mdl.setModelMaterials(NoeModelMaterials([], matList))
		mdl.setBones(boneBuff[0][0])
		for bone in boneBuff[0][0]:
			if bone.name =="Bone_L_Weapon":print(bone._matrix)
		return mdl
class Parser:
	def __init__(self,data):
		self.data=NoeBitStream(data)
		
	def parser(self,Root,vertBuff=[],faceBuff=[],boneBuff=[],texBuff=[],matBuff=[],shaderBuff=[]):
		self.sections={}
		self.section=[]
		self.data.seek(4)
		while self.data.tell()<self.data.getSize():
			section=self.data.readUInt()
			size = self.data.readUInt()
			self.data.readBytes(size)
			self.sections[section]=size
			self.section.append(section)
		self.data.seek(3)
		
		global mesh_type
		mesh_type = self.data.read('b')[0]
		for i in range(len(self.sections)):
			
			section = self.data.readUInt()
			print(section)
			if section == 0: #MIF : material 
				self.data.readUInt()
				size = self.data.readUInt()
				# StrSize=self.data.readUInt()
				self.mif= noeStrFromBytes(self.data.readBytes(size))
			elif section == 3:
				mif = self.mif.replace("/","\\").split("\\")
				try:
					q=open(mif[-1],'wb')
					size = self.data.readUInt()
					mifdata = self.data.readBytes(size)
					q.write(mifdata)
					q.close()
				except:print(mif)
				if Root =="MAIN":
					global MIF
					mif = mifdata.split(b"AttachPoint\r\n")
					mif[-1] = mif[-1].split(b"}\r\n")
					mif[-1]=mif[-1][0] +b"}\r\n"
					print(mif[-1])
							
					
			elif section == 4: #vertex
				size            = self.data.readUInt()
				numInt          = self.data.readUInt()
				vertLength      = self.data.readUInt()
				numVerts        = self.data.readUInt()
				vertOrder       =[]
				for i in range(numInt): 
					vertOrder.append(self.data.readUInt())
				vertBuffer = self.data.readBytes(vertLength*numVerts)
				vertBuff.append((vertBuffer,vertOrder,vertLength,numVerts))
			elif section == 5: #triangles/faces/drawcall
				size = self.data.readUInt()
				numIdx = self.data.readUInt()
				numDrawCall = self.data.readUInt()
				idxBuff = self.data.readBytes(numIdx*2*3)
				
				###
				drawCallIndex = []
				drawCall = []
				###
				
				for i in range(numDrawCall):
					drawCallIndex.append([])
					shader,startFace,faceCount,word=self.data.read('4i')
					if mesh_type ==10:
						for t in range(word):
							drawCallIndex[i].append(self.data.readUInt())
					elif mesh_type==11:
						self.data.read('6f')
						ints=self.data.readUInt()
						for t in range(ints):
							drawCallIndex[i].append(self.data.readUInt())
				
					drawCall.append((shader,startFace,faceCount))
				faceBuff.append(idxBuff)
				shaderBuff.append((drawCallIndex,drawCall))
			elif section == 6: #bones
				print("bones going")
				size = self.data.readUInt()
				numBones = self.data.readUInt()
				if Root =="MAIN":
					bonenames=[]
					boneIndex=[]
					boneCIndex=[]
					numChild=[]
					boneMat=[]
					bonelinks={}
					bones=[]
					for i in range(numBones):
						boneName = noeStrFromBytes(self.data.readBytes(32))
						boneIndex.append(i)
						boneCIndex.append(self.data.readUInt())
						numChild.append(self.data.readUInt())

						boneBuffer=self.data.readBytes(48)
						
						(a1,a2,a3),(a4,a5,a6),(a7,a8,a9),(x,y,z) = NoeMat43.fromBytes(boneBuffer)
						
						tuple=(a1,a2,a3,0),(a4,a5,a6,0),(a7,a8,a9,0),(x,y,z,1)
						
						boneMat.append(NoeMat44(tuple))
						bonenames.append(boneName)
						
					for i in range(numBones):
						for t in range(numChild[i]):
							child = bonenames[boneCIndex[i]+t]
							bonelinks[child]=(i,bonenames[i])
						if not bonenames[i] in bonelinks:
							bonelinks[bonenames[i]]= (-1,None)
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
							bones.append(NoeBone(i,bonenames[i],boneMat[i],bonelinks[bonenames[i]][1]))
						except:
							raise
					boneBuff.append((bones,bonenames,bonelinks))
				else:
					bonenames=[]
					for i in range(numBones):
						boneName = noeStrFromBytes(self.data.readBytes(32))
						self.data.readBytes(56)
						bonenames.append(boneName)
					boneBuff.append((None,bonenames,None))
			elif section == 7: #textures
				size = self.data.readUInt()
				numTex = self.data.readUInt()
				
				texLength=[]
				texMat=[]
				texString=[]
				texType=[]
				self.matList=[]
				self.texList=[]
				for t in range(numTex):
					shaderLength = self.data.readUInt()
					shader = noeStrFromBytes(self.data.readBytes(shaderLength))
					numParam = self.data.readUInt()
					texLength.append([])
					texMat.append([])
					texType.append([])
					texString.append([])
					for i in range(numParam):
						texLength[t].append(self.data.readUInt())
						texMat[t].append(noeStrFromBytes(self.data.readBytes(texLength[t][i])))
						texType[t].append(self.data.readUInt())
				
						if texType[t][i] ==7:
							length=self.data.readUInt()
							texString[t].append(noeStrFromBytes(self.data.readBytes(length)))
						elif texType[t][i] ==8:
							texString[t].append(self.data.read('2f'))
						elif texType[t][i] ==9:
							texString[t].append(self.data.read('3f'))
						elif texType[t][i] ==10:
							texString[t].append(self.data.read('f'))
				texBuff.append((texString,texMat,texType))
			else:
				size=self.data.readUInt()
				self.data.readBytes(size)