#include <math.h>
#include <float.h>

typedef double polyReal_t;
typedef unsigned short mUShort_t;


class LocalMemPool
{
private:
	typedef size_t poolSize_t;
	typedef struct singlePool_s
	{
		poolSize_t			size;
		poolSize_t			ptr;
		unsigned char		*mem;
		singlePool_s		*next;
	} singlePool_t;
public:
	LocalMemPool(poolSize_t poolSize = 1048576)
	{
		m_pools = NULL;
		m_poolDefault = poolSize;
		m_memAlloc = malloc;
		m_memFree = free;
	}
	~LocalMemPool()
	{
		singlePool_t *p = m_pools;
		while (p)
		{
			singlePool_t *n = p->next;
			m_memFree(p);
			p = n;
		}
	}

	void *Alloc(poolSize_t size)
	{
		for (singlePool_t *p = m_pools; p; p = p->next)
		{
			if (p->ptr+size <= p->size)
			{
				void *r = p->mem+p->ptr;
				p->ptr += size;
				return r;
			}
		}
		const poolSize_t allocSize = (size > m_poolDefault) ? size : m_poolDefault;
		singlePool_t *newPool = (singlePool_t *)m_memAlloc(sizeof(singlePool_t) + allocSize);
		memset(newPool, 0, sizeof(singlePool_t));
		newPool->mem = (unsigned char *)(newPool+1);
		newPool->size = allocSize;
		newPool->next = m_pools;
		m_pools = newPool;
		newPool->ptr += size;

		return newPool->mem;
	}

private:
	singlePool_t		*m_pools;
	poolSize_t			m_poolDefault;
	void				*(*m_memAlloc)(poolSize_t size);
	void				(*m_memFree)(void *ptr);
};

//cheap resource hashing system using doom's 8-character resource names
class DoomResHash
{
public:
	DoomResHash(const int hashSize = 131072, const int poolSize = 131072)
		: m_pool(poolSize)
	{
		m_numBuckets = hashSize;
		m_buckets = (hashBucket_t *)m_pool.Alloc(sizeof(hashBucket_t)*m_numBuckets);
		memset(m_buckets, 0, sizeof(hashBucket_t)*m_numBuckets);
	}

	void AddResource(const char *id, const int resIndex)
	{
		const unsigned int bucketIndex = BucketForId(id);
		hashBucket_t *bucket = m_buckets+bucketIndex;

		//we just assume the resource isn't already in the hash
		hashEntry_t *newEntry = (hashEntry_t *)m_pool.Alloc(sizeof(hashEntry_t));
		memset(newEntry, 0, sizeof(hashEntry_t));
		memcpy(newEntry->id, id, 8);
		newEntry->resIndex = resIndex;
		newEntry->next = bucket->entries;

		bucket->entries = newEntry;
	}

	int GetResourceIndexForId(const char *id)
	{
		const unsigned int bucketIndex = BucketForId(id);
		hashBucket_t *bucket = m_buckets+bucketIndex;
		for (hashEntry_t *entry = bucket->entries; entry; entry = entry->next)
		{
			for (int i = 0; i < 8; i++)
			{
				//crappiness shoehorned after the fact upon noticing that capitalization in pnames and in
				//texture headers doesn't necessarily match.
				if (tolower(entry->id[i]) != tolower(id[i]))
				{
					return -1;
				}
				if (!entry->id)
				{
					break;
				}
			}
			return entry->resIndex;
		}
		return -1;
	}

private:
	unsigned int BucketForId(const char *id)
	{
		unsigned int hash = 2166136261;
		for (int i = 0; i < 8; i++)
		{
			if (!id[i])
			{
				break;
			}
			hash = (hash^tolower(id[i])) * 16777619;
		}
		return (hash%m_numBuckets);
	}

	typedef struct hashEntry_s
	{
		char			id[8];
		int				resIndex;
		hashEntry_s		*next;
	} hashEntry_t;
	typedef struct hashBucket_s
	{
		hashEntry_t		*entries;
		int				numEntries;
	} hashBucket_t;

	hashBucket_t		*m_buckets;
	int					m_numBuckets;

