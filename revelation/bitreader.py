"""
== Overview ==
BitReader is a small Python utility library for reading bits from bytes by
specifying the structure of data with JSON compatible syntax to avoid the
unreadable mess of bitwise operations. Little & big endian data supported.

Licensed under MIT license.

=== Simple example ===
{{{
#!python
from bitreader import BitReader, bytes2str, str2bytes

# A specification defines names of variables and how many bits they need
spec    = ['test1', 12, 'test2', 4]

reader = BitReader(spec)
result = reader.read([0xfe, 0xda]) # Or just reader.read(0xFEDA)

# The result contains the variables as attributes
hex(result.test1)
> '0xfed'

hex(result.test2)
> '0xa'

# And you can convert the result back to binary format
result.dump()
> array('B', [254, 218])

}}}

This can be used to read static data, but very often the data is dynamic or we
need to read a list of data elements. That can be done with subspecification.

=== Subspecification ===

{{{
#!python
# Dynamic data or arrays can be read with subspecification
# described with a dict.
spec   = [
    'length', 8,
    # 'sizeby' is used to set the field which tells the length
    # of the string we are reading. We could also hard code the size
    # with 'size' key instead of 'sizeby'. 'size' tells the length
    # of the data and data defined in 'spec' is read until the given
    # size is exceeded or matched. Hopefully matched. There's also
    # 'count' and 'countby' which can be used to read the data
    # exactly the given times. Here, we could use either one.
    'data',{
        'sizeby' : 'length',
        'spec'   : ['char',8]
    }
]
reader = BitReader(spec)

# Create test data
text   = "Hello World!"
data   = [len(text)] + str2bytes(text)

# Read the data to BitData object
bitdata = reader.read(data)
# The text is stored in bitdata.data as list of BitData objects
# Each BitData object has char attribute holding a single
# character. We need to join them together to form the string.
print bytes2str(bitdata.data, attribute="char")
> 'Hello World!'

}}}

"""

__author__ = "Jussi Toivola<jtoivola@gmail.com>"
__license__ = "MIT"

from array import array

# Utility functions to easily mark data length to common lengths
# instead of using bit values
def B4(b): return b * 4
def B8(b): return b * 8
def B16(b): return b * 16
def B32(b): return b * 32
def B64(b): return b * 64

NIBBLE = B4(1)
BYTE   = B8(1)
SHORT  = B16(1)
INT    = B32(1)
LONG   = B64(1)

#: Utility for converting string to list of bytes
def str2bytes(text):
    return map(ord,text)

#: Utility for converting list of bytes or BitData objects to string
#: To convert list of BitData objects, set the attribute parameter to
#: the field holding the byte to convert
def bytes2str(bytes, attribute=None):
    if attribute is None:
        bytes = map(chr,bytes)
    else:
        bytes = [chr(getattr(x, attribute)) for x in bytes]
    return "".join(bytes)

class BitSpec:
    #: When using subspec, this is the keyword to set the spec to dict
    spec = "spec"
    
    #: Can be used to hard code the size of the specification 
    size = "size"
    #: Can be used to multiply size
    count = "count"
    #: Used to refer to another field in the (super)specification,
    #: which determines the size of the subspecification(eg. string array)
    sizeby = "sizeby"
    #: Same as sizeby but for count
    countby = "countby"
    
