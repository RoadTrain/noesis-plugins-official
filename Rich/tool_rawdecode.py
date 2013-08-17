from inc_noesis import *
import os

RAWDECODE_STRING = "640;480;r5g5b5p1;0"

def registerNoesisTypes():
	handle = noesis.registerTool("Raw image decode", rdToolMethod, "Perform a raw image decode.")
	noesis.setToolFlags(handle, noesis.NTOOLFLAG_CONTEXTITEM)
	return 1

def rdGetOptionDict(optionString):
	try:
		l = optionString.split(";")
		return {"width":int(l[0]), "height":int(l[1]), "format":l[2], "offset":int(l[3])}
	except:
		return None
	
def rdValidateOptionString(inVal):
	options = rdGetOptionDict(inVal)
	if options is None:
		return "Invalid format string."
	return None
	
def rdToolMethod(toolIndex):
	srcName = noesis.getSelectedFile()
	if srcName is None or os.path.exists(srcName) is not True:
		noesis.messagePrompt("Selected file isn't readable through the standard filesystem.")
		return 0

	#prompt for the decoding spec string
	global RAWDECODE_STRING
	optionString = noesis.userPrompt(noesis.NOEUSERVAL_STRING, "Option String", "Enter the decode specification string in the format of width;height;format;offset.", RAWDECODE_STRING, rdValidateOptionString)
	if optionString is None:
		return 0
	#store the string globally so it can be remembered next time the script is run
	RAWDECODE_STRING = optionString
	#parse options out of the spec string
	options = rdGetOptionDict(optionString)
	if options is None:
		return 0

	#create a Noesis RAPI module instance and set it as the active rapi interface
	noeMod = noesis.instantiateModule()
	noesis.setModuleRAPI(noeMod)

	#set the temporary destination file name
	dstName = noesis.getScenesPath() + "rawdecode_results.png"
	
	#load the file up and decode it using the spec string
	rawData = rapi.loadIntoByteArray(srcName)
	rgba = rapi.imageDecodeRaw(rawData[options["offset"]:], options["width"], options["height"], options["format"])
	#create a texture for the decoded image
	tex = NoeTexture(dstName, options["width"], options["height"], rgba, noesis.NOESISTEX_RGBA32)
	
	#free the RAPI module instance
	noesis.freeModule(noeMod)

	#save the decoded image out from the texture object
	if noesis.saveImageRGBA(dstName, tex) is not True:
		noesis.messagePrompt("Error writing decoded image.")
		return 0
	
	#open the temp file in preview, and remove it after it's been opened
	noesis.openAndRemoveTempFile(dstName)
	return 0
