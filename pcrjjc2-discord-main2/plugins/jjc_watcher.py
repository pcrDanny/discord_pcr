from pcrclient import pcrclient, ApiException
from asyncio import Lock
from copy import deepcopy
from traceback import format_exc
from playerpref import decryptxml
from sender import *
from discord.ext import tasks
from bot import bot
from datetime import datetime , timedelta
import pandas as pd 
import aiocron
import os
import json
import time 
import discord
from collections import defaultdict

_config = None
_binds = None
enemy_chanel = None
_cache = None
qlck = Lock()
lck = Lock()
_clients = {}

async def query(id: str, client):
    async with qlck:
        while client.shouldLogin:
            await client.login()
        res = (await client.callapi('/profile/get_profile', {
            'target_viewer_id': int(id)
        }))
        return res['user_info']


def initialize(config):
    global _config, _binds, _cache, _clients  ,enemy_chanel , role_dict_11, role_dict_33
    role_dict_11 ={ "1" : "1v1 (１)" , 
    "2" : "1v1 (２)" , 
    "3" : "1v1 (３)" , 
    "4" : "1v1 (４)" , 
    "5" : "1v1 (５)" ,
    "6" : "1v1 (６)" ,
    "7" : "1v1 (７)" ,
    "8" : "1v1 (８)" ,
    "9" : "1v1 (９)" ,
    "10" : "1v1 (１０)" 
    }
    role_dict_33 ={ "1" : "3v3 (１)" , 
    "2" : "3v3 (２)" , 
    "3" : "3v3 (３)" , 
    "4" : "3v3 (４)" , 
    "5" : "3v3 (５)" ,
    "6" : "3v3 (６)" ,
    "7" : "3v3 (７)" ,
    "8" : "3v3 (８)" ,
    "9" : "3v3 (９)" ,
    "10" : "3v3 (１０)" ,
    "11": "1v1 (11)", 
    "12": "1v1 (12)", 
    "13": "1v1 (13)", 
    "14": "1v1 (14)", 
    "15": "1v1 (15)", 
    }
    _config = config
    if not os.path.exists(_config['binds_file']):
        with open(config['binds_file'], 'w') as f:
            json.dump({}, f)
    if not os.path.exists(_config['enemy_chanel']):
        with open(config['enemy_chanel'], 'w') as f:
            json.dump({}, f)        
    with open(config['binds_file'], 'r') as f:
        _binds = json.load(f)
    with open(config['enemy_chanel'], 'r') as f:
        enemy_chanel = json.load(f)     
    _cache = {}
    for server in config['playerprefs']:
        acinfo = decryptxml(config['playerprefs'][server])
        _clients[server] = pcrclient(acinfo['UDID'],
                                     acinfo['SHORT_UDID'],
                                     acinfo['VIEWER_ID'],
                                     acinfo['DL_BDL_VER'].decode(),
                                     '' if acinfo['TW_SERVER_ID'] == '1' else acinfo['TW_SERVER_ID'],
                                     _config['proxy'])
      #  print('TW-{} client started'.format(server))


bot.remove_command('help')


@bot.command(name='help')
async def _jjc_help(ctx):
    _sv_help = '''[bind uid server] 綁定競技場排名變動推送，默認雙場均啟用，僅排名降低時推送
[query uid1 server1 uid2 server2 ...] 查詢競技場簡要信息
[watch 11/33 on/off] 打開或者關閉11或者33的推送
[private on/off] 啟用或關閉私聊推送
server: 1 2 3 4(台一~台四)
============下面用不太到===========
[delete] 刪除競技場排名變動推送綁定
[delete id1 server1 id2 server2 ...] 刪除指定競技場排名變動推送綁定
[querystatus] 查看排名變動推送綁定狀態
============新增功能===========
#11 返回與你同區競技場的戰友的排名  >>方便搞電梯，建議在各自的指揮室用
#33 返回與你同區公主競技場的戰友的排名  >>方便搞電梯，建議在各自的指揮室用
#check_group 返回你兩個p場的group number
#enemy enemyid 4 >>設立你的仇家list 我限定每人只可有set兩個仇家
#e  >>返回你仇家現在兩個p 場的位置 方便你在裡面卡秒時 跟踪仇家
#delete_enemy enemyid 
#set enemyid >>把enemy id 跟頻道綁定
#unset enemyid >>把enemy id 跟頻道解綁'''
    await ctx.send(_sv_help)

