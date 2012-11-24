from inc_noesis import *
import noesis
import rapi
def registerNoesisTypes():
	handle = noesis.register("Diablo III", ".app")
	noesis.setHandlerTypeCheck(handle, noepyCheckType)
	noesis.setHandlerLoadModel(handle, noepyLoadModel)
	return 1
	
def noepyCheckType(data):
	return 1

def noepyLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	parser =appFile(data)
	mdl=parser.parse_file()
	mdlList.append(mdl)
	rapi.rpgClearBufferBinds()
	return 1

class appFile:
	def __init__(self,data):
		self.data=NoeBitStream(data)
		self.boneList=[]
		self.vertList=[]
		self.idxList =[]
		self.matList=[]
		self.texList=[]
		self.triList=[]
		self.animList=[]
		self.drawCallFace=[]
		self.matID=[]
	def Serialise(self):
		offset	  = self.data.readUInt()
		size		= self.data.readUInt()
		if size  ==  0:
			return 0
		x		   = self.data.tell()
		self.data.seek(offset+16)
		return x
	def parse_file(self):
		self.HEADER()
		i0			= self.data.readUInt()
		dwFlags	   = self.data.readUInt()
		self.numBones = self.data.readUInt()
		offset		= self.Serialise()
		print(self.data.tell())
		if offset != 0:
			self.BONES()
		self.data.seek(offset)
		pad0 = self.data.read('2I')
		self.data.seek(92 + 4 + 8+8,1)
		self.GeoSet()
		try:
			mdl = rapi.rpgConstructModel()
			mdl.setBones(self.boneList)
			return mdl
		except:return
	def HEADER(self):
		self.data.readBytes(28)
	def SubObj(self,count):
		for i in range(count):
			self.data.seek(4,1)
			numVert = self.data.readUInt()
			#print("numVert",numVert)
			offset = self.Serialise()
			#self.vertList.append([])
			vertList=b''
			for t in range(numVert):
				vertList+=self.data.readBytes(12)
				self.data.seek(32,1)
			self.data.seek(offset)
			self.data.seek(4+8+4,1)
			numIdx = self.data.readUInt()
			#print("numIdx",numIdx,self.data.tell())
			offset = self.Serialise()
			idxList=b''
			for t in range(numIdx):
				idxList+=self.data.readBytes(2)
			self.data.seek(offset)
			self.data.seek(4+8+4+4+4+4+128+128+24+4+8+8,1)
			rapi.rpgBindPositionBufferOfs(vertList, noesis.RPGEODATA_FLOAT, 12, 0)
			rapi.rpgCommitTriangles(idxList, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
			

	def GeoSet(self):
		for i in range(1):
			print(self.data.tell())
			count = self.data.readUInt()
			offset = self.Serialise()
			print("  ",self.data.tell(),count)
			self.SubObj(count)
			self.data.seek(offset)
	def BONES(self):
			numB = self.numBones
			print('bones',self.numBones)
			printdata=''
			for i in range(numB):
				name   = noeStrFromBytes(self.data.readBytes(64))#.replace(' ','')
				parent = self.data.readInt()
				v1	 = self.data.read('3f')
				v2	 = self.data.read('3f')
				sphere = self.data.read('3f'),self.data.read('f')
				t1	 = self.data.read('4f'),self.data.read('3f'),self.data.readFloat()
				t2	 = self.data.read('4f'),self.data.read('3f'),self.data.readFloat()
				t3	 = self.data.read('4f'),self.data.read('3f'),self.data.readFloat()
				CollShapeCount = self.data.readUInt()
				self.data.seek(8,1)
				pad0   = self.data.readUInt()
				self.data.seek(8,1)
				pad1   = self.data.readUInt()
				snow   = self.data.readUInt()
				printdata+= '%s , %s , %s , %s\n'%(v1[0],v1[1],v1[2],name)
				bone   = NoeMat43()
				bone.__setitem__(3,v1)
				self.boneList.append(NoeBone(i,name,bone,None,parent))
				
			print(printdata)
