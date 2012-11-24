class switch(object):
	def __init__(self, value):
		self.value = value
		self.fall = False

	def __iter__(self):
		"""Return the match method once, then stop"""
		yield self.match
		raise StopIteration
    
	def match(self, *args):
		"""Indicate whether or not to enter a case suite"""
		if self.fall or not args:
			return True
		elif self.value in args: # changed for v1.5, see below
			self.fall = True
			return True
		else:
			return False
from inc_noesis import *

import noesis

#rapi methods should only be used during handler callbacks
import rapi

#registerNoesisTypes is called by Noesis to allow the script to register formats.
#Do not implement this function in script files unless you want them to be dedicated format modules!
def registerNoesisTypes():
	handle = noesis.register("Phantasy Star Online 2", ".aqo")
	noesis.setHandlerTypeCheck(handle, pso2CheckType)
	noesis.setHandlerLoadModel(handle, pso2LoadModel)
	#noesis.setHandlerWriteModel(handle, pso2WriteModel)
	#noesis.setHandlerWriteAnim(handle, pso2WriteAnim)
	#noesis.logPopup()
	#print("The log can be useful for catching debug prints from preview loads.\nBut don't leave it on when you release your script, or it will probably annoy people.")
	return 1

#check if it's this type based on the data

def pso2CheckType(data):
	bs = NoeBitStream(data)
	aqoMagic = bs.readInt()
	if aqoMagic != 0x6F7161:
		return 0
	return 1       