#@aiocron.crontab('0 5 * * *') ###inital climb-up time
#async def cornjob1():  
  #  for set_id in enemy_chanel.keys():
      #  print( enemy_chanel[set_id]   )
     #   enemy_chanel[set_id]['11_time'] = 0
     #   enemy_chanel[set_id]['33_time'] = 0
   # save_enemy_chanel()    




#@tasks.loop(seconds=1)  #1823

@tasks.loop(seconds=110)
async def check_name():
    bind_enemy = {}
    async with lck:
        bind_enemy = deepcopy(enemy_chanel)
    for set_id in bind_enemy.keys():
        old_split_length= 0
        res = await query(set_id, _clients['4'])
        now_11 =res["arena_rank"] 
        now_33 =res["grand_arena_rank"]
        now_name  =res["user_name"]
        now_name = f"{now_name} {now_33}"
        try:
            channel = await bot.fetch_channel(enemy_chanel[set_id]['gid'])
         #  channel = bot.get_channel(int(bind_enemy[set_id]['gid']))
            old_name = str(channel)
         #   print( 'old_name',  old_name  )
            now_split_length = len( now_name.split(" ")[-1])    +1
          #  print( 'now_split_length', now_split_length   )
           # old_split_length = len(old_name.split("-")[-1]) + len( old_name.split("-")[-2]   ) +1  #-1 is 33 , -2 is 11 rank
            old_split_length = len(old_name.split("-")[-1]) +1
         #   print(  'old_split_length', old_split_length   )
            now_name_split = now_name[:len(now_name)- now_split_length]
          #  print(  now_name_split  )
            old_name_split =  old_name[:len(old_name)- old_split_length]
      #      print( now_name_split   )
       #     print( old_name_split   )
         #   print(  old_name_split  )
          #  old11 =  int(old_name.split("-")[-2] )
            old33 =  int(old_name.split("-")[-1] )
            if now_name.lower() != old_name.lower() :
                await channel.edit(name=now_name)
                if now_name_split.lower().replace(u'\u3000',u'').strip() != old_name_split.lower().replace("-", "".strip() ) :
                #    print(  'now_name_split.lower()', now_name_split.lower().replace(u'\u3000',u' ').strip()  )
                #    print(  'old_name_split.lower()', old_name_split.lower().replace("-", "".strip()   )  )
                    msg = f'{ old_name_split } 已改名至 {now_name_split}, channel名同時更新'
                    await channel.send(str(msg)  )
           # if now_11 != old11 :
             #   msg = f'11排名發生變化 {old11}>>{now_11},變動了{old11- now_11}名'
              #  await channel.send(str(msg)  )
            if now_33 != old33 :  
                msg = f'33排名發生變化 {old33}>>{now_33},變動了{old33- now_33}名'
                await channel.send(str(msg)  )      
        except:
            print(f'查詢出錯，{now_name}')

check_name.start()

@check_name.before_loop
async def before_myfunctionname():
    await bot.wait_until_ready()

@bot.command(name='bind')
async def on_arena_bind(ctx, dc_id : str, pcr_id: str, expire: int):
    """
        ctx: discord context
        pcr_id : 
    """
    super_uid = str(ctx.author.id)
    if super_uid=="714144621978189924":
        expire = datetime.now() + timedelta(days=expire*30)
        expire = expire.strftime("%Y-%m-%d")
        server = "4"
        uid = dc_id
        try:
            res = await query(pcr_id, _clients[server])
        except:
            return await ctx.send("未查詢到九碼,綁定失敗!")
        async with lck:
            last = _binds[uid] if uid in _binds else None   
            expire_date = expire
            if last is None: #1st buy and no uid in database
                next_data = [(server, pcr_id)]
            elif [server, pcr_id] in last['data']:  ###續費 or 1st buy but already have uid in database
                next_data = last['data']
            else:
                next_data = last['data'] + [(server, pcr_id)] ###add new sub-account
                expire_date = _binds[uid]['expire'] 
            if uid in  _binds :   ### add more account 
                _binds[uid] = {
                    'uid': uid,
                    'gid': ctx.channel.id,
                    'expire': expire_date ,
                    '11': True,
                    '33': True,
                    'data': next_data,
                    'is_private': last is not None and last['is_private'],
                    '11_group' :   _binds[uid]['11_group']   ,
                    '33_group' :   _binds[uid]['33_group'] 
                }
                save_binds()
            else: ### first bind 
                _binds[uid] = {
                    'uid': uid,
                    'gid': ctx.channel.id,
                    'expire':expire  ,
                    '11': True,
                    '33': True,
                    'data': next_data,
                    'is_private': last is not None and last['is_private'],
                    '11_group' :   res["arena_group"]   ,
                    '33_group' :   res["grand_arena_group"]
                }
                save_binds()   
            print_expire = _binds[uid]['expire']    
        await ctx.send(f'競技場綁定成功,到期日為{print_expire}')






   