class BitData(object):
    def __init__(self, spec, little_endian = True ):
        self.spec  = spec
        self.little_endian = little_endian
        
    def add(self, name, value):
        # This is faster than setattr
        self.__dict__[name] = value
    
    def asdict(self):
        d = {}
        specindex = -1
        name = ""
        for s in self.spec:
            specindex += 1
            if specindex % 2:
                d[name] = getattr(self, name)
            else:
                name = s
        return d
    
    def dump(self):
        """ Serialize the data back into byte format.
        
        @return: An array of unsigned bytes based on 
                 the attributes of this object and given specification.
        @rtype: array.array
        """
        curbyte    = 0
        bitsinbyte = 0
        result     = array('B')
        spec = self.spec
        name = None
        specindex = -1
        for s in spec:
            specindex += 1
            if specindex % 2:
                data = getattr(self, name)
                bits = s
                
                # Handle subspecification
                if type(bits) is dict:
                    if type(data) is list:
                        for x in data:
                            if type(x) is int:
                                result.append(x)
                            else:
                                result.extend(x.dump())
                    continue
                
                bitsinbyte += bits
                
                # Check that the data doesn't take more bits than it should
                if data >> bits:                    
                    raise OverflowError("Data takes more space than defined in the specification. Name:%s bits:%d data:0x%X" % ( name, bits, data) )
                
                curbyte = curbyte << bits | data
                while bitsinbyte >= 8:
                    bitsinbyte -= 8
                    
                    if self.little_endian:
                        byte = curbyte & 0xFF
                        curbyte >>= 8
                    else:
                        byte = curbyte >> bitsinbyte
                        curbyte ^= ( byte << bitsinbyte)
                        
                    result.append(byte)
                    
            else:
                name = s
        
        # Add the last byte
        if(curbyte):
            result.append(curbyte)
           
        return result
        
