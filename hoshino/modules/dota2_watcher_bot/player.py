class Player:
    def __init__(self, steamid='', nickname='', last_match_id=0):
        self.steamid = steamid
        self.nickname = nickname
        self.last_match_id = last_match_id
        self.stats = {}

    def to_dict(self):
        output = {}
        output["steamid"] = self.steamid
        output["nickname"] = self.nickname
        output["last_match_id"] = self.last_match_id
        return output

    def load_dict(self, d):
        self.steamid = d["steamid"]
        self.nickname = d["nickname"]
        self.last_match_id = d["last_match_id"]

    def load_player_info(self, player_game_info):
        tmp["kill"] = player_game_info['kills']
        tmp["death"] = player_game_info['deaths']
        tmp["assist"] = player_game_info['assists']
        tmp["kda"] = (tmp["kill"] +  tmp["assist"]) / max(tmp["death"], 1)

        tmp["dota2_team"] = get_team_by_slot(player_game_info['player_slot'])
        tmp["hero"] = player_game_info['hero_id']
        tmp["last_hit"] = player_game_info['last_hits']
        tmp["damage"] = player_game_info['hero_damage']
        tmp["gpm"] = player_game_info['gold_per_min']
        tmp["xpm"] = player_game_info['xp_per_min']
        self.stats = tmp