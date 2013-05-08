from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
	handle = noesis.register("Fate Extra", ".Im")
	noesis.setHandlerTypeCheck(handle, noepyCheckType)
	noesis.setHandlerLoadModel(handle, noepyLoadModel) #see also noepyLoadModelRPG

	noesis.logPopup()
	return 1


#check if it's this type based on the data
def noepyCheckType(data):
	bs = NoeBitStream(data)
	return 1       

#load the model
def noepyLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	bs = NoeBitStream(data)
	#rapi.rpgSetPosScaleBias((-1,-1,1),(0,0,0))
	boneList = []

	boneCount = bs.readInt()
	boneOffset = bs.tell() + bs.readInt()
	texCount = bs.readInt()
	texOffset = bs.tell() + bs.readInt()
	matCount = bs.readInt()
	matOffset = bs.tell() + bs.readInt()
	meshCount = bs.readInt()
	meshOffset = bs.tell() + bs.readInt()

	bs.seek(boneOffset, NOESEEK_ABS)
	for i in range(0, boneCount):
		boneName = bs.readBytes(0x20).decode("ASCII").rstrip("\0")
		boneMtx = NoeMat44.fromBytes(bs.readBytes(0x40)).toMat43()
		bs.readBytes(0x40)
		boneParent = bs.readInt()
		bs.readBytes(0x8)
		pos = NoeVec3.fromBytes(bs.readBytes(12))
		bs.readBytes(0x8)
		quat = NoeQuat.fromBytes(bs.readBytes(16))
		NoeVec3.fromBytes(bs.readBytes(12))
		bs.readBytes(0x14)
		boneMtx = quat.toMat43()
		boneMtx[3] = pos
		newBone = NoeBone(i, boneName, boneMtx, None, boneParent)
		boneList.append(newBone)
	boneList = rapi.multiplyBones(boneList)

	texInfo = []
	texList = []
	bs.seek(texOffset, NOESEEK_ABS)
	for i in range(0, texCount):
		texName = bs.readBytes(0x20).decode("ASCII").rstrip("\0")
		texStart = bs.tell() + bs.readInt()
		bs.readBytes(0xC)
		texInfo.append([texName,texStart])
	#print(texInfo)
	for i in range(0, texCount):
		bs.seek(texInfo[i][1], NOESEEK_ABS)
		bs.readBytes(0xC)
		palOff = bs.tell() + bs.readInt()
		texType, unk02, pixWidth, pixHeight, unk03, unk04 = bs.read("6H")
		texSize = bs.readInt()
		texOff = bs.tell() + bs.readInt()
		bs.seek(texOff, NOESEEK_ABS)
		texData = bs.readBytes(texSize)
		bs.seek(palOff, NOESEEK_ABS)
		unk11, unk22 = bs.read("2H")
		palSize, Null = bs.read("2I")
		palStart = bs.tell() + bs.readInt()
		bs.seek(palStart, NOESEEK_ABS)
		palData = []
		for a in range(0, palSize // 4):
			pR, pG, pB, pA = bs.read("4B")
			if pR == 0 and pG == 255 and pB == 0 and pA == 255:
				pG = 0
				pA = 0
			palData.append(pR)
			palData.append(pG)
			palData.append(pB)
			palData.append(pA)
		palData = struct.pack("<" + 'B'*len(palData), *palData)
		if texType == 5:
			pix = rapi.imageUntwiddlePSP(texData, pixWidth, pixHeight, 8)
			pix = rapi.imageDecodeRawPal(pix, palData, pixWidth, pixHeight, 8, "r8g8b8a8")
		elif texType == 4:
			pix = rapi.imageUntwiddlePSP(texData, pixWidth, pixHeight, 4)
			pix = rapi.imageDecodeRawPal(pix, palData, pixWidth, pixHeight, 4, "r8g8b8a8")
		texList.append(NoeTexture(texInfo[i][0], pixWidth, pixHeight, pix, noesis.NOESISTEX_RGBA32))

	matList = []
	bs.seek(matOffset, NOESEEK_ABS)
	for i in range(0, matCount):
		matName = bs.readBytes(0x20).decode("ASCII").rstrip("\0")
		bs.readBytes(0xC)
		texID = bs.readInt()
		unk01, unk02, unk03, unk04 = bs.read("4B")
		bs.readBytes(0x8)
		material = NoeMaterial(matName, "")
		if texID >= 0:
			material.setTexture(texInfo[texID][0])
			#material.setOpacityTexture(texInfo[texID][0])
		matList.append(material)

	meshList = []
	bs.seek(meshOffset, NOESEEK_ABS)
	for i in range(0, meshCount):
		meshName = bs.readBytes(0x20).decode("ASCII").rstrip("\0")
		mshCount = bs.readInt()
		unk11 = bs.readInt()
		meshStart = bs.tell() + bs.readInt()
		bs.readBytes(0xC)
		meshList.append([meshName, meshStart, mshCount, unk11])
	#print(meshList)

	for a in range(0, len(meshList)):
		mshInfo = []
		#print(meshList[a][0])
		bs.seek(meshList[a][1], NOESEEK_ABS)
		for b in range(0, meshList[a][2]):
			unk20 = bs.readInt()
			matID = bs.readInt()
			mshC = bs.readInt()
			MshOff = bs.tell() + bs.readInt()
			mshInfo.append([matID, mshC, MshOff])
		#print(mshInfo)
		mshInfo2 = []
		for b in range(0, len(mshInfo)):
			bs.seek(mshInfo[b][2], NOESEEK_ABS)
			for c in range(0, mshInfo[b][1]):
				meshPc = bs.readInt()
				vType  = bs.readInt()
				meshPc2  = bs.readInt()
				mshPo  = bs.tell() + bs.readInt()
				mshPo2 = bs.tell() + bs.readInt()
				mshInfo2.append([meshPc, vType, meshPc2, mshPo, mshPo2, matList[(mshInfo[b][0])].name])
		#print(mshInfo2)
		for b in range(0, len(mshInfo2)):
			mshInfo3 = []
			rapi.rpgSetMaterial(mshInfo2[b][5])
			bs.seek(mshInfo2[b][3], NOESEEK_ABS)
			idxList = [[0, 0, 0, 0, 0, 0, 0, 0]]
			for c in range(0, mshInfo2[b][2]):
				idxList[0][c] = bs.readInt()
			bs.seek(mshInfo2[b][4], NOESEEK_ABS)
			#print(idxList)
			for c in range(0, mshInfo2[b][0]):
				mshId2     = bs.readInt()
				vertCount  = bs.readInt()
				vertStart  = bs.tell() + bs.readInt()
				mshInfo3.append([mshId2, vertCount, vertStart])
			#print(mshInfo3)
			for c in range(0, len(mshInfo3)):
				#print(mshInfo3[c])
				bs.seek(mshInfo3[c][2], NOESEEK_ABS)
				rapi.rpgSetName(meshList[a][0])
				#rapi.rpgSetName(meshList[a][0] + "_" + str(b) + "_" + str(c) + "_" + str(mshInfo2[b][1]))

				vertStride = 0
				if mshInfo2[b][1] == 7:
					vertStride = 0x18
					vertBuff = bs.readBytes(mshInfo3[c][1] * vertStride)
					rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0xC)
					rapi.rpgBindColorBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, vertStride, 0x8, 4)
					rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0)
				elif mshInfo2[b][1] == 24:
					vertStride = 0x1C
					vertBuff = bs.readBytes(mshInfo3[c][1] * vertStride)
					rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x10)
					rapi.rpgBindColorBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, vertStride, 0xC, 4)
					rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x4)
				elif mshInfo2[b][1] == 25:
					vertStride = 0x1C
					vertBuff = bs.readBytes(mshInfo3[c][1] * vertStride)
					rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x10)
					rapi.rpgBindColorBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, vertStride, 0xC, 4)
					rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x4)
				elif mshInfo2[b][1] == 26:
					vertStride = 0x20
					vertBuff = bs.readBytes(mshInfo3[c][1] * vertStride)
					rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x14)
					rapi.rpgBindColorBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, vertStride, 0x10, 4)
					rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x8)
				elif mshInfo2[b][1] == 27:
					vertStride = 0x20
					vertBuff = bs.readBytes(mshInfo3[c][1] * vertStride)
					rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x14)
					rapi.rpgBindColorBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, vertStride, 0x10, 4)
					rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x8)
				elif mshInfo2[b][1] == 28:
					vertStride = 0x24
					vertBuff = bs.readBytes(mshInfo3[c][1] * vertStride)
					rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x18)
					rapi.rpgBindColorBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, vertStride, 0x14, 4)
					rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0xC)
				elif mshInfo2[b][1] == 29:
					vertStride = 0x24
					vertBuff = bs.readBytes(mshInfo3[c][1] * vertStride)
					rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x18)
					rapi.rpgBindColorBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, vertStride, 0x14, 4)
					rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0xC)
				elif mshInfo2[b][1] == 30:
					vertStride = 0x28
					vertBuff = bs.readBytes(mshInfo3[c][1] * vertStride)
					rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x1C)
					rapi.rpgBindColorBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, vertStride, 0x18, 4)
					rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x10)
				elif mshInfo2[b][1] == 23:
					vertStride = 0x28
					vertBuff = bs.readBytes(mshInfo3[c][1] * vertStride)
					rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x1C)
					rapi.rpgBindColorBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, vertStride, 0x18, 4)
					rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x10)

				else:
					print(bs.tell())
					print("unknown found " + str(mshInfo2[b][1]))
				
				vs = NoeBitStream(vertBuff)
				tmp = []
				tmp2 = []
				weight = []
				index = []
				if vertStride == 0x18:
					for d in range(0, mshInfo3[c][1]):
						w1, w2, w3, w4, w5, w6, w7, w8 = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
						index.append(idxList[0][0]); index.append(idxList[0][1]); index.append(idxList[0][2]); index.append(idxList[0][3])
						index.append(idxList[0][4]); index.append(idxList[0][5]); index.append(idxList[0][6]); index.append(idxList[0][7])
						weight.append(w1); weight.append(w2); weight.append(w3); weight.append(w4); weight.append(w5); weight.append(w6); weight.append(w7); weight.append(w8)
						vs.readBytes(0xC)
						tmp.append([vs.readUInt(), vs.readUInt(), vs.readUInt()])
				elif vertStride == 0x1C:
					for d in range(0, mshInfo3[c][1]):
						w1, w2, w3, w4, w5, w6, w7, w8 = [vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
						index.append(idxList[0][0]); index.append(idxList[0][1]); index.append(idxList[0][2]); index.append(idxList[0][3])
						index.append(idxList[0][4]); index.append(idxList[0][5]); index.append(idxList[0][6]); index.append(idxList[0][7])
						weight.append(w1); weight.append(w2); weight.append(w3); weight.append(w4); weight.append(w5); weight.append(w6); weight.append(w7); weight.append(w8)
						vs.readBytes(0xC)
						tmp.append([vs.readUInt(), vs.readUInt(), vs.readUInt()])
				elif vertStride == 0x20:
					for d in range(0, mshInfo3[c][1]):
						w1, w2, w3, w4, w5, w6, w7, w8 = [vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF, 0.0, 0.0, 0.0, 0.0]
						index.append(idxList[0][0]); index.append(idxList[0][1]); index.append(idxList[0][2]); index.append(idxList[0][3])
						index.append(idxList[0][4]); index.append(idxList[0][5]); index.append(idxList[0][6]); index.append(idxList[0][7])
						weight.append(w1); weight.append(w2); weight.append(w3); weight.append(w4); weight.append(w5); weight.append(w6); weight.append(w7); weight.append(w8)
						vs.readBytes(0xC)
						tmp.append([vs.readUInt(), vs.readUInt(), vs.readUInt()])
				elif vertStride == 0x24:
					for d in range(0, mshInfo3[c][1]):
						w1, w2, w3, w4, w5, w6, w7, w8 = [vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF, 0.0, 0.0]
						index.append(idxList[0][0]); index.append(idxList[0][1]); index.append(idxList[0][2]); index.append(idxList[0][3])
						index.append(idxList[0][4]); index.append(idxList[0][5]); index.append(idxList[0][6]); index.append(idxList[0][7])
						weight.append(w1); weight.append(w2); weight.append(w3); weight.append(w4); weight.append(w5); weight.append(w6); weight.append(w7); weight.append(w8)
						vs.readBytes(0xC)
						tmp.append([vs.readUInt(), vs.readUInt(), vs.readUInt()])
				elif vertStride == 0x28:
					for d in range(0, mshInfo3[c][1]):
						w1, w2, w3, w4, w5, w6, w7, w8 = [vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF, vs.readUShort() / 0x7FFF]
						index.append(idxList[0][0]); index.append(idxList[0][1]); index.append(idxList[0][2]); index.append(idxList[0][3])
						index.append(idxList[0][4]); index.append(idxList[0][5]); index.append(idxList[0][6]); index.append(idxList[0][7])
						weight.append(w1); weight.append(w2); weight.append(w3); weight.append(w4); weight.append(w5); weight.append(w6); weight.append(w7); weight.append(w8)
						vs.readBytes(0xC)
						tmp.append([vs.readUInt(), vs.readUInt(), vs.readUInt()])
				indexBuff  = struct.pack('B'*len(index), *index)
				weightBuff = struct.pack('f'*len(weight), *weight)
				rapi.rpgBindBoneIndexBuffer(indexBuff, noesis.RPGEODATA_BYTE, 8, 8)
				rapi.rpgBindBoneWeightBuffer(weightBuff, noesis.RPGEODATA_FLOAT, 0x20, 8)
				flip = 0
				step = 1
				if mshInfo3[c][0] == 0:
					step = 3
				for d in range(0, mshInfo3[c][1] - 2, step):
					if (tmp[d] != tmp[(d + 1)]) and (tmp[d] != tmp[(d + 2)]) and (tmp[d + 1] != tmp[(d + 2)]):
						tmp2.append(d)
						tmp2.append(d + 1 + flip)
						tmp2.append(d + 2 - flip)
						if mshInfo3[c][0] != 0:
							flip = 1 - flip
					else:
						flip = 0
						#print(d)
				faceBuff = struct.pack('H'*len(tmp2), *tmp2)
				if len(faceBuff) > 3:
					rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, len(tmp2), noesis.RPGEO_TRIANGLE, 1)
				rapi.rpgClearBufferBinds() 

	mdl = rapi.rpgConstructModel()
	mdl.setModelMaterials(NoeModelMaterials(texList, matList))
	mdlList.append(mdl)
	mdl.setBones(boneList)

  
	return 1