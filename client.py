import requests

user_id=-1
user_pass=-1

def make_req(url):
    resp = requests.get(url)
    if not resp.ok:
        print("Ой, сервер принял удар и упал, новых юморесок не будет")
        return None
    resp=resp.json()
    if resp['state'] == 'error':
        print(resp['data'])
        return None
    return resp['data']

def auth():
    global user_pass
    user_pass = input("Введите пароль: ")
    resp=make_req(f"http://localhost:8000/auth?user_id={user_id}&user_pass={user_pass}")
    return bool(resp)

print("Добро пожаловать в ленту мемов!")
print("Для регистрации введите id=-1")
user_id = input("Введите id: ")
if user_id != "-1":
    if not auth():
        exit(0)
    print("С возвращением!")
else:
    resp={'valid': False, 'msg': ""}
    while not resp['valid']:
        print(resp['msg'])
        user_id = input("Придумайте новый id(число): ")
        user_pass = input("Придумайте новый пароль(число): ")
        resp = make_req(f"http://localhost:8000/reg_user?user_id={user_id}&user_pass={user_pass}")
        if not resp: exit(0)
    print("Вы успешно зарегестрировались!")

print("===============")
i=1
while True:
    mem = make_req(f"http://localhost:8000/get_mem?user_id={user_id}&user_pass={user_pass}")
    if not mem: break
    print("Юмореска " + str(i)+":")
    print("лайки: " + str(mem['likes']['count']))
    print("автор: " + mem['author']['first_name'] + " " + mem['author']['last_name'])
    print("ссылка на автора: https://vk.com/id"+ str(mem['author']['id']))
    print("ссылка на юмореску: "+ str(mem['sizes'][-1]['url']))
    print("====")
    invite_text = "лайк/скип/выход/дальше(+/-/0/enter): "
    action = input(invite_text)
    while  action not in ["+", "-", "0", ""]:
        print("Увы, ввод некорректен")
        next = input(invite_text)
    print("==========\n")
    if action == "+" or action == "-":
        method = "like_mem" if action == "+" else "skip_mem"
        resp = make_req(f"http://localhost:8000/{method}?mem_id={mem['id']}&user_id={user_id}&user_pass={user_pass}")
        if not resp: break
        print("Лайк поставлен!\n" if action == "+" else "Шутка была удалена\n")
    elif action == "0":
        break
    i+=1

print("Приходите еще!")