@bot.command(name='farm')
async def check_farm(ctx, *args):
    uid = str(ctx.author.id)
    if uid =="714144621978189924" :
        farm_id = pd.read_excel('princess.xlsx')
        farm_id = farm_id[farm_id['FARM']==int(args[0])    ]      
        msg = [] 
        for index, row in farm_id.iterrows() :
         #   print(row)
            res = await query(row['ID'], _clients['4'])
            last_login = res['last_login_time']
            last_login = datetime.fromtimestamp(last_login).strftime("%B %d, %Y %H:%M:%S")
            msg.append( str(row['ID']) + " | " + row['LV'] + " | " + last_login    )
        msg = sorted(msg, key=lambda  x: x.split(' | ')[2] )
        msg = [ str(x) for x in msg  ]
        joined_string = "\n".join(msg)
    #  print( str(joined_string)  )
        await ctx.send(str(joined_string)  )  
    else:
        await ctx.send('你沒有農場')   

@bot.command(name='test')
async def enemy_check(ctx, *args):
    print(  'ctx.guild', ctx.guild  )
    member = await ctx.guild.fetch_member(742397309362503690)
    print(member.nick)
    for guild in bot.guilds:
        print(guild)
        print(guild.id)
  #  print(   ctx.author.name)







@tasks.loop(seconds=70)
async def on_arena_schedule():
    bind_cache = {}
    async with lck:
        bind_cache = deepcopy(_binds)

    for user in bind_cache:
        user_id = user
        bot.wait_until_ready()
        guild = bot.get_guild(729256891385118760) 
        print( 'guild', guild    )
        info = bind_cache[user]
        ### concate info and enemy list to one, then loop
        for (server, pcr_id) in info['data']:
            try:
                if info['11'] or  info['33'] :
                 #   print( "total time = " ,end_time -  beginning_time   )
                    res = await query(pcr_id, _clients[server])
                    name = res['user_name']
                    res = (res['arena_rank'], res['grand_arena_rank'],res['user_name'])
                    now = datetime.now()
                    if user not in _cache or pcr_id not in _cache[user]:
                        if user not in _cache:
                            _cache[user] = {}
                        _cache[user][pcr_id] = res
                        continue
                    last = _cache[user][pcr_id]
                    _cache[user][pcr_id] = res
                    if res[0] > last[0] and info['11']:
                        time = now.strftime("%H:%M:%S")
                        destination = {'user_id': info['uid']} if info['is_private'] else {'channel_id': _config['channel11']}
                        await send_msg(
                            **destination,
                            message=f'{time} : {name}的競技場排名發生變化：{last[0]}->{res[0]}，降低了{res[0]-last[0]}名。'
                                    + ('' if info['is_private']
                                    else at_person(user_id=user.replace("fake","")))  ### remove fake in ID
                        )

                    if res[1] > last[1] and info['33']:
                        time = now.strftime("%H:%M:%S")
                        destination = {'user_id': info['uid']} if info['is_private'] else {'channel_id': _config['channel33']}
                        await send_msg(
                            **destination,
                            message=f'{time} : {name}的公主競技場排名發生變化：{last[1]}->{res[1]}，降低了{res[1]-last[1]}名。' +
                            ('' if info['is_private'] else at_person(user_id=user.replace("fake","")))
                        )    
                    
                    if last[2] != name :
                     #   print("oldname", res[2]  ,name )
                        member = await guild.fetch_member(str(user_id))
                        group_11 = _binds[user_id]['11_group']
                        group_33 = _binds[user_id]['33_group']
                        tag_group = role_dict_11[str(group_11)] 
                        role11 = discord.utils.get(member.guild.roles, name=tag_group) #Bot get guild(server) roles
                        tag_group = role_dict_33[str(group_33)] 
                        role33 = discord.utils.get(member.guild.roles, name=tag_group) #Bot get guild(server) roles
                    #    print( 'role!!!!!!!!!!!!!!!' , role11.id   )
                        channel = await bot.fetch_channel(857205929274376232)
                        msg = f' <@&{str(role11.id)}> \n <@&{str(role33.id)}> \n{last[2]}已經改名為{name} ，同區大佬注意不要誤打 '
                        await channel.send(str(msg)  )
                        #await ctx.send(f'<@&{str(role.id)}> \n【{member_name}】在此跟同區1vs1-{group_11}區大佬訂下互不打恊議 \n當你打指令#11時會看到我遊戲名字劃線 \n代表每日15點排名結算前夕，除了前3名的自己人外 \n本人絕對不會刺其他非前3名的自已人 \n故結算前夕本人不在前3名時也請各位大佬不要刺我\n違者將通報記點，感謝高抬貴手(跪')
                     #   destination = {'user_id': info['uid']} if info['is_private'] else {'channel_id': _config['channel33']}
                    #    await send_msg(
                     #       **destination,
                     #       message=f'{time} : {name}的公主競技場排名發生變化：{last[1]}->{res[1]}，降低了{res[1]-last[1]}名。' +
                     #       ('' if info['is_private'] else at_person(user_id=user.replace("fake","")))
                     #   )     
            except:
                print(f'對{pcr_id}的檢查出錯\n{format_exc()}')

