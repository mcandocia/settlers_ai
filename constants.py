from collections import OrderedDict
from collections import defaultdict 
import numpy as np
from copy import copy, deepcopy

class dotdict(dict):
    def __getattr__(self, name):
    	if  name  in  ['__deepcopy__','__copy__']:
    		return dict(self).__getattr__(name)
        return self[name]

DEBUG = False

#data structures that will help organize the rest of the files

TILE_TYPES = ['forest','fields','pasture','mountains','hills','desert']
TILE_TYPES_INDEXES = {k:i for i, k in enumerate(TILE_TYPES)}
TILE_COUNTS = {'forest':4, 'fields':4, 'pasture':4,'mountains':3,'hills':3,'desert':1}


TILE_RESOURCES = {'forest':'wood','fields':'grain','sheep':'wool','mountains':'ore','hills':'brick','desert':None}
RESOURCES_UNIQUE = ['wood','grain','wool','ore','brick']
RESOURCES_UNIQUE_HIDDEN = ['wood','grain','wool','ore','brick','unknown']

DEVELOPMENT_CARDS = ['knight','victory','monopoly','road_building','year_of_plenty']
DEVELOPMENT_CARD_COUNT = {'knight':14, 'monopoly':2, 'road_building':2, 'year_of_plenty':2, 'victory':5}
#useful for shuffling
DEVELOPMENT_CARD_VALUES = reduce(list.__add__, [[k for _ in range(v)] 
	for k, v in DEVELOPMENT_CARD_COUNT.iteritems()])
#used for indexing purposes
DEVELOPMENT_CARD_UNIQUE = DEVELOPMENT_CARD_COUNT.values()
DEVELOPMENT_CARD_UNIQUE.sort()
DEVELOPMENT_CARD_UNIQUE_INDEX = {k:v for v, k in enumerate(DEVELOPMENT_CARD_UNIQUE)}

#used to track played cards
DEVELOPMENT_CARD_SPECIAL_INDEX = {'monopoly':0,'year_of_plenty':1,'road_building':2}

#[0] represents desert, which has no roll value
DICE_ROLL_TOKENS = [0] + range(2,13)
DICE_ROLL_TOKEN_COUNT = {x:2 - (x in [0, 2, 12]) for x in [0] + range(2, 13)}
DICE_ROLL_TOKEN_INDEXES = {k:i for i, k in enumerate(DICE_ROLL_TOKENS)}

HARBOR_PIECES = ['wool','wood','brick','ore','grain','generic']
HARBOR_INDEXES = {k:v for v, k in enumerate(HARBOR_PIECES)}

HARBOR_PIECES_COUNTS = {x:(1+(x=='generic')) for x in HARBOR_PIECES}

DEVELOPMENT_CARD_COST = {'grain':1,'wool':1,'ore':1,'wood':0,'brick':0}
ROAD_COST = {'wood':1,'brick':1,'grain':0,'wool':0,'ore':0}
SETTLEMENT_COST = {'wood':1,'brick':1,'grain':1,'wool':1,'ore':0}
CITY_COST = {'wood':0,'brick':0,'grain':2,'ore':3,'wool':0}


#let's define a coordinate system


#axial 

"""
	   ( 0,-2)( 1,-2)( 2,-2)
	(-1,-1)( 0,-1)( 1,-1)( 2,-1)
(-2, 0)(-1, 0)( 0, 0)( 1, 0)( 2, 0)
	(-2, 1)(-1, 1)( 0, 1)( 1, 1)
		(-2, 2)(-1, 2)( 0, 2)

adjacency rules:

c[1] is row, so any tile with the same c[1] and +/-1 c[0] is adjacent
c[0] is down-rightward diagonal, so any tile with the same c[0] and +/ c[1] is adjacent
if c[0] + c[1] is the same and c1[0] - c2[0] = c2[1] - c1[1], they are adjacent

calculating edge and vertex position:

edge coordinates are the average of two hex cells

vertex coordinates are the average of three hex cells
"""

#hardcoded index

"""

cells:

    00  01  02
  03  04  05  06
07  08  09  10  11
  12  13  14  15
    16  17  18

edges:

          00  01  02  03  04  05
        06      07      08      09
      10  11  12  13  14  15  16  17
    18      19      20      21      22
  23  24  25  26  27  28  29  30  31  32
33      34      35      36      37      38
  39  40  41  42  43  44  45  46  47  48
    49      50      51      52      53
      54  55  56  57  58  59  60  61
        62      63      64      65
          66  67  68  69  70  71

vertices:

        00  01  02  03  04  05  06
    07  08  09  10  11  12  13  14  15  
16  17  18  19  20  21  22  23  24  25  26  
27  28  29  30  31  32  33  34  35  36  37  
    38  39  40  41  42  43  44  45  46  
        47  48  49  50  51  52  53   

"""