#load the model
def pso2LoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	bs = NoeBitStream(data)
	Bones = []
	Bone_Pallet = []
	Bone_Matrix = []
	Bone_Name = []
	Bone_Parent = []
	vertSize = []
	vertCount = []
	vtxeOffset = []
	vtxlOffset = []
	psetOffset = []

	boneFileName = rapi.getDirForFilePath(rapi.getInputName()) + rapi.getLocalFileName(rapi.getInputName()).rstrip(".aqo") + ".aqn"
	if (rapi.checkFileExists(boneFileName)):
		boneData = rapi.loadIntoByteArray(boneFileName)
		if boneData is not None:
			bd = NoeBitStream(boneData)
		bd.seek(0xC, NOESEEK_ABS)
		start = bd.readInt()
		bd.seek(start + 0x10, NOESEEK_ABS)
		while not bd.checkEOF():
			chunkStart = bd.tell()
			chunkType = bd.readBytes(4).decode("ASCII")
			chunkSize = bd.readInt()
			subChunkType = bd.readBytes(4).decode("ASCII")
			#print([chunkType,chunkSize,subChunkType])

			for case in switch(subChunkType):
				if case('AQGF'):
					bd.seek(chunkStart + chunkSize, NOESEEK_ABS)
					break
				if case('ROOT'):
					bd.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
					break
				if case('NODE'):
					bd.seek(6, NOESEEK_REL)
					while bd.tell() < chunkStart + 8 + chunkSize:
						nodeChunkStart = bd.tell()
						nodeChunkType = bd.readUShort()
						#print([nodeChunkType,nodeChunkStart])
						for case in switch(nodeChunkType):
							if case(0x903):
								nodeTest1 = bd.readInt()
								break
							if case(0x804):
								BoneParent = bd.readInt()
								Bone_Parent.append(BoneParent)
								break
							if case(0x80F):
								nodeTest1 = bd.readInt()
								break
							if case(0x805):
								nodeTest1 = bd.readInt()
								break
							if case(0x806):
								nodeTest1 = bd.readInt()
								break
							if case(0x4A07):
								bd.seek(0xD, NOESEEK_REL)
								break
							if case(0x4A08):
								bd.seek(0xD, NOESEEK_REL)
								break
							if case(0x4A09):
								bd.seek(0xD, NOESEEK_REL)
								break
							if case(0xCA0A):
								bd.seek(0x2, NOESEEK_REL)
								BoneMatrix = NoeMat44.fromBytes(bd.readBytes(64)).toMat43()
								Bone_Matrix.append(BoneMatrix.inverse())
								break
							if case(0x90B):
								nodeTest1 = bd.readInt()
								break
							if case(0x90C):
								nodeTest1 = bd.readInt()
								break
							if case(0x20D):
								nSize = bd.readUByte()
								boneName = bd.readBytes(nSize).decode("ASCII")
								Bone_Name.append(boneName)
								break
							if case(0xFD):
								break
					break
				if case('NODO'):
					bd.seek(bd.getSize(), NOESEEK_ABS)
					break
				if case(): # default, could also just omit condition or 'if True'
					bd.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
					# No need to break here, it'll stop anyway
		for a in range(0, len(Bone_Matrix)):
			bn = NoeBone(a, Bone_Name[a], Bone_Matrix[a], None, Bone_Parent[a])
			Bones.append(bn)
	aqoMagic = bs.readInt()
	while not bs.checkEOF():
		chunkStart = bs.tell()
		chunkType = bs.readBytes(4).decode("ASCII")
		chunkSize = bs.readInt()
		subChunkType = bs.readBytes(4).decode("ASCII")
		#print([chunkType,chunkSize,subChunkType])

		for case in switch(subChunkType):
			if case('AQGF'):
				bs.seek(chunkStart + chunkSize, NOESEEK_ABS)
				break
			if case('ROOT'):
				bs.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
				break
			if case('OBJC'):
				bs.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
				break
			if case('VSET'):
				while bs.tell() < chunkStart + 8 + chunkSize:
					vsetChunkStart = bs.tell()
					vsetChunkType = bs.readUShort()
					#print([vsetChunkStart,vsetChunkType])
					for case in switch(vsetChunkType):
						if case(0x9B6):
							vsetVertSize = bs.readInt()
							vertSize.append(vsetVertSize)
							#print([vsetChunkType,vsetVertSize])
							break
						if case(0x9BF):
							vsetUnk01 = bs.readInt()
							break
						if case(0x9B9):
							vsetVertCount = bs.readInt()
							vertCount.append(vsetVertCount)
							#print([vsetChunkType,vsetVertCount])
							break
						if case(0x9C4):
							vsetUnk01 = bs.readInt()
							break
						if case(0x9BD):
							vsetUnk01 = bs.readInt()
							if vsetUnk01 == 0:
								Bone_Pallet.append(())
							break
						if case(0x86BE):
							test = bs.readByte()
							test = bs.readUByte()
							BonePallet = bs.read("H"*(test + 1))
							Bone_Pallet.append(BonePallet)
							break
						if case(0x6BE):
							test = bs.readByte()
							test = bs.readUByte()
							Bone_Pallet.append(())
							break
						if case(0x9C8):
							vsetUnk01 = bs.readInt()
							break
						if case(0x9CC):
							vsetUnk01 = bs.readInt()
							break
						if case(0x9C9):
							vsetUnk01 = bs.readInt()
							break
						if case(0xFD):
							break

				bs.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
				break
			if case('VTXE'):
				vtxeOffset.append([chunkStart,chunkSize])
				bs.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
				break
			if case('MESH'):
				bs.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
				break
			if case('REND'):
				bs.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
				break
			if case('SHAD'):
				bs.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
				break
			if case('SHAP'):
				bs.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
				break
			if case('TSTA'):
				bs.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
				break
			if case('TSET'):
				bs.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
				break
			if case('VTXL'):
				vtxlOffset.append([chunkStart,chunkSize])
				bs.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
				break
			if case('TEXF'):
				bs.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
				break
			if case('PSET'):
				psetOffset.append(chunkStart)
				bs.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
				break
			if case(): # default, could also just omit condition or 'if True'
				bs.seek(chunkStart + 8 + chunkSize, NOESEEK_ABS)
				# No need to break here, it'll stop anyway
		
	#bs.readBytes(8).decode("ASCII").rstrip("\0")
	FaceOff = psetOffset[0] + 18
	rapi.rpgSetUVScaleBias(NoeVec3 ((1.0, -1.0, 1.0)), NoeVec3 ((1.0, 1.0, 1.0)))
	for i in range(0, len(vertSize)):
		bs.seek(vtxlOffset[i][0] + 18, NOESEEK_ABS)
		test = bs.readByte()
		if test == 8:
			test = bs.readUByte()
			VertBuff = bs.readBytes(vtxlOffset[i][1] - 12)
		elif test == 24:
			test = bs.readInt()
			VertBuff = bs.readBytes(vtxlOffset[i][1] - 15)
		else:
			test = bs.readUShort()
			VertBuff = bs.readBytes(vtxlOffset[i][1] - 13)
		bs.seek(vtxeOffset[i][0] + 18, NOESEEK_ABS)
		for j in range(0, (vtxeOffset[i][1] - 10) // 26):
			vtxeChunkTypeid = bs.readUShort()
			vtxeChunkType = bs.readInt()
			vtxeChunkType2id = bs.readUShort()
			vtxeChunkType2 = bs.readInt()
			vtxeChunkPosId = bs.readUShort()
			vtxeChunkPos = bs.readInt()
			vtxeChunkUnkid = bs.readUShort()
			vtxeChunkUnk = bs.readInt()
			vtxeChunkTerm = bs.readUShort()
			if vtxeChunkType == 0:
				rapi.rpgBindPositionBufferOfs(VertBuff, noesis.RPGEODATA_FLOAT, vertSize[i], vtxeChunkPos)
			elif vtxeChunkType == 1:
				rapi.rpgBindBoneWeightBufferOfs(VertBuff, noesis.RPGEODATA_FLOAT, vertSize[i], vtxeChunkPos, 4)
			elif vtxeChunkType == 2:
				#rapi.rpgBindNormalBufferOfs(VertBuff, noesis.RPGEODATA_FLOAT, vertSize[i], vtxeChunkPos)
				pass
			elif vtxeChunkType == 3:
				rapi.rpgBindColorBufferOfs(VertBuff, noesis.RPGEODATA_UBYTE, vertSize[i], vtxeChunkPos, 4)
			elif vtxeChunkType == 4:
				pass#4 bytes as floats 2nd vertex color?
			elif vtxeChunkType == 11:
				rapi.rpgBindBoneIndexBufferOfs(VertBuff, noesis.RPGEODATA_UBYTE, vertSize[i], vtxeChunkPos, 4)
			elif vtxeChunkType == 16:
				rapi.rpgBindUV1BufferOfs(VertBuff, noesis.RPGEODATA_FLOAT, vertSize[i], vtxeChunkPos)
			elif vtxeChunkType == 17:
				rapi.rpgBindUV2BufferOfs(VertBuff, noesis.RPGEODATA_FLOAT, vertSize[i], vtxeChunkPos)
			elif vtxeChunkType == 32:
				pass#tangents?
			elif vtxeChunkType == 33:
				pass#binormals/tangents?
			else:
				print(vtxeChunkType)
		bs.seek(FaceOff, NOESEEK_ABS)
		bs.seek(0x1A, NOESEEK_REL)
		test = bs.readByte()
		if test == 8:
			FaceCount = bs.readUByte()
			FaceBuff = bs.readBytes((FaceCount + 1) * 2)
		elif test == 16:
			FaceCount = bs.readUShort()
			FaceBuff = bs.readBytes((FaceCount + 1) * 2)
		else:
			FaceCount = bs.readInt()
			FaceBuff = bs.readBytes((FaceCount + 1) * 2)
		bs.seek(0x8, NOESEEK_REL)
		FaceOff = bs.tell()
		rapi.rpgSetName(str(i))
		rapi.rpgSetMaterial(str(i))
		material = NoeMaterial((str(i)), "")
		if len(Bone_Pallet) > 0:
			if len(Bone_Pallet[i]) > 0:
				rapi.rpgSetBoneMap(Bone_Pallet[i])
		
		rapi.rpgCommitTriangles(FaceBuff, noesis.RPGEODATA_USHORT, FaceCount + 1, noesis.RPGEO_TRIANGLE_STRIP, 1)
	mdl = rapi.rpgConstructModel()
	mdl.setBones(Bones)
	mdlList.append(mdl)
	rapi.rpgClearBufferBinds()	
	return 1