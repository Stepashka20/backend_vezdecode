import requests
import uvicorn
from fastapi import FastAPI
import json

app = FastAPI()
global access_token_vk, vk_api_version
global mem_album, user_stat
global memes_from_file
@app.on_event('startup')
def start():
    global mem_album, memes_from_file
    global access_token_vk, vk_api_version
    access_token_vk = "insert_vk_access_token_here"
    vk_api_version = "5.131"
    memes_from_file = False
    init()


@app.get("/reg_user")
async def reg_user(user_id: str, user_pass: str):
    global user_stat
    msg=""
    if user_id in user_stat: 
        msg="id занят, попробуйте другой"
    elif not user_id.isdigit():
        msg="id должно быть целым положительным числом"
    elif len(user_id) > 20:
        msg="id слишком длинный, попробуйте другой"
    elif not user_pass.isdigit():
        msg="пароль должен быть целым положительным числом"
    elif len(user_pass) > 20:
        msg="пароль слишком длинный, попробуйте другой"
    if not msg:
        user_stat[user_id] = {
            'cur_mem': 0,
            'pass': user_pass,
            'like': [],
            'skip': [],
        }
        with open("stat.json", "w") as write_file:
            json.dump(user_stat, write_file, indent=2)
    return {'state':'ok','data': {'valid': not bool(msg), 'msg':msg}} 

@app.get("/auth")
async def auth(user_id: str, user_pass: str):
    global user_stat
    if user_id in user_stat and user_stat[user_id]['pass'] == user_pass:
        return {'state':'ok','data': 'данные верны'}
    return {'state':'error','data': 'Ваш id или пароль неверные'}
 

@app.get("/get_mem")
async def get_mem(user_id: str, user_pass: str):
    auth_resp = await auth(user_id,user_pass)
    if auth_resp['state'] == 'error':
        return auth_resp
    global user_stat
    cur_mem=user_stat[user_id]['cur_mem']
    while cur_mem < len(mem_album) and mem_album[cur_mem]['id'] in user_stat[user_id]['skip']:
        cur_mem+=1
    if cur_mem < len(mem_album):
        mem = mem_album[cur_mem]
        user_stat[user_id]['cur_mem'] = cur_mem+1
        with open("stat.json", "w") as write_file:
            json.dump(user_stat, write_file, indent=2)
        return {'state':'ok','data': mem} 
    else:
        return {'state':'error','data': "шутки кончились, пора отдыхать"} 

@app.get("/like_mem")
async def like_mem(mem_id: int, user_id: str, user_pass: str):
    auth_resp = await auth(user_id,user_pass)
    if auth_resp['state'] == 'error':
        return auth_resp
    global user_stat
    if mem_id not in user_stat[user_id]['like']:
        user_stat[user_id]['like'].append(mem_id)
        with open("stat.json", "w") as write_file:
            json.dump(user_stat, write_file, indent=2)
    return {'state':'ok','data': "ok"} 

@app.get("/skip_mem")
async def skip_mem(mem_id: int, user_id: str, user_pass: str):
    auth_resp = await auth(user_id,user_pass)
    if auth_resp['state'] == 'error':
        return auth_resp
    global user_stat
    if mem_id not in user_stat[user_id]['skip']:
        user_stat[user_id]['skip'].append(mem_id)
        with open("stat.json", "w") as write_file:
            json.dump(user_stat, write_file, indent=2)
    return {'state':'ok','data': "ok"} 


# return {'state','data'} 
def vk_req_json(method, p):
    global mem_album, access_token_vk, vk_api_version
    p['v']=vk_api_version
    p['access_token'] = access_token_vk
    resp = requests.get(
        f'https://api.vk.com/method/{method}',
        params=p
    ).json()
    if 'response' in resp:
        return {'state':'ok','data': resp['response']} 
    else:
        return {'state':'error','data': resp['error']}

def download_mems():
    global mem_album
    resp = vk_req_json("photos.get", {
        "owner_id": "-197700721",
        "album_id": "283939598",
    })
    if resp['state'] == 'error':
        print(resp['data']['error_msg'])
        exit(0)
        
    mem_count = resp['data']['count']

    resp = vk_req_json("photos.get", {
            "owner_id": "-197700721",
            "album_id": "283939598",
            "extended": "1",
            "offset": 0,
            "count": mem_count,
        })
    if resp['state'] == 'error':
        print(resp['data']['error_msg'])
        exit(0)

    mem_album=resp['data']['items']
    user_ids = [str(mem['user_id']) for mem in mem_album]

    resp = vk_req_json("users.get", {
        "user_ids": ",".join(user_ids)
        })
    if resp['state'] == 'error':
            print(resp['data']['error_msg'])
            exit(0)

    users_info={}
    for user in resp['data']:
        users_info[str(user['id'])] = {
            'first_name': user['first_name'],
            'last_name': user['last_name']
        }

    for mem in mem_album:
        id=mem.pop('user_id', None)
        mem['author'] = {
            'id': id,
            'first_name': users_info[str(id)]['first_name'],
            'last_name': users_info[str(id)]['last_name']
        }
    
    with open("memes.json", "w") as write_file:
        json.dump(mem_album, write_file, indent=2)
    return mem_album


def init():
    global mem_album, user_stat
    with open("stat.json", "r") as read_file:
        user_stat = json.load(read_file)
    if memes_from_file:
        with open("memes.json", "r") as read_file:
            mem_album = json.load(read_file)
    else:
        mem_album = download_mems()

if __name__ == '__main__':
    uvicorn.run('server:app', host='0.0.0.0', port=8000)