cell_edges = {
	0:(0,1,7,12,11,6),
	1:(2,3,8,14,13,7),
	2:(4,5,9,16,15,8),
	3:(10,11,19,25,24,18),
	4:(12,13,20,27,26,19),
	5:(14,15,21,29,28,20),
	6:(16,17,22,31,30,21),
	7:(23,24,34,40,39,33),
	8:(25,26,35,42,41,34),
	9:(27,28,36,44,43,35),
	10:(29,30,37,46,45,36),
	11:(31,32,38,48,47,37),
	12:(40,41,50,55,54,49),
	13:(42,43,51,57,56,50),
	14:(44,45,52,59,58,51),
	15:(46,47,53,61,60,52),
	16:(55,56,63,67,66,62),
	17:(57,58,64,69,68,63),
	18:(59,60,65,71,70,64)
	}

cell_vertices = {
	0:(0,1,2,10,9,8),
	1:(2,3,4,12,11,10),
	2:(4,5,6,14,13,12),
	3:(7,8,9,19,18,17),
	4:(9,10,11,21,20,19),
	5:(11,12,13,23,22,21),
	6:(13,14,15,25,24,23),
	7:(16,17,18,29,28,27),
	8:(18,19,20,31,30,29),
	9:(20,21,22,33,32,31),
	10:(22,23,24,35,34,33),
	11:(24,25,26,37,36,35),
	12:(28,29,30,40, 39, 38),
	13:(30,31,32,42,41,40),
	14:(32,33,34,44,43,42),
	15:(34,35,36,46,45,44),
	16:(39,40,41,49,48,47),
	17:(41,42,43,51,50,49),
	18:(43,44,45,53,52,51)
}

edge_vertices = {}
#use cell_edges and cell_vertices to construct this

cell_inconsistencies = False
for i in range(19):
	vertices = cell_vertices[i]
	edges = cell_edges[i]
	current_dict = {}
	for j in range(6):
		current_vertex_pair = frozenset( (vertices[j], vertices[ (j + 1) % 6]) )
		current_edge = edges[j] 
		if current_edge in edge_vertices:
			if edge_vertices[current_edge] <> current_vertex_pair:
				cell_inconsistences = True 
				print 'cell vertices %s' % str(cell_vertices[current_edge])
				print 'current vertex pair %s' % str(current_vertex_pair)
				print 'current edge: %s' % str(current_edge)
				print 'CELL INCONSISTENCY!'
				exit()
		edge_vertices[current_edge] = current_vertex_pair

if DEBUG:
	print 'EDGE VERTICES: '
	print edge_vertices

#calculate connected edges...
#inefficient for large maps, but easy for small ones
CONNECTED_EDGES = defaultdict(set)
for edge, vertex_set in edge_vertices.iteritems():
	for vertex in vertex_set:
		for edge2, vertex_set2 in edge_vertices.iteritems():
			if edge==edge2:
				continue
			if vertex in vertex_set2:
				CONNECTED_EDGES[edge].add(edge2)
if DEBUG: 
	print 'CONNECTED EDGES:'
	print CONNECTED_EDGES

#make templates
DEFAULT_TILE_TEMPLATE = {
	0:'forest',
	1:'pasture',
	2:'fields',
	3:'hills',
	4:'mountains',
	5:'hills',
	6:'pasture',
	7:'desert',
	8:'forest',
	9:'fields',
	10:'forest',
	11:'fields',
	12:'hills',
	13:'pasture',
	14:'pasture',
	15:'mountains',
	16:'mountains',
	17:'fields',
	18:'forest',
}

DEFAULT_TILE_VALUES = DEFAULT_TILE_TEMPLATE.values()

DEFAULT_HARBOR_TEMPLATE = {
	0:'generic',
	3:'wool',
	17:'generic',
	18:'ore',
	38:'generic',
	49:'grain',
	61:'brick',
	66:'generic',
	69:'wood',
}

DEFAULT_HARBOR_VALUES = DEFAULT_HARBOR_TEMPLATE.values()

N_HARBORS = len(DEFAULT_HARBOR_VALUES)

DEFAULT_ROLL_TEMPLATE = {
	0:11,
	1:12,
	2:9,
	3:4,
	4:6,
	5:5,
	6:10,
	7:0,#desert
	8:3,
	9:11,
	10:4,
	11:8,
	12:8,
	13:10,
	14:9,
	15:3,
	16:5,
	17:2,
	18:6
}

DEFAULT_INVERSE_ROLL_TEMPLATE = {}
for k, v in DEFAULT_ROLL_TEMPLATE.iteritems():
	if v not in DEFAULT_INVERSE_ROLL_TEMPLATE:
		DEFAULT_INVERSE_ROLL_TEMPLATE[v] = [k]
	else:
		DEFAULT_INVERSE_ROLL_TEMPLATE[v].append(k)

