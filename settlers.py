from game import Game 
from player import Player 

def main():
	initial_checks()



def initial_checks():
	"""
	used to verify that various aspects of the game engine are working
	"""
	test_game = Game(id=0)
	players = test_game.players
	hexmap = test_game.hexmap
	#print hexmap
	p0 = players[0]
	print p0.get_longest_road_length()
	for e in [0,1,2,3,8, 62, 58, 51, 44,45,46,47]:
		p0.edges.add(e)
	print p0.get_longest_road_length()

if __name__=='__main__':
	main()
