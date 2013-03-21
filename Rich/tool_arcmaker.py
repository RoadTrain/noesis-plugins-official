from inc_noesis import *
import os
import subprocess

COMPRESS_TYPE = 1
EXTERNAL_ARCHIVER_EXE = None #"C:\\somesdk\\tools\\somecompressionapp.exe"

def registerNoesisTypes():
	handle = noesis.registerTool("&Create archive", makeArcToolMethod, "Create an archive from a folder of data")
	handle = noesis.register("Test archive", ".testarc")
	noesis.setHandlerExtractArc(handle, testArcExtract)

	return 1

def testArcExtract(fileName, fileLen, justChecking):
	if fileLen < 16:
		return 0
	with open(fileName, "rb") as f:
		id = noeStrFromBytes(f.read(8))
		if id != "TESTARCV":
			return 0
		ver, numFiles = noeUnpack("<ii", f.read(8))
		if ver != 1 or numFiles <= 0:
			return 0
		if justChecking:
			return 1

		print("Extracting", numFiles, "files from archive.")
		for i in range(0, numFiles):
			nameLen = noeUnpack("<i", f.read(4))[0]
			name = noeStrFromBytes(f.read(nameLen))
			decompSize, compSize, paddedSize, compType = noeUnpack("<iiii", f.read(16))
			compData = f.read(paddedSize)
			print("Writing '" + name + "'.")
			if compType == 0: #decompressed
				rapi.exportArchiveFile(name, compData)
			elif compType == 1: #inflate
				decompData = rapi.decompInflate(compData, decompSize)
				rapi.exportArchiveFile(name, decompData)
			else: #unsupported
				print("Warning: Unsupported decompression type.")
				rapi.exportArchiveFile(name, compData)
	return 1

def validateInput(inVal):
	if os.path.isdir(inVal) is not True:
		return "'" + inVal + "' is not a valid directory!"
	return None

def makeArc(srcDir, dstName):
	noeMod = noesis.instantiateModule()
	noesis.setModuleRAPI(noeMod)

	noesis.logPopup()

	print("Constructing archive.")
	arcFile = open(dstName, "wb")
	arcFile.write("TESTARCV".encode("ASCII"))
	arcFile.write(noePack("<ii", 1, 0))

	dirList = os.listdir(srcDir)
	numObj = 0
	numFiles = 0
	for fileName in dirList:
		srcFileName = srcDir + "\\" + fileName
		if os.path.islink(srcFileName) or os.path.isdir(srcFileName):
			continue
		padByteName = bytearray(fileName.encode("ASCII"))
		padLen = len(padByteName) + 4
		fixedPadLen = padLen
		if fixedPadLen & 15:
			fixedPadLen += (16-(fixedPadLen & 15))
		exLen = fixedPadLen-padLen
		padByteName.extend(0 for i in range(0, exLen))

		numFiles += 1
		arcFile.write(noePack("<i", fixedPadLen-4))
		arcFile.write(padByteName)

		print("Compressing '" + srcFileName + "'.")
		compType = COMPRESS_TYPE
		compData = None
		srcFileLen = os.path.getsize(srcFileName)
		if compType == 0: #no compression
			f = open(srcFileName, "rb")
			compData = f.read()
			f.close()
		elif EXTERNAL_ARCHIVER_EXE is None or compType == 1: #use noesis deflate implementation
			f = open(srcFileName, "rb")
			decompData = f.read()
			f.close()
			compData = rapi.compressDeflate(decompData)
			if len(compData) >= len(decompData): #bad results, do not compress
				compData = decompData
				compType = 0
		else: #use an external tool
			compParm = "-lh" if compType == 2 else "-lex"
			compressedFileName = srcFileName + ".noesis_compressed"
			subprocess.call([EXTERNAL_ARCHIVER_EXE, compParm, "-o", compressedFileName, srcFileName], shell = True)
			f = open(compressedFileName, "rb")
			compData = f.read()
			f.close()
			os.remove(compressedFileName)
			if len(compData) >= srcFileLen: #bad results, do not compress
				f = open(srcFileName, "rb")
				compData = f.read()
				f.close()
				compType = 0

		if compData is None:
			noesis.doException("Failed to compress a file while generating the archive.")
		padCompLen = len(compData)
		if padCompLen & 15:
			padCompLen = (16-(padCompLen & 15))
		arcFile.write(noePack("<iiii", srcFileLen, len(compData), len(compData)+padCompLen, compType))
		arcFile.write(compData)
		arcFile.write(bytearray([0])*padCompLen)

	arcFile.seek(12)
	arcFile.write(noePack("<i", numFiles))
	arcFile.close()	
	noesis.freeModule(noeMod)
	print("Generated archive. (compression type is " + repr(COMPRESS_TYPE) + ")")
	return 0

def makeArcToolMethod(toolIndex):
	srcDir = noesis.userPrompt(noesis.NOEUSERVAL_FOLDERPATH, "Open Folder", "Select a folder to archive.", noesis.getSelectedDirectory(), validateInput)
	if srcDir is None:
		return 0

	dstDefault = srcDir + "_archive.testarc"
	dstName = noesis.userPrompt(noesis.NOEUSERVAL_SAVEFILEPATH, "Save File", "Select destination path for the archive file.", dstDefault, None)
	if dstName is None:
		return 0

	return makeArc(srcDir, dstName)
