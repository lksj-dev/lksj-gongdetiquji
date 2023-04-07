import json
import logging
import os
import signal
import sqlite3
import time

from aiohttp import ClientSession
from khl import Bot, Message, MessageTypes
from khl.card import CardMessage, Card, Element, Module, Types

from .filter import allow
from .processor import get_files_to_upload
from .uploader import create_uploader

bot=Bot(token=os.environ['BOT_TOKEN'])

downloader=ClientSession()

with open('./data/uploader.json') as f:
    uploader=create_uploader(json.load(f))

history=sqlite3.connect('./data/history.db')

history.execute('CREATE TABLE IF NOT EXISTS history (timestamp BIGINT, msg_id VARCHAR(100), src_url TEXT, paste_url TEXT);')
history.execute('CREATE TABLE IF NOT EXISTS upload_perm (guild_id TEXT, subject TEXT);')

def create_status_card() -> CardMessage:
    total_pastes_served=history.execute('SELECT COUNT(*) FROM history;').fetchone()[0]
    status=Card(
        Module.Section(
            Element.Text('**功德提取机**\n一只默默将日志或崩溃报告转存到粘贴箱上的机器人', 'kmarkdown'),
            accessory=Element.Image(bot.me.avatar), mode='left'
        ),
        Module.Divider(),
        Module.Section(Element.Text(f'目前已累计转存 {total_pastes_served} 份日志或崩溃报告。', 'kmarkdown')), 
        Module.Divider(),
        Module.Section(Element.Text(f'**Q：**这是什么？\n**A：**我是将您的日志及崩溃报告转存至粘贴箱的机器人，以方便崩溃分析人员找到并解决问题。', 'kmarkdown')),
        Module.Divider(),
        Module.Section(Element.Text(f'**Q：**为什么要使用粘贴箱？\n**A：**这可以让崩溃分析人员不用下载就可以快速浏览您上传的日志，还可以避免刷屏。', 'kmarkdown')),
        Module.Divider(),
        Module.Section(Element.Text(f'**Q：**如何使用？**\nA：**直接在此发送日志或崩溃报告文件，我会自动识别并帮你转存。', 'kmarkdown')),
        theme='primary'
    )
    return CardMessage(status)

@bot.on_startup
async def on_bot_started(b: Bot):
    # Define graceful exiting handler
    def graceful_exit():
        logging.info('SIGTERM/SIGINT received, stopping...')
        # Trick khl.py to stop
        raise KeyboardInterrupt()
    # Register the graceful exiting handler, so that docker can kill the process faster
    b.loop.add_signal_handler(signal.SIGTERM, graceful_exit)
    b.loop.add_signal_handler(signal.SIGINT, graceful_exit)
    # Fetch profile info of bot itself
    await b.fetch_me()
    # Start playing a "game"
    await b.client.update_playing_game(890880) # JetBrains Aqua

    add_keyword={ '+', '允许', '添加', '增加' }
    remove_keyword={ '-', '禁止', '删除', '移除' }

    @bot.command(name='功德提取机显式上传权限', prefixes=['////'])
    async def explicit_upload_perm(msg: Message, op: str, subject: str):
        if msg.author == msg.ctx.guild.master_id:
            if subject.startswith('(rol)') and subject.endswith('(rol)'):
                subject=subject.removeprefix('(rol)').removesuffix('(rol)')
            elif subject.startswith('(met)') and subject.endswith('(met)'):
                subject=subject.removeprefix('(met)').removesuffix('(met)')
            else:
                await msg.reply('第二个参数必须是 @ 某个人或 @ 某个特定角色。')
                return
            exists=history.execute('SELECT * FROM upload_perm WHERE guild_id = ? AND subject = ?;', 
                (msg.ctx.guild.id, subject)).fetchone()
            if op in add_keyword:
                if exists:
                    await msg.reply('该用户/角色已有强制上传日志权限，无需再次添加。')
                else:
                    with history:
                        history.execute('INSERT INTO upload_perm VALUES (?, ?);', (msg.ctx.guild.id, subject))
                    await msg.reply('指定用户/角色现在可以强制上传指定日志了。')
            elif op in remove_keyword:
                if exists:
                    with history:
                        history.execute('DELETE FROM upload_perm WHERE guild_id = ? AND subject = ?;', (msg.ctx.guild.id, subject))
                    await msg.reply('指定用户/角色现在不能再强制上传指定日志了。')
                else:
                    await msg.reply('该用户/角色并无强制上传日志权限，不需要再次删除其权限。')

def has_permission_to_force_upload(guild_id: str, subject_id: str):
    return bool(history.execute('SELECT * FROM upload_perm WHERE guild_id = ? AND subject = ?;', (guild_id, subject_id)).fetchone())

@bot.on_message(MessageTypes.SYS)
async def file_watch(msg: Message):
    # Ignore bot messages
    if msg.author.bot:
        return
    self_mentioned=bot.me.id in msg.extra['mention']
    cards=[]
    # Try parse card message. 
    # Uploaded files are represented by a card message containing file module.
    if msg.type == MessageTypes.CARD:
        try:
            cards=json.loads(msg.content)
        except:
            return
    elif 'quote' in msg.extra and self_mentioned:
        try:
            cards=json.loads(msg.extra['quote']['content'])
        except:
            return
    elif self_mentioned:
        await msg.reply(create_status_card(), is_temp=True)
        return
    reply=[
        Module.Section(Element.Text('**功德提取机**\n一只默默将日志或崩溃报告转存到粘贴箱上的机器人', 'kmarkdown'),
            accessory=Element.Image(bot.me.avatar), mode='left')
    ]
    allow_force_upload=any([ has_permission_to_force_upload(msg.ctx.guild.id, str(role)) for role in msg.author.roles ])
    if not allow_force_upload:
        allow_force_upload=has_permission_to_force_upload(msg.ctx.guild.id, msg.author_id) or msg.ctx.guild.master_id == msg.author_id
    for card in cards:
        card: dict
        modules: list=card.get('modules', [])
        for m in modules:
            if m['type'] == 'file':
                fname=m['title']
                src_url=m['src']
                async with downloader.get(src_url) as resp:
                    content=await resp.read()
                    if not (self_mentioned and allow_force_upload) and not allow(fname, content):
                        continue
                    for name, content, full in get_files_to_upload(fname, content):
                        paste_url=await uploader.upload(name, content)
                        reply+=[
                            Module.Divider(),
                            Module.Section(Element.Text(f'您的日志/崩溃报告已{"" if full else "部分"}转存。')),
                            Module.ActionGroup(Element.Button(Element.Text('点击浏览（可能需要代理）', Types.Text.PLAIN), value=paste_url, click='link', theme='info')),
                            Module.Context(Element.Text(f'您也可以复制链接后访问：\n[{paste_url}]({paste_url})', 'kmarkdown'))
                        ]
                        with history:
                            history.execute('INSERT INTO history(timestamp, msg_id, src_url, paste_url) VALUES (?, ?, ?, ?)', (int(time.time()), msg.id, src_url, paste_url))
    if len(reply) > 1:
        for retry in range(3):
            try:
                await msg.reply(CardMessage(Card(*reply)))
                break
            except:
                logging.error(f'Failed to send message, retrying {retry + 1} times...')

@bot.on_shutdown
async def on_bot_terminate(b: Bot):
    await downloader.close()
    await uploader.close()
