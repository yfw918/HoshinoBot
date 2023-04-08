import requests
from datetime import datetime
from .DOTA2_dicts import *
from hoshino import Service
import nonebot
import time
import aiohttp

players = {  # 手动维护
    # 125581247: 'Ame',
    # 177416702: 'Ame',
    # 898754153: 'Ame',
    106863163: 'Maybe',
    108376607: 'Cty',
    140613225: 'Cty',
    # 111189717: 'Inflame',
    # 207917054: 'Inflame',
    94054712: 'Topson',
    # 111620041: 'Sumail', # 没开共享
    139822354: 'Setsu',
    108146306: 'qcy',
}

apikey = '' # https://steamcommunity.com/dev/apikey
url_prefix = "http://api.steampowered.com"
proxies = { # socks5代理需要额外安装pysocks库
    "http": "http://127.0.0.1:10809",
    "https": "http://127.0.0.1:10809",
}

class Player:
    def __init__(self, account_id, last_match=0, personaname='') -> None:
        self.account_id = account_id
        self.last_match = last_match
        self.personaname = personaname

def get_url(url, max_retries=5):    # 梯子是真你妈垃圾
    for i in range(max_retries):
        response = requests.get(url, proxies=proxies, timeout=10)
        if response.status_code == 200:
            return response
        else:
            print(f"重试第{i+1}次")
    return None

player_list = []
for id in players.keys():
    try:
        player_list.append(Player(id, get_url(f"{url_prefix}/IDOTA2Match_570/GetMatchHistory/v1?key={apikey}&account_id={id}&matches_requested=1").json()['result']['matches'][0]['match_id'], players[id]))
        print(f"{id}已导入到player_list")
    except Exception as e:
        print(e)

sv = Service('mydota2', enable_on_default=False)

datas = {}  # 缓存获取到的比赛详情，如果是开黑的话就不必多次调用api了

@sv.scheduled_job('cron', minute='*')   # 每分钟执行一次
async def dota():
    bot = nonebot.get_bot()

    for player in player_list:

        try:
            last_match = get_url(f"{url_prefix}/IDOTA2Match_570/GetMatchHistory/v1?key={apikey}&account_id={player.account_id}&matches_requested=1").json()['result']['matches'][0]['match_id']
        except Exception as e:
            last_match = player.last_match  # 否则会重复报上一局的战绩
            await bot.send_group_msg(group_id=691740214, message=f'获取{player.account_id}的last_match失败: {e}')

        if last_match != player.last_match:
            player.last_match = last_match
            match_id = last_match

            try:
                personaname = player.personaname if player.personaname else get_url(f"{url_prefix}/ISteamUser/GetPlayerSummaries/v2?key={apikey}&steamids={player.account_id+76561197960265728}").json()['response']['players'][0]['personaname']
            except Exception as e:
                await bot.send_group_msg(group_id=691740214, message=f'获取{player.account_id}的personaname失败: {e}')
            account_id = player.account_id

            if match_id in datas.keys():
                data = datas[match_id]
                await bot.send_group_msg(group_id=691740214, message=f'比赛数据已经缓存')
            else:
                try:
                    data = get_url(f"{url_prefix}/IDOTA2Match_570/GetMatchDetails/v1?key={apikey}&match_id={match_id}").json()['result']
                    datas[match_id] = data
                except Exception as e:
                    await bot.send_group_msg(group_id=691740214, message=f'获取{player.personaname}的match_detail失败: {e}')

            radiant_win = data['radiant_win']
            duration = data['duration']
            start_time = data['start_time']
            cluster = data['cluster']
            # lobby_type = data['lobby_type']
            game_mode = data['game_mode']
            radiant_score = data['radiant_score']
            dire_score = data['dire_score']
            radiant_damage = 0
            dire_damage = 0
            czl = 0
            for player in data['players']:
                if player['team_number']:
                    dire_damage += player.get('hero_damage', 0)    # 老比赛没有
                else:
                    radiant_damage += player.get('hero_damage', 0) # 老比赛没有
                if player['account_id'] == account_id:
                    team = 'dire' if player['team_number'] else 'radiant'
                    hero = player['hero_id']
                    kills = player['kills']
                    deaths = player['deaths']
                    assists = player['assists']
                    last_hits = player['last_hits']
                    denies = player['denies']
                    gpm = player['gold_per_min']
                    xpm = player['xp_per_min']
                    net_worth = player['net_worth']
                    hero_damage = player.get('hero_damage', 0)
                    tower_damage = player.get('tower_damage', 0)
                    hero_healing = player.get('hero_healing', 0)
            win = True if radiant_win and team == 'radiant' or not radiant_win and team == 'dire' else False
            if team == 'radiant':
                damage_percent = f"{100 * hero_damage/radiant_damage:.3}%" if radiant_damage else 0
                czl = f"{100 * (kills+assists)/radiant_score:.3}%" if radiant_score else 0
            else:
                damage_percent = f"{100 * hero_damage/dire_damage:.3}%" if radiant_damage else 0
                czl = f"{100 * (kills+assists)/dire_score:.3}%" if dire_score else 0
            kda = f"{(kills+assists)/deaths:.2f}" if deaths else kills+assists

            msg = ''

            radiant_name = data.get('radiant_name')
            dire_name = data.get('dire_name')
            if radiant_name or dire_name:
                msg += f"锦标赛：{radiant_name} vs {dire_name}\n"

            msg += f"{personaname}使用{HERO_NAMES.get(hero, '未知新英雄')}"
            msg += "赢得了比赛，" if win else "输掉了比赛，"
            msg += f"比分：{radiant_score}:{dire_score}\n" if team == 'radiant' else f"比分：{dire_score}:{radiant_score}\n"
            msg += f"游戏模式：{GAME_MODE.get(game_mode, '未知新模式')}，服务器：{CLUSTER.get(cluster, '未知服务器')}\n"
            msg += f"时间：{datetime.fromtimestamp(start_time)}，时长：{duration//60}分{duration%60}秒\n"
            msg += f"战绩：{kills}/{deaths}/{assists}，KDA：{kda}，补刀：{last_hits}/{denies}\n"
            msg += f"财产综合：{net_worth}，GPM：{gpm}，XPM：{xpm}\n"
            msg += f"英雄伤害{hero_damage}，建筑伤害{tower_damage}，英雄治疗{hero_healing}\n"
            msg += f"参战率：{czl}，伤害百分比：{damage_percent}"
            msg += f"https://www.opendota.com/matches/{match_id}"

            await bot.send_group_msg(group_id=691740214, message=msg)