#on_arena_schedule.start()

@bot.command('watch')
async def change_arena_sub(ctx, arena_type, state, *args):
    uid = str(ctx.author.id)
    expire =  _binds[uid].get('expire', "1999-01-04")  
    expire  = datetime.strptime(str(expire),'%Y-%m-%d')
    if datetime.now() > expire :
        return await ctx.send('該為付費內容 請聯絡Bot管理員')
    if state not in ['on', 'off'] or arena_type not in ['11', '33']:
        return await ctx.send('參數錯誤')
    uid = str(ctx.author.id)
   # async with lck:
    if uid not in _binds:
        await ctx.send('您該為付費內容 請聯絡Bot管理員')
    else:
        _binds[uid][arena_type] = state == 'on'
        save_binds()
        await ctx.send(f'{arena_type} {state}')





@bot.command('add_role')
async def on_member_join(ctx, *args): 
    if len(args)==1:
        uid = str(args[0]).replace('<@','').replace('>','').replace('!','') 
    else:
        uid  =str(ctx.author.id) 
    pcr_id  = _binds[uid]['data'][0][1]
    res = await query(pcr_id, _clients['4'])
    member = await ctx.guild.fetch_member(uid)
    role1 = role_dict_11[str(res["arena_group"])]  # Role to be autoroled when user joins
    rank = discord.utils.get(member.guild.roles, name=role1) #Bot get guild(server) roles
    await member.add_roles(rank)
    #  await ctx.send(f'{member} 成功加入了{role}')
    role2 = role_dict_33[str(res["grand_arena_group"])]  # Role to be autoroled when user joins
    rank = discord.utils.get(member.guild.roles, name=role2) #Bot get guild(server) roles
    await member.add_roles(rank)
    await ctx.send(f'{member} 成功加入了{role1} {role2}')

'''@bot.command('add_roles')
async def on_member_join2(ctx): 
    role_dict_11 ={ "1" : "1v1 (１)" , 
    "2" : "1v1 (２)" , 
    "3" : "1v1 (３)" , 
    "4" : "1v1 (４)" , 
    "5" : "1v1 (５)" ,
    "6" : "1v1 (６)" ,
    "7" : "1v1 (７)" ,
    "8" : "1v1 (８)" ,
    "9" : "1v1 (９)" ,
    "10" : "1v1 (１０)" ,
    "11": "1v1 (11)", 
    "12": "1v1 (12)", 
    "13": "1v1 (13)", 
    "14": "1v1 (14)", 
    "15": "1v1 (15)", 
    }
    role_dict_33 ={ "1" : "3v3 (１)" , 
    "2" : "3v3 (２)" , 
    "3" : "3v3 (３)" , 
    "4" : "3v3 (４)" , 
    "5" : "3v3 (５)" ,
    "6" : "3v3 (６)" ,
    "7" : "3v3 (７)" ,
    "8" : "3v3 (８)" ,
    "9" : "3v3 (９)" ,
    "10" : "3v3 (１０)" ,
    }
    #uid  =str(ctx.author.id) 
    for every_uid in _binds.keys():
        pcr_id  = _binds[every_uid]['data'][0][1]
        res = await query(pcr_id, _clients['4'])
        member = await ctx.guild.fetch_member(every_uid.replace("fake",""))
        role1 = role_dict_11[str(res["arena_group"])]  # Role to be autoroled when user joins
        rank = discord.utils.get(member.guild.roles, name=role1) #Bot get guild(server) roles
        await member.add_roles(rank)
        role2 = role_dict_33[str(res["grand_arena_group"])]  # Role to be autoroled when user joins
        rank = discord.utils.get(member.guild.roles, name=role2) #Bot get guild(server) roles
        await member.add_roles(rank)
        await ctx.send(f'{member} 成功加入了{role1} {role2}') 
        '''

