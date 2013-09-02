from inc_noesis import *

def registerNoesisTypes():
	handle = noesis.register("Perfect World Texture", ".wtex")
	noesis.setHandlerTypeCheck(handle, wtexCheckType)
	noesis.setHandlerLoadRGBA(handle, wtexLoadRGBA)
	return 1

def wtexCheckType(data):
	if len(data) < 40 or (noeUnpackFrom("i", data, 32)[0]>>8) != 0x355854:
		return 0
	return 1

def wtexLoadRGBA(data, texList):
	dataOfs = noeUnpack("i", data[:4])[0]
	if noeUnpackFrom("i", data, dataOfs)[0] == 0x20534444: #dds
		print("Loading as DDS.")
		texture = rapi.loadTexByHandler(data[dataOfs:], ".dds")
	else:
		print("Loading as CRN.")
		texture = rapi.loadTexByHandler(data[dataOfs:], ".crn")

	texList.append(texture)
	return 1
