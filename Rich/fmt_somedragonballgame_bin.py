from inc_noesis import *
import os
import re

def registerNoesisTypes():
	handle = noesis.register("Some DB Game Tex Bin", ".bin")
	noesis.setHandlerTypeCheck(handle, dbbCheckType)
	noesis.setHandlerLoadRGBA(handle, dbbLoadRGBA)
	
	handle = noesis.registerTool("Inject DB Game Tex Bin", dbinjectToolMethod, "Inject DB Game Tex Bin")
	noesis.setToolFlags(handle, noesis.NTOOLFLAG_CONTEXTITEM)
	noesis.setToolVisibleCallback(handle, dbinjectContextVisible)
	return 1
	
def dbinjectContextVisible(toolIndex, selectedFile):
	if selectedFile is None or selectedFile.lower().endswith(".bin") is not True or os.path.exists(selectedFile) is not True:
		return 0
	return 1
	
globalImageCount = 0
globalLastInjectedImagePath = ""

def dbinjectValidateImage(inVal):
	if os.path.exists(inVal) is not True:
		return "File does not exist or cannot be read."
	return None
	
def dbinjectShiftAlphaKernel(imageData, ofs, kernelData, userData):
	imageData[3] = (imageData[3]+1)>>1

def dbinjectValidateImageIndex(inVal):
	global globalImageCount
	if inVal < 0 or inVal >= globalImageCount:
		return "Value is out of range."
	return None
	
def dbinjectInvoked(binName):
	data = rapi.loadIntoByteArray(binName)
	if dbbCheckType(data) == 0:
		print("Doesn't look like this is a valid file.")
		return
	bs = NoeBitStream(data)
	imgInfo = dbbParseImageInfo(bs)
	if len(imgInfo) <= 0:
		print("No images were parsed from the file.")
		return

	global globalImageCount
	globalImageCount = len(imgInfo)

	global globalLastInjectedImagePath
	imageImportPath = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "Open Image", "Select the image to inject. (WARNING: this will modify the selected .bin file)", globalLastInjectedImagePath, dbinjectValidateImage)
	if imageImportPath is None:
		return

	injectTex = rapi.loadExternalTex(imageImportPath)
	if injectTex is None:
		print("Error: Could not load image for file:", imageImportPath)
		return
		
	try:
		#try to determine the desired injection index from the filename of the texture being injected
		fileNums = re.findall(r"[0-9]+", rapi.getExtensionlessName(rapi.getLocalFileName(imageImportPath)))
		defaultImageIndex = int(fileNums[len(fileNums)-1])
		if defaultImageIndex < 0 or defaultImageIndex >= globalImageCount:
			defaultImageIndex = 0
	except:
		defaultImageIndex = 0

	imageIndex = noesis.userPrompt(noesis.NOEUSERVAL_INT, "Image Index", "Enter the index of the image in the bundle you want to replace. (between 0 and %i)"%(globalImageCount-1), repr(defaultImageIndex), dbinjectValidateImageIndex)
	if imageIndex is None:
		return

	print("Injecting image data into bundle.")
		
	injectPix = rapi.imageGetTexRGBA(injectTex)
	#shift the alpha down
	injectPix = rapi.imageKernelProcess(injectPix, injectTex.width, injectTex.height, 4, dbinjectShiftAlphaKernel)
		
	globalLastInjectedImagePath = imageImportPath
	imgOfs, palOfs, imgSize, palSize = imgInfo[imageIndex]
	bs.seek(imgOfs, NOESEEK_ABS)
	imgData = bs.readBytes(imgSize)
	imgBs = NoeBitStream(imgData[:96])
	imgData = imgData[96:]
	
	imgBs.seek(48, NOESEEK_ABS)
	imgWidth = imgBs.readInt()
	imgHeight = imgBs.readInt()
	if palOfs > 0:
		#we need to resample and repalettize
		imgWidth <<= 1
		imgHeight <<= 2
		injectPix = rapi.imageResample(injectPix, injectTex.width, injectTex.height, imgWidth, imgHeight)
		#convert down to 16 colors
		palData = rapi.imageGetPalette(injectPix, imgWidth, imgHeight, 16, 1, 1)
		idxPix = rapi.imageApplyPalette(injectPix, imgWidth, imgHeight, palData, 16, 1)
		#now twiddle it
		idxPix = rapi.imageTwiddlePS2(idxPix, imgWidth, imgHeight, 4)
		if len(palData) != palSize-96-32:
			print("Error: Unexpected image palette size:", palSize-96-32, "versus", len(palData))
		elif len(idxPix) != imgSize-96-32:
			print("Error: Unexpected paletted image size:", imgSize-96-32, "versus", len(idxPix))
		else:
			data[palOfs+96:palOfs+96+len(palData)] = palData
			data[imgOfs+96:imgOfs+96+len(idxPix)] = idxPix
	else:
		#it's raw rgba32, we don't have to do anything other than resize it
		injectPix = rapi.imageResample(injectPix, injectTex.width, injectTex.height, imgWidth, imgHeight)
		if len(injectPix) != imgSize-96-32:
			print("Error: Unexpected raw image size:", imgSize-96-32, "versus", len(injectPix))
		else:
			data[imgOfs+96:imgOfs+96+len(injectPix)] = injectPix
			
	#write the modified data back out
	f = open(binName, "wb")
	f.write(data)
	f.close()
	print("Injection process complete.")
	