	LocalMemPool		m_pool;
};

typedef struct doomMapRes_s
{
	DoomResHash						wallTexHash;
	DoomResHash						flatsHash;
	CArrayList<noesisTex_t *>		noeTextures;
	CArrayList<noesisMaterial_t *>	noeMaterials;
	noesisMatData_t					*noeMatData;
} doomMapRes_t;

typedef struct wadHdr_s
{
	BYTE			id[4]; //"PWAD"/"IWAD"
	int				numLumps;
	int				lumpsOfs;
} wadHdr_t;
typedef struct wadLump_s
{
	int				ofs;
	int				size;
	char			name[8];
} wadLump_t;
typedef struct memLump_s
{
	wadLump_t		*l;
	int				lIdx;
	wadHdr_t		*base;
} memLump_t;

typedef struct wadPatchHdr_s
{
	short			width;
	short			height;
	short			leftOfs;
	short			topOfs;
} wadPatchHdr_t;

typedef struct wadPatchData_s
{
	int				size;
	BYTE			*data;
} wadPatchData_t;

typedef struct wadTexPatch_s
{
	short			originX;
	short			originY;
	unsigned short	patchIndex;
	unsigned short	stepDir;
	unsigned short	colorMap;
} wadTexPatch_t;

typedef struct wadTexHdr_s
{
	char			name[8];
	unsigned int	masked; //?
	unsigned short	width;
	unsigned short	height;
	unsigned int	columnDir; //?
	unsigned short	patchCount;
	wadTexPatch_t	patches[1];
} wadTexHdr_t;

typedef struct mapLineDef_s
{
	mUShort_t		startVert;
	mUShort_t		endVert;
	mUShort_t		flags;
	mUShort_t		specialType;
	mUShort_t		sectorTag;
	mUShort_t		rightSideDef;
	mUShort_t		leftSideDef;
} mapLineDef_t;
typedef struct mapSideDef_s
{
	short			xOfs;
	short			yOfs;
	char			upperTex[8];
	char			lowerTex[8];
	char			middleTex[8];
	mUShort_t		sectorNum;
} mapSideDef_t;
typedef struct mapVert_s
{
	short			pos[2];
} mapVert_t;
typedef struct mapSector_s
{
	short			floorHeight;
	short			ceilingHeight;
	char			floorTex[8];
	char			ceilingTex[8];
	mUShort_t		lightLevel;
	mUShort_t		type;
	mUShort_t		tagNum;
} mapSector_t;
typedef struct mapSubSector_s
{
	mUShort_t		segNum;
	mUShort_t		firstSeg;
} mapSubSector_t;
typedef struct mapSeg_s
{
	mUShort_t		firstVert;
	mUShort_t		endVert;
	mUShort_t		ang;
	mUShort_t		lineDef;
	mUShort_t		dir;
	mUShort_t		dist;
} mapSeg_t;
typedef struct mapNode_s
{
	short			partLine[2];
	short			partLineLen[2];
	short			childBoxes[2][4];
	mUShort_t		children[2];
} mapNode_t;

typedef struct polyPoint_s
{
	polyReal_t			p[2];
} polyPoint_t;
typedef struct polyEdge_s
{
	int					idx[2];
} polyEdge_t;
typedef struct extraNodeData_s
{
	int				parentIndex;
} extraNodeData_t;
typedef struct extraSubSectData_s
{
	int				nodeParent;
	int				sectorIndex;

	polyPoint_t		*convexPoints;
	int				numPoints;
} extraSubSectData_t;

typedef struct segChopLine_s
{
	polyReal_t		pos[2];
	polyReal_t		length[2];
} segChopLine_t;

typedef struct convexMapPoly_s
{
	polyPoint_t			*points;
	int					numPoints;
	int					numPointsAlloc;

	polyEdge_t			*edges;
	int					numEdges;
	int					numEdgesAlloc;
} convexMapPoly_t;

typedef struct wadOpts_s
{
	polyReal_t			collapseEdges;
	polyReal_t			weldVerts;
	polyReal_t			minSecCutDist;
} wadOpts_t;
extern wadOpts_t *g_opts;
