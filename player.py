from constants import edge_vertices, cell_vertices, cell_edges
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
		self.other_player_resources = [{k:0 for k in RESOURCES_UNIQUE_HIDDEN} for _ in range(3)]
		self.your_resources_to_other_players = [{k:0 for k in RESOURCES_UNIQUE_HIDDEN} for _ in range(3)]

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

	def serialize_self(self, external=False, force=False):
		"""
		will return either a self-visible or publicly-visible amount of information 
		in the form of a vector

		PUBLIC LENGTH: 190
		PRIVATE LENGTH: 203
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
			V_resources = np.asarray([
				self.resources.wood, 
				self.resources.grain,
				self.resources.wool,
				self.resources.ore,
				self.resources.brick
				])

			V_settlements = np.zeros(54)
			for s in self.settlements:
				V_settlements[s] = 1

			V_cities = np.zeros(54)
			for s in self.cities:
				V_cities[s] = 1

			V_roads = np.zeros(72)
			for s in self.edges:
				V_roads[s] = 1

			V_development_cards_ready = np.zeros(5)
			V_development_cards_recent = np.zeros(5)
			V_development_cards_played = np.zeros(3)
			for key, value in self.development_cards_ready.iteritems():
				V_development_cards_ready[DEVELOPMENT_CARD_UNIQUE_INDEX[key]] = value 

			for key, value in self.development_cards_recent.iteritems():
				V_development_cards_recent[DEVELOPMENT_CARD_UNIQUE_INDEX[key]] = value 

			for key, value in self.development_cards_played.iteritems():
				V_development_cards_played[DEVELOPMENT_CARD_SPECIAL_INDEX[key]] = value 

			V_number_knights = [self.knights]
			V_longest_road = [self.longest_road_length]
			V_visible_points = [self.visible_points]
			V_actual_points = [self.actual_points]

			V_n_development_cards_recent = [self.n_development_cards_recent]
			#this has length of 5; using monopoly/year of plenty cards the following turn
			#to get new development cards may obfuscate data marginally
			V_n_development_cards_ready = self.n_ready_development_history

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
			self.visible_serialized_self = np.concatenate( (
				V_settlements,#0:54
				V_cities,# 54:108
				V_roads,# 108:180
				V_development_cards_played, #180:185
				V_n_development_cards_recent, #185:186
				V_n_development_cards_ready, #186:187
				V_number_knights, #187:188
				V_longest_road, #188:189
				V_visible_points) #189:190
				)
		if external:
			return self.visible_serialized_self
		else:
			return self.serialized_self

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

		else:
			internal_copy = copy(self.serialized_self)


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