

"""

the first network, which only looks at the placement of the initial tiles, 
will require map information and road/settlement information of other players

moves will have a simple constraint check, as well as a forecast to see if that is a proper move

SECOND NETWORK

action types:

CONSTRAINT CHECK, RESOURCE & STATE MODIFICATION FOR PREDICTION

* build road
* build settlement
* upgrade settlement to city
* buy development card

CONSTRAINT CHECK, SPECIAL DECISION FLAG, STATE MODIFICATION FOR PREDICTION

* play knight card (choose tile) [DIM=1, 0-for-NO]
* move robber to a tile [DIM=1]
* play monopoly card & name resource [DIM=5, 0-FOR-NO]

ADVANCED CONSTRAINT CHECK, LARGE SEARCH SPACE FOR PREDICTION, STATE MODIFICATION FOR PREDICTION

* play road_building [DIM=0]

MULTIPLE CHOICE DECISION FLAG

* steal as a result of robber moving (choose target) [DIM=3]

EXTRA STATE FLAGS, STATE MODIFICATION FOR PREDICTION
* choose which cards to discard when hand > 7 when 7 is rolled [DIM=1 (for indicating others may need to discard)]

STATE MODIFICATION FOR PREDICTION

* play year of plenty card [ROW=15+1 (no modification)]
"""


class PlayerAI(object):
	def __init__(self,filename=None,id=None):
		self.filename = filename 
		self.id = id 
