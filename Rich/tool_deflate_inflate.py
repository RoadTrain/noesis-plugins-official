from inc_noesis import *
import os

GAUSSIAN_BLUR_DEFAULT = 8.0

def registerNoesisTypes():
	handle = noesis.registerTool("&Deflate file", deflateToolMethod, "Deflate a file")
	handle = noesis.registerTool("&Inflate file", inflateToolMethod, "Inflate a file")
	return 1

def validateInput(inVal):
	if os.path.exists(inVal) is not True:
		return "'" + inVal + "' does not exist!"
	return None
	
def deflateToolMethod(toolIndex):
	srcName = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "Open File", "Select a file to deflate.", noesis.getSelectedFile(), validateInput)
	if srcName is None:
		return 0

	f = open(srcName, "rb")
	decompData = f.read()
	f.close()
	
	dstDefault = os.path.splitext(srcName)[0] + "_deflated.bin"
	dstName = noesis.userPrompt(noesis.NOEUSERVAL_SAVEFILEPATH, "Save File", "Select destination path for the deflated file.", dstDefault, None)
	if dstName is None:
		return 0

	noeMod = noesis.instantiateModule()
	noesis.setModuleRAPI(noeMod)
	compData = rapi.compressDeflate(decompData)
	noesis.freeModule(noeMod)

	f = open(dstName, "wb")
	f.write(compData)
	f.close()

	noesis.messagePrompt("Successfully deflated file.")	
	return 0

def inflateToolMethod(toolIndex):
	srcName = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "Open File", "Select a file to inflate.", noesis.getSelectedFile(), validateInput)
	if srcName is None:
		return 0

	f = open(srcName, "rb")
	compData = f.read()
	f.close()
	
	dstDefault = os.path.splitext(srcName)[0] + "_inflated.bin"
	dstName = noesis.userPrompt(noesis.NOEUSERVAL_SAVEFILEPATH, "Save File", "Select destination path for the inflated file.", dstDefault, None)
	if dstName is None:
		return 0

	noeMod = noesis.instantiateModule()
	noesis.setModuleRAPI(noeMod)
	decompData = rapi.decompInflate(compData, rapi.getInflatedSize(compData))
	noesis.freeModule(noeMod)

	f = open(dstName, "wb")
	f.write(decompData)
	f.close()

	noesis.messagePrompt("Successfully inflated file.")	
	return 0
