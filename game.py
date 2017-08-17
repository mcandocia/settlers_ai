from constants import HexMap
from constants import DEVELOPMENT_CARD_VALUES
from player import Player 
from copy import copy 

import numpy as np 


class Game(object):
	def __init__(self, id, players=None, template_settings='default',
		ai_filename = None):
		self.id = id
		#initialize map
		if template_settings=='default':
			self.hexmap = HexMap()
		elif template_settings=='random':
			self.hexmap = HexMap(None,None,None,None)
		elif isinstance(template_settings, HexMap):
			self.hexmap = template_settings
		else:
			raise NotImplementedError('only "random", "default", and args of class `HexMap` are accepted')

		#initialize players
		if ai_filename is None:
			ai_args = [None for _ in range(4)]
		elif isinstance(ai_filename, list):
			ai_args = ai_filename
		else:
			ai_args = [ai_filename for _ in range(4)]
		if players is None:
			self.players = [Player(i, i, ai_arg, self) for i, ai_arg in enumerate(ai_args)]
		else:
			self.players = players
			for player in self.players:
				player.reset_state()
				player.game = self 
		#initialize and shuffle development cards...
		self.development_cards = copy(DEVELOPMENT_CARD_VALUES)
		np.random.shuffle(self.development_cards)
		self.number_of_development_cards = len(self.development_cards)

		#initialize road, settlement, and city occupation tiles
		self.open_edges = set(range(72))
		self.open_vertices = set(range(54))
		#roads only, in form of {edge_id:player_order}
		self.occupied_edges = {}
		#roads and cities, in form of {vertex_id:(player_order, 'city'/'settlement')}
		self.occupied_vertices = {}

		self.turn = 0
		#this will be a weighting vector for the training algorithm
		#so that turns with many state records do not have too much influence over model
		self.n_state_checks_per_turn = []

	def serialize_self(self):
		"""
		no additional data is needed for network
		"""
		raise NotImplementedError("The Game does not need to be serialized...")


	def calculate_longest_road(self):
		pass

	def calculate_largest_army(self):
		pass