DEFAULT_ROLL_VALUES = DEFAULT_ROLL_TEMPLATE.values()

#restrictions to values
POSSIBLE_HARBOR_LOCATIONS = [
0,1,2,3,4,5,
6,9,
10,17,
18,22,
23,32,
33,38,
39,48,
49,53,
54,61,
62,65,
66,67,68,69,70,71]

POSSIBLE_HARBOR_LOCATIONS_INDEX = {k:v for v, k in enumerate(POSSBILE_HARBOR_LOCATIONS)}


#generation functions
def generate_random_tiles():
	values = copy(DEFAULT_TILE_VALUES)
	np.random.shuffle(values)
	return {i:v for i, v in enumerate(values)}

def generate_random_harbors():
	values = copy(DEFAULT_HARBOR_VALUES)
	np.random.shuffle(values)
	locations = copy(POSSIBLE_HARBOR_LOCATIONS)
	np.random.shuffle(locations)
	locations = locations[:N_HARBORS]
	return {l:v for l, v in zip(locations, values)}

def generate_random_roll(tiles):
	"""
	returns both a regular template and an inverted template
	so dice roll numbers return what tiles are selected
	"""
	keys, vals = tiles.keys(), tiles.values()
	keys.pop(vals.index('desert'))
	values = [x for x in DEFAULT_ROLL_VALUES if x <> 0]
	np.random.shuffle(values)
	template =  {k:v for k, v in zip(keys, values)}
	inverse_template = {}
	for k, v in template.iteritems():
		if v not in inverse_template:
			inverse_template[v] = [k]
		else:
			inverse_template[v].append(k)
	return template, inverse_template 


class HexMap(object):
	def __init__(self, 
		tile_template=DEFAULT_TILE_TEMPLATE, 
		roll_template=DEFAULT_ROLL_TEMPLATE, 
		roll_inverse_template=DEFAULT_INVERSE_ROLL_TEMPLATE,
		harbor_template=DEFAULT_HARBOR_TEMPLATE):
		if tile_template is None:
			tile_template=generate_random_tiles()
		if roll_template is None or roll_inverse_template is None:
			roll_template, roll_inverse_template = generate_random_roll(tile_template)
		if harbor_template is None:
			harbor_template = generate_random_harbors()

		self.tiles = copy(tile_template)
		self.rolls = copy(roll_template)
		self.inverse_rolls = copy(roll_inverse_template)
		self.harbors = copy(harbor_template)
		#this value can change
		self.robber_location = self.tiles.keys()[self.tiles.values().index('desert')]

	def __str__(self):
		selfvars = [x for x in dir(self) if x[0] <> '_']
		return '<->' + '\n\n<->'.join([varname + ': ' + str(getattr(self, varname)) 
			for varname in selfvars])

	def reset(self):
		self.robber_location = self.tiles.keys()[self.tiles.values().index('desert')]

	def get_self_serialization(self):
		"""
		returns the board state initially calculated at the beginning of the game, 
		plus the following vector:

		ROBBER LOCATION: 
		index = tile index of robber
		total_dim = 19
		"""
		V_robber = np.zeros(19)
		V_robber[self.robber_location] = 1 
		return np.append(self.serialization, V_robber)

	def get_self_serialization_with_moved_robber(self, robber_location):
		"""
		used for making predictions when the robber is to be moved...
		"""
		return np.append(self.serialization, robber_location)

	def serialize_self(self):
		"""
		returns the board configuration as described by class variables:
		
		TILE TYPES:
		index = tile_index * 6 + tile_type_index
		total_dim = 19*6 + 5 = 119

		ROLL VALUES:
		index = tile_index * 12 + 11 
		total_dim = 19*12 + 11 = 239

		HARBORS:
		index = possible_harbor_edge_index * 6 + 5
		total_dim = 30*6 + 5 = 185

		

		"""
		V_tile_types = np.zeros(113)
		V_roll_values = np.zeros(227)
		V_harbors = np.zeros(185)
		for tile_index, tile_type in self.tile_template.iteritems():
			V_tile_types[tile_index*6 + TILE_TYPES_INDEXES[tile_type]] = 1

		for tile_index, roll_value in self.roll_template.iteritems():
			V_roll_values[tile_index*12 + DICE_ROLL_TOKEN_INDEXES[roll_value]] = 1

		for edge_index, harbor_type in self.harbor_template.iteritems():
			V_harbors[POSSIBLE_HARBOR_LOCATIONS_INDEX[edge_index]]*6 + HARBOR_INDEXES[harbory_type]

		self.serialization = reduce(np.append([V_tile_types, V_roll_values, V_harbors]))

#a few vectors used for modifying slices of player numpy arrays when forecasting

#still considering if this is good approach
PLAYER_INTERNAL_MODIFICATION_VECTORS = {
	'resource_modifications':range(5),
	'development_card_modifications':None
}