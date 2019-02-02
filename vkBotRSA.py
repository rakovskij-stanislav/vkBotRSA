import requests
import json
import time
import random

# Vk group bot v 0.1 pre
#
# For Unicorns by RSA/reganel
# https://vk.com/dev/bots_docs

"""
Работает только с сообщениями
В случае другой активности может даже оповестить о том, что приходят события, отличные от сообщений


Todo:
Работа с входящими медиафайлами
Работа с исходящими медиафайлами
Красивые логи
"""

class vkRSA():
    def __init__(self, token, gID):
        # token - токен группы. Минимальное разрешение, необходимое для работы - разрешение на управление сообществом.
        #                       Для использования доп. функций нужны доп. разрешения
        # gID - id управляемой группы
        self._token, self._gID = token, gID
        self._firstRequest()
        self._decorators = {} # text : def
        
    def _unifRequest(self, method, parameters = {}, access_token="default", v="5.92"): 
        if access_token == "default":
            access_token = self._token
        _par = "&".join(['{}={}'.format(i, parameters[i]) for i in parameters.keys()])
        
        # https://api.vk.com/method/METHOD_NAME?PARAMETERS&access_token=ACCESS_TOKEN&v=V 
        r = requests.get("https://api.vk.com/method/{}?{}&access_token={}&v={}".format(method, _par, access_token, v))
        r = json.loads(r.text)
        if "error" in r:
            raise Exception("Exception in _unifRequest:\n"+str(r))
        return r

    def _firstRequest(self):
        r = self._unifRequest("groups.getLongPollServer", {"group_id":self._gID}, self._token)
        self._ts =     r['response']["ts"]
        self._server = r['response']["server"]
        self._key =    r['response']['key']

    
    def run(self, wait="default", conf=[]):
        if wait=='default':
            self.wait = 25
        else:
            self.wait = wait
        self.conf = conf
        onRunText = ["Сервер запущен.",
                    "Текущее время обновления - {} секунд (вк рекомендует 25)".format(wait),
                    "Текущий уровень конфигурации - {} (рекомендую [0, 2])".format(str(conf)),
                    "Допустимые значения конфигурации:",
                    "    0 - оповещать о задекларированных событиях",
                    "    1 - оповещать о незадекларированных событиях",
                    "    2 - оповещать об ошибках сервера",
                    "    3 - вызывать исключение при ошибке сервера",
                    "    4 - выводить сырой результат запроса a_check",
                    ]
        print("\n".join(onRunText))
        while True:
            r = requests.get("{server}?act=a_check&key={key}&ts={ts}&wait={wait}".format(
                server=self._server, key=self._key, ts=self._ts, wait=self.wait))
            ans = json.loads(r.text)
            
            if 4 in self.conf:
                print("[conf 4]", str(ans))
            
            ### Обработка исключений (https://vk.com/dev/bots_longpoll раздел 2.2)+ Обновляем ts
            
            if "failed" in ans:
                errorText = "Неизвестная ошибка. ПАНИКА!"
                if ans["failed"] in [1, "1"]:
                    errorText = "История событий устарела или была частично утеряна. Некритично"
                    self._ts = ans["ts"]
                    continue
                elif ans["failed"] in [2, "2"]:
                    errorText = "Истекло время действия ключа. Некритично"
                    _firstRequest()
                    #time.sleep(5)
                    continue
                elif ans["failed"] in [3, "3"]:
                    errorText = "Информация утрачена. Некритично"
                    _firstRequest()
                    #time.sleep(5)
                    continue
                else:
                    if 4 in self.conf:
                        raise Exception(errorText)
                if 3 in self.conf:
                        print("[conf 3]", errorText)
                        continue
            else:
                self._ts = ans["ts"]
                
            ### вызываем нужный декоратор
            for ev in ans["updates"]:
                if ev["type"]!='message_new':
                    if 1 in self.conf:
                        print("[conf 1]", ev)
                else:
                    obj = ev["object"]
                    print("obj", obj)
                    if 'text' in obj:
                        if obj['text'] in self._decorators:
                            rai = self._decorators[obj['text']] # raise event
                            what2answer = rai(obj) or "Мой хозяин не определил, что ответить"
                            self._unifRequest("messages.send", {"peer_id": obj["peer_id"], "message": what2answer, "random_id":random.randrange(0, 2**32)})
                        else:
                            # raise default message event
                            if None not in self._decorators:
                                print("[conf 1 important]. Не было создан дефолтный обработчик сообщений, поэтому это событие будет проигнорировано. ", ev)
                            else:
                                rai = self._decorators[None]
                                what2answer = rai(obj) or "Мой хозяин не определил, что ответить..."
                                self._unifRequest("messages.send", {"peer_id": obj["peer_id"], "message": what2answer, "random_id":random.randrange(0, 2**32)})
                    else:
                        raise Exception("Какой-то странный нетекст")
                             
            ### 

    def message_event(self, texts=[], **config):
            # декоратор передаст твоей функции такой словарь:
            """
    body = {'group_id': 177664328,
   'object': {'attachments': [],
    'conversation_message_id': 1,
    'date': 1549106733,
    'from_id': 169728041,
    'fwd_messages': [],
    'id': 1,
    'important': False,
    'is_hidden': False,
    'out': 0,
    'peer_id': 169728041,
    'random_id': 0,
    'text': '12'},
   'type': 'message_new'}
            """
            # также декоратор можно затриггерить на определенные фразы: @message_event(texts=("Хой", "Прив"))
            
            #сохраняем себя
            print("Добавляю триггер с текстами {}...".format(texts))
            def decorator(callback):
                for i in texts:
                    self._decorators.update({i:(callback)})
                if len(texts)==0:
                    self._decorators.update({None:(callback)})
                print("Успех!")
            return decorator