class BitReader(object):
    """
    Utility for reading bits from list of bytes.
    
    Reading simple data:
    >>> spec   = ['test1', 12, 'test2', 4]
    >>> reader = BitReader(spec)
    >>> result = reader.read([0xfe, 0xda])
    >>> hex(result.test1)
    '0xfed'
    >>> hex(result.test2)
    '0xa'
    >>> result.dump()
    array('B', [254, 218])
    
    Using subspecs:
    >>> spec   = ['length', 8, 'data',{'sizeby' : 'length', 'spec' : ['char',8]}]
    >>> reader = BitReader(spec)
    >>> text   = "Hello World!"
    >>> data   = [len(text)] + map(ord,text)
    >>> result = reader.read(data)
    >>> "".join( [ chr(x.char) for x in result.data])
    'Hello World!'
    
    Note that subspecification data is stored as list of BitData objects
    on the data attribute.
    
    """
    
    LITTLE_ENDIAN = "little"
    BIG_ENDIAN    = "big"
    #: Endianess constants are the same that sys.byteorder returns.
    #: To set the default endianess to system's do:
    #:  BitReader.DEFAULT_ENDIAN = sys.byteorder
    DEFAULT_ENDIAN = BIG_ENDIAN
    
    def __init__(self, spec, endianess = None, little_endian = None ):
        if endianess is None:
            endianess = BitReader.DEFAULT_ENDIAN
        if little_endian is None:
            little_endian = (endianess == BitReader.LITTLE_ENDIAN)
        
        self.spec   = spec
        self.endianess = endianess
        self.little_endian = little_endian
        self.result = BitData(spec, self.little_endian)
        #: The unused bits from the last byte
        self.unusedbits = 0
        #: How many bytes were read
        self.bytesused = 0
        self.bitsinbytes = 0
        
    def read(self, data):
        """ Map values in data to a variables defined in the specification.
        """
        
        spec  = self.spec
        little_endian = self.little_endian
        # Tells how many bits of data we have. Each byte adds 8 bits.
        # When a value is read, it's bit count is reduced from this.
        # Tells us if we need to read more data for the next value.
        bitsinbytes = self.bitsinbytes 
        databuffer  = self.unusedbits
        currentindex = 0
        
        # The amount of bits required for current variable defined in the spec.
        varbits  = -1
        
        self.data = data        
        
        iterator = None
        
        # If an integer was given, convert it to byte array
        t = type(data)
        if t is int:
            self.data = array("B")
            remaining = -1
            while data:
                b = data & 0xFF
                self.data.append(b)
                data = data >> 8
            # Usually when giving integer, we want the first byte
            # to be found at the first value in spec.
            # eg. int 0xABCD with spec ['first',8,'second',8]
            # 'first' should have value 0xAB
            # We need to reverse the array to have it this way
            # But this might cause confusion with little endian data
            # where the data would be mapped 0xCDAB in memory
            # But if one reads the data and converts it into short
            # integer, it should be expected that using the same
            # value results in same results.
            # eg. giving [0xAB,0xCD] or 0xABCD must have the 
            # same result.
            self.data.reverse()
            # Integer as data is always read as big endian
            little_endian = False
        else:
            self.data = data        

        # Covers list,tuple and iterator types
        # Removes the need for type checking here.
        iterator = iter(self.data)
        
        name   = None
        isbits = True
        for varbits in spec:   
            # Element in spec defines either bits or the name         
            isbits = not isbits
            if isbits:                
                
                # Handle subspecification
                if type(varbits) is dict:
                    count = -1
                    size  = 0
                    
                    if "count" in varbits:
                        count = varbits["count"]
                    elif "countby" in varbits:
                        count = getattr(self.result,varbits["countby"])
                    elif "sizeby" in varbits:
                        size  = getattr(self.result,varbits["sizeby"])
                    elif "size" in varbits:
                        size  = varbits["size"]
                    
                    subspec = varbits["spec"]
                    subresult = []
                    
                    end = currentindex + size
                    while count > 0 or (currentindex < end):
                        
                        #print "Creating sub bitreader"
                        #print "with databuffer",databuffer,hex(databuffer)
                        #print "with bitsinbytes",bitsinbytes,hex(bitsinbytes)
                        br = BitReader(subspec, endianess = self.endianess)
                        br.unusedbits  = databuffer
                        br.bitsinbytes = bitsinbytes
                    
                        d = self.data[currentindex:]

                        sr  = br.read(d)
                        subresult.append(sr)
                        
                        databuffer  = br.unusedbits
                        bitsinbytes = br.bitsinbytes
                        # Consume the data that was used by subspec
                        currentindex += br.bytesused
                        count -= 1
                    
                    iterator = iter(self.data[currentindex:])
                    self.result.add(name, subresult)
                    continue
                
                # Read enough data to buffer
                while varbits > bitsinbytes:
                    #print varbits,bitsinbytes,varbits > bitsinbytes
                    # 400001 function calls in 37.130 CPU seconds
                    #databuffer   = ( databuffer << 8 ) | data[bufferindex]
                    #bufferindex += 1
                    
                    # 400001 function calls in 39.261 CPU seconds
                    # using iterator interface is slightly slower than indexing,
                    # but it gives more options on how to supply
                    # the data(eg. stream)
                    # TODO: Expecting all data to have BYTE size
                    #       need temporary value and detect when more 
                    #       data is needed.

                    # Need to reverse byte order if little endian
                    if little_endian:
                        databuffer   =  (iterator.__next__() << bitsinbytes) | databuffer
                    else:
                        databuffer   = ( databuffer << 8 ) | iterator.__next__()
                    currentindex += 1
                    bitsinbytes += 8

                shift = ( bitsinbytes - ( varbits ) )
                if shift >= 0:
                    value = databuffer >> shift
                else:
                    value = databuffer
                    self.result.add(name, value)
                    break
                
                self.result.add(name, value)
                
                # 400001 function calls in 37.630 CPU seconds
                #databuffer &= MASK_CACHE[( bitsinbytes - ( varbits ) )]
                
                # 400001 function calls in 37.130 CPU seconds
                # Speed difference is marginal, while this allows
                # dynamic mask not limited by mask list.
                databuffer  ^= ( value << shift)
                bitsinbytes -= varbits
                
            else:
                name = varbits
        
        self.bitsinbytes = bitsinbytes
        self.unusedbits = databuffer
        self.bytesused  = currentindex
        
        return self.result

if __name__ == '__main__':
    import doctest
    doctest.testmod()