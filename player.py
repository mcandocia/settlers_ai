0from constants import edge_vertices, cell_vertices, cell_edges
from constants import CONNECTED_EDGES
from copy import copy 
import numpy as np 

from constants import dotdict
from constants import DEVELOPMENT_CARD_UNIQUE
from constants import * 

#TODO: continue working on hidden player serialization

class Player(object):
	def __init__(self, order, id, game, ai=None):
		self.order = order 
		self.id = id 

		#initialize cities and roads (data structure only)
		#which vertices cities or settlements are built on
		#sets are used for faster constraint-checking
		self.vertices = set()
		self.cities = set()
		self.settlements = set()
		#which edges roads are built on
		self.edges = set() 
		self.game = game 

		#resources
		self.resources = dotdict({
		'grain':0,
		'wood':0,
		'wool':0,
		'ore':0,
		'brick':0
		})
		self.hand_size = 0
		#may be played on your turn
		self.development_cards_ready = dotdict({
		'knight':0,
		'victory':0,
		'monopoly':0,
		'road_building':0,
		'year_of_plenty':0,
		})
		#knight has its own category
		self.development_cards_played = dotdict({
		'monopoly':0,
		'road_building':0,
		'year_of_plenty':0,
		})
		#not available for use until next turn
		self.development_cards_recent = copy(self.development_cards_ready)
		self.n_recent_development = 0
		self.n_ready_development = 0
		#record number of ready cards per turn 
		self.n_ready_development_history = [0 for _ in range(5)]
		#numeric attributes
		self.knights = 0
		self.longest_path = 0
		self.visible_points = 0
		self.actual_points = 0
		#only used at end of game
		self.win = 0
		#used whenever anything changes so that serializer knows when to update
		self.changed = False
		self.serialized_self = None 
		self.initialize_other_player_data()

	def sum_of_resources(self):
		total = 0
		for k, v in self.resources.iteritems():
			total+=v 
		return total 

	def construct_tradeables(self, player):
		"""
		creates a list of possible (or thought-out trades) with other players
		sensible restrictions:
		* will not assume identity of more than 1 random resource
		* will not trade more than 3 of any 1 resource 
		* will not trade more than 5 resources on either side
		* will not contain same resources on either side
		* will not request resources for which player has 4 or more 
		"""
		#
		if self.sum_of_resources()==0:
			return []
		if player.sum_of_resources()==0:
			return [] 
		#next
		r1 = self.resources 
		r2 = self.other_player_resources[(player.order - self.order % 4)]

		offerings = []
		requests = [] 
		unknown_resource = r2['unknown'] > 0
		#make offerings #grain; wood; wool; ore; brick
		for grain_amount in range(min(r1.grain+1, 3)):
			for wood_amount in range(min(3, r1.wood+1)):
				for wool_amount in range(min(3, r1.wool+1)):
					for ore_amount in range(min(3, r1.ore+1)):
						for brick_amount in range(min(3, r1.brick+1)):
							if grain_amount+wood_amount+wool_amount+ore_amount+brick_amount > 5:
								continue 
							offerings.append([grain_amount, wood_amount, wool_amount, ore_amount, brick_amount])

		#make requests
		for grain_amount in range(min(r1.grain+1+unknown_resource, 3)):
			for wood_amount in range(min(3, r1.wood+1+unknown_resource)):
				for wool_amount in range(min(3, r1.wool+1+unknown_resource)):
					for ore_amount in range(min(3, r1.ore+1+unknown_resource)):
						for brick_amount in range(min(3, r1.brick+1+unknown_resource)):
							if grain_amount+wood_amount+wool_amount+ore_amount+brick_amount > 5:
								continue 
							requests.append([grain_amount, wood_amount, wool_amount, ore_amount, brick_amount])

		potential_trades = offerings_requests_cartesian_filter(offerings, requests)
		return potential_trades 

	def filter_trades(self, potential_trades):
		possible_trades = []
		for trade in potential_trades:
			if has_resource_list(trade[1]):
				possible_trades.append(trade)
		return possible_trades 

	def has_resources_list(self, request):
		"""
		checks to see if player has resources given a  list in a specific order;
		needs to be updated if resources are updated
		"""
		r = self.resources 
		if r.grain < request[0]:
			return False 
		elif r.wood < request[1]:
			return False 
		elif r.wool < request[2]:
			return False 
		elif r.ore < request[3]:
			return False 
		elif r.brick < request[4]:
			return False 
		return True 

	def has_resources(self, resource_list):
		"""
		checks to see if player has resources given dotdict
		"""
		for resource, value in resource_list.iteritems():
			if self.resources[resource] < value:
				return False 
		return True 

	def account_for_hand_discrepancies(self):
		"""
		adjusts knowledge of other players based on card counts and other information
		"""
		print 'account_for_hand_discrepancies not yet implemented!'

	def initialize_other_player_data(self):
		"""
		call this after game has been created and players are attached, but
		before the game has actually started

		secret information:
		player resources
		player unknown resources
		player number of recent 

		your resources, known/unknown to other players
		"""
		game_players = self.game.players
		self.other_players = [game_players[i % 4] for i in range(self.order, self.order+4)]
		#these data structures are technically duplicated elsewhere, because this hidden information
		#is always known among the two relevant parties
		self.other_player_resources = [dotdict({k:0 for k in RESOURCES_UNIQUE_HIDDEN}) for _ in range(3)]
		self.your_resources_to_other_players = [dotdict({k:0 for k in RESOURCES_UNIQUE_HIDDEN}) for _ in range(3)]


	def get_longest_road_length(self, depth=0, subset=None, constrained_starts = None):
		"""
		gets the longest road length for a player
		currently working :D
		"""
		if not subset and len(self.edges)==0:
			return 0 
		if subset <> None and len(subset)==0:
			return 1
		if subset == None:
			subset = copy(self.edges)
		path_lengths = [0]
		if not constrained_starts:
			iterset = subset
		else:
			iterset = constrained_starts
		for edge in iterset:
			#make new edge list that removes the current edge
			edges_copy = copy(subset)
			edges_copy.remove(edge)
			#now iterate over all neighbors
			valid_neighbors = CONNECTED_EDGES[edge]
			paths_to_search = valid_neighbors.intersection(edges_copy)
			for valid_path in paths_to_search:
				path_lengths.append(self.get_longest_road_length(depth+1, edges_copy, [valid_path]))
		if depth==0:
			self.longest_road_length = 1 + max(path_lengths)
		return 1 + max(path_lengths)

	def roadbuilding_possible_options(self):
		"""
		determines all frozensets of possible roadbuilding pairs
		"""
		frozensets = set()
		#calculate all adjacent edges
		connected_edges = set()
		for edge in self.edges:
			connected_edges.add(CONNECTED_EDGES[edge])
		#remove occupied ones
		open_edges = self.game.open_edges 
		connected_edges = connected_edges.intersection(open_edges)
		#iterate over all empty tiles connected to player, then iterate over all empty tiles connected to player and potential road
		for edge in connected_edges:
			#check all edges that could be built from that edge if connected
			possible_additions = CONNECTED_EDGES[edge].intersection(open_edges)
			for addition in possible_additions:
				frozensets.add(frozenset([addition, edge]))
		return frozensets

	def serialize_roadbuilding_frozensets(self, frozensets):
		"""
		creates overlay
		"""
		n_sets = len(frozensets)
		M_player_edges = np.zeros([n_sets, 72])
		for i, fset in enumerate(frozensets):
			cols = list(fset)
			M_player_edges[i,cols[0]] = 1
			M_player_edges[i, cols[1]] = 1
		return M_player_edges

	def trade_serialization(self, trades, target_player):
		"""
		serializes potential trades made with another player
		returns a length-20 vector, with the target resources occupying slots 6-20
		"""
		offset = (target_player.order - self.order) % 4

		n_trades = len(trades)
		M_trades = np.zeros([n_trades,20])
		for i, trade in enumerate(trades):
			for j, v in enumerate(trade[0]):
				M_trades[i,j] = v 
			for j, v in enumerate(trade[1]):
				M_trades[i,j+5*offset] = v 
		return M_trades 

	def construct_decision_serialization(self, decision_type):
		"""
		takes a decision type and serialize all possibilities

		POSSIBILITIES:
		* build settlement
		* build city
		* build road
		* buy development card

		* use knight card
		* use monopoly card
		* use year of plenty card
		* use road building card

		* trade

		* convert resources
		"""

	def trade_response_serialization(self, trades, source_player):
		"""
		will look at an offered trade and serialize the response
		it is a bit of an inversion of trade_serialization
		the main difference will be that there will be a turn flag
		that determines whose turn it is
		"""

	def convert_resources_serialization(self):
		"""
		determines how many ways player can trade resources

		* 4 for 1 
		* 3 for 1 (default if available)
		* 2 for 1 (default if available for individual resources)
		"""

	def serialize_self(self, external=False, force=False, source_player=None):
		"""
		will return either a self-visible or publicly-visible amount of information 
		in the form of a vector

		PUBLIC LENGTH: 195
		PRIVATE LENGTH: 202
	    # of resources [DIM=5]
	    SETTLEMENT VECTOR [DIM=54]
	    CITY VECTOR [DIM=54]
	    ROAD VECTOR [DIM=72]

	    DEVELOPMENT CARDS READY VECTOR [DIM=5]
	    DEVELOPMENT CARDS RECENT VECTOR [DIM=5]
	    DEVELOPMENT CARDS PLAYED VECTOR [DIM=3, public and private] 

	    N DEVELOPMENT CARDS RECENT [DIM=1, numeric, public only] 
	    N DEVELOPMENT CARDS READY [DIM=5, numeric,  time-lagged] 

		LONGEST_ROAD [DIM=1]
		LARGEST_ARMY [DIM=1]
		NUMBER_OF_KNIGHTS [DIM=1]
		LONGEST_ROAD_LENGTH [DIM=1]

		POINTS VISIBLE
		POINTS ACTUAL 
		"""
		if self.changed or force or (self.serialized_self == None):
			#0/5, PUBLIC/PRIVATE
			V_resources = np.asarray([
				self.resources.wood, 
				self.resources.grain,
				self.resources.wool,
				self.resources.ore,
				self.resources.brick
				])
			#54, PUBLIC/PRIVATE, 54/59
			V_settlements = np.zeros(54)
			for s in self.settlements:
				V_settlements[s] = 1

			#54, PUBLIC/PRIVATE, 109/113
			V_cities = np.zeros(54)
			for s in self.cities:
				V_cities[s] = 1

			#72, PUBLIC/PRIVATE, 181/185
			V_roads = np.zeros(72)
			for s in self.edges:
				V_roads[s] = 1

			#0/5, PUBLIC/PRIVATE, 181/190
			V_development_cards_ready = np.zeros(5)
			#0/5, PUBLIC/PRIVATE, 181/195
			V_development_cards_recent = np.zeros(5)
			#3/3, PUBLIC/PRIVATE, 184/198
			V_development_cards_played = np.zeros(3)
			for key, value in self.development_cards_ready.iteritems():
				V_development_cards_ready[DEVELOPMENT_CARD_UNIQUE_INDEX[key]] = value 

			for key, value in self.development_cards_recent.iteritems():
				V_development_cards_recent[DEVELOPMENT_CARD_UNIQUE_INDEX[key]] = value 

			for key, value in self.development_cards_played.iteritems():
				V_development_cards_played[DEVELOPMENT_CARD_SPECIAL_INDEX[key]] = value 

			#3, PUBLIC/PRIVATE, 187/201
			V_number_knights = [self.knights]
			V_longest_road = [self.longest_road_length]
			V_visible_points = [self.visible_points]
			#0/1, PUBLIC/PRIVATE, 187/202
			V_actual_points = [self.actual_points]

			#1/0, PUBLIC/PRIVATE, 188/202
			V_n_development_cards_recent = [self.n_development_cards_recent]
			#this has length of 5; using monopoly/year of plenty cards the following turn
			#to get new development cards may obfuscate data marginally
			#1/0, PUBLIC/PRIVATE, 189/202
			V_n_development_cards_ready = self.n_ready_development_history

			#now serialize what external player knows
			#6/0, PUBLIC/PRIVATE, 195/202
			if external:
				e_resources = source_player.other_player_resources[(self.order - source_player.order) % 4]
				V_external_resources = np.asarray([
				e_resources.wood, 
				e_resources.grain,
				e_resources.wool,
				e_resources.ore,
				e_resources.brick,
				e_resources.unknown
				])

			self.serialized_self = np.concatenate( (
				V_resources,#5, 0:5
				V_settlements,#54, 5:59
				V_cities,#54, 59:113
				V_roads,#72, 113:185
				V_development_cards_ready,#5, 185:190
				V_development_cards_recent,#5, 190:195
				V_development_cards_played,#3, 195:198
				V_n_development_cards_ready,#1, 198:199
				V_number_knights,#1, 199:200
				V_longest_road,#1, 200:201
				V_visible_points,#1, 201:202
				V_actual_points))#1, 202:203
			#note that resources visible to other players are modified elsewhere
			#numbers are slightly off, but the comments above each of the individual calculations are correct
			self.visible_serialized_self = np.concatenate( (
				V_settlements,#0:54
				V_cities,# 54:108
				V_roads,# 108:180
				V_development_cards_played, #180:183
				V_n_development_cards_recent, #185:186
				V_n_development_cards_ready, #186:187
				V_number_knights, #187:188
				V_longest_road, #188:189
				V_visible_points,
				V_external_resources) #189:190
				)
		#map + self + 3 players dim = 516 + 203 + 3*190 = 1289	
		if external:
			return self.visible_serialized_self
		else:
			return self.serialized_self
	'''
	#considering not doing this due to complexity
	def forecast_self_serialization(self, 
		resource_modifications=[], 
		development_card_modifications = [],
		settlement_modifications=[],
		city_modifications=[],
		road_modifications=[],
		external=False,
		zip_args=True):
		"""
		CURRENTLY NOT USING...
		this will create series of vectors that modify the self-serialization, which

		"""
		iter_args = {}
		if resource_modifications <> []:
			iter_args['resource_modifications'] = resource_modifications
		if development_card_modifications <> []:
			iter_args['development_card_modifications'] = development_card_modifications
		if settlement_modifications <> []:
			iter_args['settlement_modifications'] = settlement_modifications
		if city_modifications <> []:
			iter_args['city_modifications'] = city_modifications
		if road_modifications <> []:
			iter_args['road_modifications'] = road_modifications
		#not sure if force=True should be set...
		self.forecast_self_serialization(force=True)

		if external:
			external_copy = copy(self.visible_serialized_self)
			if zip_args:
				pass
		else:
			internal_copy = copy(self.serialized_self)
	'''

	def serialize_other_players(self):
		"""
		this appends the serialized values for the other 3 players to you
		"""
		return np.concatenate([player.serialize_self(external=True) for player in self.other_players])

	def serialize_hidden_information(self):
		"""
		string together hidden information for next three players, then append information 
		they know about you to the next part
		"""


	def serialize_game(self):
		"""
		full serialization for input to neural network

		MAP SERIALIZATION
		SELF SERIALIZATION
		OTHER PLAYERS PUBLIC SERIALIZATION
		OTHER PLAYERS PRIVATE SERIALIZATION
		YOUR PRIVATE SERIALIZATION WITH RESPECT TO OTHER PLAYERS
		"""
		print 'full serialization not implemented yet'

	def reset_state(self):
		"""
		reverts most settings to beginning of game, 
		but keeps history among other non-game-specific attributes
		in tact
		"""
		print 'reset state not implemented yet'

	def rel(self, player):
		return (4 + self.order - player.order) % 4
	#will be called often with None special_mode due to turn number
	#relevance for probability calculation

	def decision_serialization(self, special_mode=None):
		"""
		resource trade vectors [DIM=20]
		card usage vector [DIM=5]
		knight placement vector [DIM=19]
		monopoly resource choice vector [DIM=5]
		turn indicator [DIM=4]
		#YEAR OF PLENTY RESOURCE VECTOR WILL BE DIRECTLY FORECASTED
		#ALL BUILDING WILL BE DIRECTLY FORECASTED
		#DIM = base_dim + 20 + 5 + 19 + 5 + 4
		"""

def offerings_requests_cartesian_filter(offerings, requests):
	"""
	will create a cartesian product of all offerings and requests
	requests will not be filtered by the receiving player as to avoid
	giving the AI extra knowledge of what the opponent has

	this will need to filter out offerings and requests which contain the same resources, however
	"""
	trades = [] 
	for offer in offerings:
		for request in requests:
			if check_mutual(offer, request):
				trades.append([offer, request])
	return trades 

def check_mutual(offer, request):
	for i in range(5):
		if offer[i] * request[i] > 0:
			return False 
	return True 