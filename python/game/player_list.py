from serf.publisher import Publisher

# Don't actually need to transport Player objects.
# If anything they would go as Proxies. But this is
# an informative example.

# from serf.json_codec import JSONCodec

# def makePlayer(vat, data):
#     player_list = vat.storage['players']
#     player = Player(player_list, data)
#     vat.refs.append(player)
#     return player

# JSONCodec.hooks['Player'] = makePlayer

# This would be added as a method of the Player class.
#    def ext_encoding(self):
#        return 'Player', self.name

class Player(Publisher):
    def __init__(self, player_list):
        Publisher.__init__(self)
        self.name = None
        self.player_list = player_list

    def setName(self, name):
        self.name = name
        self.player_list.notify('online', [str(hash(self)),name])

class PlayerList(Publisher):
    """Model for a collection of online players.

    Events:
        ('online', player) online player has chosen a name
        ('offline', player) player has gone offline
    """
    def init(self, online_list):
        """Implements factory interface for OnlineList."""
        Publisher.__init__(self)
        self.online_list = online_list
        self.online_list.subscribe('offline', self._notifyPlayerOffline)

    def make(self):
        """Implements factory interface for OnlineList."""
        return Player(self)
        
    def _notifyPlayerOffline(self, ev, info):
        """Convert OnlineList offline notifications to player format."""
        addr, player = info
        if player.name is not None:
            self.notify('offline', str(hash(player)))

    def getPlayers(self):
        """Return dictionary of players who have given a name."""
        players = {}
        for addr, player in self.online_list.items():
            if player.name is not None:
                players[str(hash(player))] = player.name
        return players

    def getPlayer(self, name):
        """Get player with a given name."""
        for addr, player in self.online_list.items():
            if player.name == name:
                return player
