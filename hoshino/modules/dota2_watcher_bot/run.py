import json
from .player import Player
from . import DOTA2
from hoshino import Service, priv, aiorequests

sv = Service(
    'dota-poller2',
    use_priv=priv.SUPERUSER,
    enable_on_default=False,
    manage_priv=priv.SUPERUSER,
    visible=True,
    help_='添加玩家 玩家昵称 数字id\n如：添加玩家 前成员 108146306\n'
)

apikey = "0DEDEEC36762100FC99B93ECAD100E27" # http://steamcommunity.com/dev/apikey
proxies = {
    'http': 'http://127.0.0.1:10809',
    'https': 'http://127.0.0.1:10809'
}

class DOTA2HTTPError(Exception):
    pass

def steam_id_convert_32_to_64(account_id):
    return account_id + 76561197960265728

bot = sv.bot
data = {}
fn = "./hoshino/modules/dota2_watcher_bot/playerInfo.json"

with open(fn) as file:
    tmp = json.load(file)
for gid, player_list in tmp.items():
    data[gid] = []
    for info in player_list:
        player = Player()
        player.load_dict(info)
        data[gid].append(player)

def save_to_json():
    tmp = {}
    for gid, player_list in data.items():
        tmp[gid] = []
        for player in player_list:
            tmp[gid].append(player.to_dict())
    with open(fn, "w") as file:
        json.dump(tmp, file, indent=4)

@sv.scheduled_job('cron', minute='*')   # 每分钟执行一次
async def update():
    print("updating")
    for gid, player_list in data.items():
        if not sv.check_enabled(gid):
            continue
        result = {}
        """
        result = {
            match_id_1 : [Player1, Player2]
            match_id_2 : [Player3]
        }
        """
        for player in player_list:
            account_id = player.account_id
            try:
                url = f"https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v1?key={apikey}&account_id={account_id}&matches_requested=1"
                try:
                    response = await aiorequests.get(url, timeout=10, proxies=proxies)
                except Exception as e:
                    print("10秒内无法连接到网站，建议检查网络，或者尝试使用代理服务器")
                    raise e
                prompt_error(response, url)
                match = await response.json()
                try:
                    match_id = match["result"]["matches"][0]["match_id"]
                except Exception as e:
                    print(e)
                if match_id != player.last_match_id:
                    if match_id not in result:
                        result[match_id] = [player]
                    else:
                        result[match_id].append(player)
                    player.last_match_id = match_id
            except DOTA2HTTPError:
                continue
        messages = []
        for match_id, player_list in result.items():
            try:
                url = f"https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/V1?key={apikey}&match_id={match_id}"
                try:
                    response = await aiorequests.get(url, timeout=10, proxies=proxies)
                except Exception as e:
                    print("10秒内无法连接到网站，建议检查网络，或者尝试使用代理服务器")
                    raise e
                prompt_error(response, url)
                match = await response.json()
                try:
                    match_info = match["result"]
                except KeyError:
                    raise DOTA2HTTPError("Response Error: Key Error")
                except IndexError:
                    raise DOTA2HTTPError("Response Error: Index Error")
            except DOTA2HTTPError:
                raise DOTA2HTTPError("DOTA2开黑战报生成失败")
            txt = DOTA2.generate_message(match_info, player_list)
            messages.append(txt)
        if messages:
            data[gid] = player_list
            for msg in messages:
                print(msg)
                await bot.send_group_msg(group_id=gid, message=msg)
    save_to_json()
    print("done")

def prompt_error(response, url):
    if response.status_code >= 400:
        if response.status_code == 401:
            raise DOTA2HTTPError("Unauthorized request 401. Verify API key.")
        if response.status_code == 503:
            raise DOTA2HTTPError("The server is busy or you exceeded limits. Please wait 30s and try again.")
        raise DOTA2HTTPError("Failed to retrieve data: %s. URL: %s" % (response.status_code, url))

@sv.on_prefix('添加玩家')
async def add_dota2_player(bot, ev):
    cmd = ev.raw_message
    content=cmd.split()
    if len(content) != 3:
        reply="请输入：添加玩家 玩家昵称 数字id\n如：添加玩家 前成员 108146306\n"
        await bot.finish(ev, reply)
    nickname = content[1]
    account_id = int(content[2])
    # steamid = steam_id_convert_32_to_64(account_id)
    gid = str(ev['group_id'])

    # 新建一个玩家对象, 放入玩家列表
    temp_player = Player(account_id, nickname)
    for player in data[gid]:
        if player.account_id == account_id:
            player.nickname = nickname
            reply = "玩家已存在，更新昵称"
            break
    else:
        data[gid].append(temp_player)
        reply = "玩家添加成功"
    save_to_json()
    await bot.send(ev, reply)
