from hoshino import Service,priv
from random import choice

sv = Service('fuduji', use_priv=priv.NORMAL)

@sv.on_fullmatch('test')
async def hello(bot, ev):
    await bot.send(ev, "hello world")

@sv.on_fullmatch('是的')
async def hello(bot, ev):
    await bot.send(ev, '不是')

@sv.on_fullmatch('不是')
async def hello(bot, ev):
    await bot.send(ev, '是的')

@sv.on_prefix('对')
async def hello(bot, ev):
    await bot.send(ev, '不对')

@sv.on_fullmatch('不对')
async def hello(bot, ev):
    await bot.send(ev, '对的')

@sv.on_fullmatch('可以')
async def hello(bot, ev):
    await bot.send(ev, '不行')

@sv.on_fullmatch('不行')
async def hello(bot, ev):
    await bot.send(ev, '可以')

@sv.on_keyword(('资本', '美国'))
async def sigh(bot, ev):
    a = ['资本', '美国']
    kw = ev.message.extract_plain_text()
    for k in a:
        if k in kw:
            await bot.send(ev, f"唉，{k}")

@sv.on_fullmatch('原神')
async def hello(bot, ev):
    genshin = ["感觉不如原神。。。画质。。。", "玩原神玩的", "☆本群即将升级为原神群☆\n★本群即将升级为原神群★\n"*5]
    await bot.send(ev, choice(genshin))
