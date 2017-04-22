class PlayerListController(object):
    """Acts on PlayerList 'start-game' events."""
    def __init__(self, player_list, game_factory):
        self.player_list = player_list
        self.player_list.subscribe('start-game', self._onStartGame)
        self.game_factory = game_factory

    def _onStartGame(self, ev, players):
        """Create a new game and give it to the players."""
        name1, name2 = players
        p1 = self.player_list.getPlayer(name1)
        p2 = self.player_list.getPlayer(name2)
        game = self.game_factory(name1, name2)
        p1.notify('start-game', [game, name2])
        p2.notify('start-game', [game, name1])

class PlayerController(object):
    """Acts on Player 'start-game' events."""
    def __init__(self, vat, player):
        self.player = player
        self.vat = vat
        self.player.subscribe('start-game', self._onStartGame)

    def _onStartGame(self, ev, info):
        """Insert game into this player's vat and notify UI."""
        game, other_player = info
        self.vat.provide('game', game)
        self.player.notify('new-game', other_player)