def dbinjectToolMethod(toolIndex):
	srcName = noesis.getSelectedFile()
	if srcName is None or os.path.exists(srcName) is not True:
		noesis.messagePrompt("Selected file isn't readable through the standard filesystem.")
		return 0

	noeMod = noesis.instantiateModule()
	noesis.setModuleRAPI(noeMod)

	noesis.logPopup()
	dbinjectInvoked(srcName)

	noesis.freeModule(noeMod)
	
	return 0
	
def dbbCheckType(data):
	if len(data) < 32:
		return 0
	bs = NoeBitStream(data)
	numEntries = bs.readInt()
	headerEndOfs = 32 + numEntries*64
	if headerEndOfs <= 0 or headerEndOfs >= len(data):
		return 0
	#crappy validation given the generic extension, but good enough
	return 1

def dbbParseImageInfo(bs):
	bs.seek(0, NOESEEK_ABS)
	numEntries = bs.readInt()
	bs.seek(28, NOESEEK_REL)
	imgInfo = []
	for i in range(0, numEntries):
		imgOfs = bs.readInt()<<2
		palOfs = bs.readInt()<<2
		imgSize = bs.readInt()
		palSize = bs.readInt()
		imgInfo.append((imgOfs, palOfs, imgSize, palSize))
		bs.seek(48, NOESEEK_REL)
	return imgInfo

def dbbLoadRGBA(data, texList):
	if noesis.getAPIVersion() < 71:
		noesis.messagePrompt("Update your Noesis version!")
		return 0

	rapi.processCommands("-texnorepfn")
		
	bs = NoeBitStream(data)
	imgInfo = dbbParseImageInfo(bs)

	#read the image data out
	for i in range(0, len(imgInfo)):
		imgOfs, palOfs, imgSize, palSize = imgInfo[i]
		bs.seek(imgOfs, NOESEEK_ABS)
		imgData = bs.readBytes(imgSize)
		imgBs = NoeBitStream(imgData[:96])
		imgData = imgData[96:]
		
		imgBs.seek(48, NOESEEK_ABS)
		imgWidth = imgBs.readInt()
		imgHeight = imgBs.readInt()
		if palOfs > 0:
			imgWidth <<= 1
			imgHeight <<= 2
			bs.seek(palOfs, NOESEEK_ABS)
			palData = bs.readBytes(palSize)[96:]
			imgData = rapi.imageUntwiddlePS2(imgData, imgWidth, imgHeight, 4)
			imgData = rapi.imageDecodeRawPal(imgData, palData, imgWidth, imgHeight, 4, "r8g8b8a8")
			
		imgData = rapi.imageScaleRGBA32(imgData, (1.0, 1.0, 1.0, 2.0), imgWidth, imgHeight)
		texList.append(NoeTexture("db_tex_%02i"%i, imgWidth, imgHeight, imgData, noesis.NOESISTEX_RGBA32))
		
	return 1