@bot.command('update_bindsrerewrewrew')
async def update_binds(ctx): 
    for every_uid in _binds.keys():
        pcr_id  = _binds[every_uid]['data'][0][1]
        res = await query(pcr_id, _clients['4'])
        _binds[every_uid] = {
                'uid': every_uid,
                'gid': ctx.channel.id,
                '11':  True ,
                '33': True ,
                'data': _binds[every_uid]['data'] ,
                'is_private': False ,
                '11_group' :   res["arena_group"]   ,
                '33_group' :   res["grand_arena_group"],
                '11_rank' :   res["arena_rank"]   ,
                '33_rank' :   res["grand_arena_rank"]
            }
        save_binds()

@bot.command(name='unset')
async def unset_channel(ctx, *args):
    async with lck:
        set_id = args[0]
        enemy_chanel.pop(set_id, None)
        save_enemy_chanel()
        msg = f'成功解除綁定'
        await ctx.send(str(msg)  )


@bot.command(name='here')
async def get_enemy_channel_infol(ctx, *args):
    try :
        here_channel_id = [k for k,v in enemy_chanel.items() if v['gid'] == ctx.channel.id]
        here_channel_id= here_channel_id[0]
        now = datetime.now()
        time = now.strftime("%H:%M:%S")
        res = await query(here_channel_id, _clients['4'])
        last_login = res['last_login_time']
        last_login = datetime.fromtimestamp(last_login).strftime("%B %d, %Y %H:%M:%S")
    #    msg.append(  f'''{res['user_name']}:\n競技場排名：{res["arena_rank"]}\n公主競技場排名：{res["grand_arena_rank"]} \n最後上線時間：{last_login}\n━━━━━━━━━━━━━━━'''  )
        await ctx.send(f'''{res['user_name']}\nID :{here_channel_id}\nTime:{time}\n競技場排名：{res["arena_rank"]}\n公主競技場排名：{res["grand_arena_rank"]} \n最後上線時間：{last_login}\n━━━━━━━━━━━━━━━''')
    except:
        await ctx.send(str('搜尋不到這頻道相應的玩家')  )  



@bot.command(name='set')
async def get_channel(ctx, *args):
    async with lck:
        uid = str(ctx.author.id)
        expire =  _binds[uid].get('expire', "1999-01-04")  
        expire  = datetime.strptime(str(expire),'%Y-%m-%d')
        if datetime.now() > expire :
            return await ctx.send('該為付費內容 請聯絡Bot管理員')
        set_id = args[0]
        try:
            res = await query(set_id, _clients['4'])
            channel = bot.get_channel(ctx.channel.id)
            if set_id in enemy_chanel :
                await ctx.send(str('該id已跟某channel鎖定')  )
            else:    
                enemy_chanel[set_id] = {
                    'name': res["user_name"],
                    'gid': ctx.channel.id,
                    "11": 0,
                    "33": 0,
                    "11_time": 0,
                    "33_time": 0
                }
                save_enemy_chanel()
                now_name  =res["user_name"]
                now_name = f"{now_name} 0 0"
                await channel.edit(name=now_name)
                msg = f'{res["user_name"]} 與channel {ctx.channel.id} 綁定成功'
                await ctx.send(str(msg)  )
        except :
            await ctx.send(str('沒有這玩家')  )        



@bot.command('private')
async def on_change_annonce(ctx, state):
    uid = str(ctx.author.id)
    await ctx.send('請向bot管理員申請')
    '''
    async with lck:
        if uid not in _binds:
            await ctx.send('您該為付費內容 請聯絡Bot管理員')
        else:
            _binds[uid]['is_private'] = state == 'on'
            save_binds()
            await ctx.send('send through {}'.format('private' if state == 'on' else 'channel'))
    pass'''

def save_binds():
    with open(_config['binds_file'], 'w') as f:
        json.dump(_binds, f, indent=4)

def save_enemy_chanel():
    with open(_config['enemy_chanel'], 'w') as f:
        json.dump(enemy_chanel, f, indent=4)

