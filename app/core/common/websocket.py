"""
WebSocket
"""

from core.common.mongo2 import MongodbController

from fastapi import WebSocket, WebSocketDisconnect
import json

import asyncio

DB = MongodbController('FIE_DB2')

class ConnectionManager:
    """ 연결된 Web, App Websocket들을 관리하는 클래스

        1. self.web_connections : Web 연결 정보 
            -> {websocket, s_id}
        2. self.app_connections : app 연결 정보 
            -> {websocket, h_id, orders[{o_id, s_id, status}]}
    """

    def __init__(self):
        self.web_connections = {}
        self.app_connections = {}

    async def connect(self, websocket: WebSocket, s_id: str|None, h_id: str|None):
        """ websocket 연결을 허용하고 s_id, history 입력값에 따라 web, app을 구분하여 저장한다. 
            - input : websocket, s_id, h_id
            - return : X
            1. s_id 입력시, web_connections에 저장
                - web_connections = {s_id : websocket}
            2. h_id 입력시, app_connections에 저장
                - app_connections = {h_id : {"ws" : websocket,
                                             "order" : {o_id : s_id, ... },
                                             "gaze" : bool
                                            } }
        """

        await websocket.accept()

        connected_data = {"type": "connect", "result": "connected"}
        failed_data = {"type": "connect", "result": "falied"}

        await self.check_connections(s_id, h_id)

        if s_id != None and h_id == None:

            if check_client_in_db('store', s_id) == False:
                await self.send_client_data(websocket, failed_data)
                raise WebSocketDisconnect(f'The ID is not exist.')
            
            self.web_connections[s_id] = websocket 
            await self.send_client_data(websocket, connected_data)

        elif  h_id != None and s_id == None:
            
            if check_client_in_db('history', h_id) == False:
                await self.send_client_data(websocket, failed_data)
                raise WebSocketDisconnect(f'The ID is not exist.')
            
            order_dict = {}
            history = DB.read_by_id('history', h_id)
            
            for o_id in history['orders']:
                order = DB.read_by_id('order', o_id)
                order_dict[o_id] = order['s_id']

            self.app_connections[h_id] = {
                                            "ws": websocket,
                                            "order": order_dict,
                                            "gaze": False
                                         }

            await self.send_client_data(websocket, connected_data)
            
            # app 연결 시, web에게 주문생성 전송
            await self.send_create(h_id)  
            # app 연결 시, app에게 gaze 요청
            await self.send_alarm_gaze(websocket, h_id)
            
        else:
            await self.send_client_data(websocket, {"type": "connect", "result": "closed"})
            raise WebSocketDisconnect(f'The connection is denied.')
        self.printList()

    async def disconnect(self, websocket:WebSocket, s_id:str, h_id:str):
        """ client(web or app)의 연결을 해지하고, connections list에서 해당 정보를 지운다.
            - input : client
            - return : X
        """
        await self.send_client_data(websocket, {"type": "connect", "result": "closed"})
        await websocket.close()
        await self.delete_connections(websocket, s_id, h_id)


    async def handle_message(self, websocket:WebSocket, s_id:str, h_id:str, data:json):
        """ client(web or app)으로부터 받은 msg에 따라 동작한다.
            - input : client, s_id, h_id, msg
                - 'type' : 'update_state' -> web이 주문 상태 변경, 전송 결과를 app에게 출력
                - 'type' : 'create_order' -> app이 주문 접수, 전송 결과를 web에게 출력
                - 'type' : 'connect' -> 연결 해지 또는 연결 확인
                - 그외 : 입력받은 문자열 그대로 출력
            - return : X
        """
        data = json.loads(data)

        if data['type'] == 'update_state':
            await self.send_update(data['o_id'])
      
        elif data['type'] == 'create_order':
            await self.send_create(data['h_id'])

        elif data['type'] == 'connect':
            if data['result'] == "close":
                data['result'] = 'closed'
                await self.disconnect(websocket, s_id, h_id)
                raise WebSocketDisconnect(f'The client requested to close the connection.')
            elif data['result'] == "connect":
                data['result'] = 'connected'
                await self.send_client_data(websocket, data)
        else:
            await self.send_client_data(websocket, data)

    async def send_client_data(self, websocket:WebSocket, data:json):
        """ client(web or app)에게 data를 전송한다.
            - input : client, data
            - return : X
            - send_error : {"type": "send_client", "result": "ERROR"}
        """
        await websocket.send_json(data)
        print(f"# Send : {data}")

    async def receive_client_data(self, websocket:WebSocket):
        """ client(web or app)로부터 data를 수신한다.
            - input : client
            - return : data
            - error_type : {"type": "recieve_client", "result": "ERROR"}
        """
        data = await websocket.receive_text()
        if json.dumps(data):
            print(f'# Receive : {data}')
            return data



    def printList(self):
        """ web_connections, app_connections 관리를 위해 현재 상태를 출력한다. """
        print(f'Web Conn : {self.web_connections}')
        print(f'App Conn : {self.app_connections}')



    async def check_connections(self, s_id, h_id):
        """ web_connections, app_connections의 요소들을 검사하여 존재하는 경우 disconnect() 함수를 호출한다.
            - input : websocket, s_id, h_id 
            - return : X
        """
        if s_id in self.web_connections:
            await self.disconnect(self.web_connections[s_id], s_id, h_id)
        if h_id in self.app_connections:
            await self.disconnect(self.app_connections[h_id]["ws"], s_id, h_id)
    
    async def delete_connections(self, websocket:WebSocket, s_id:str, h_id:str):
        """ web_connections, app_connections의 요소들을 검사하여 해당하는 websocket 정보를 삭제한다.
            - input : s_id, h_id
            - return : X
        """
        if s_id in self.web_connections and self.web_connections[s_id] == websocket:
            del self.web_connections[s_id]
        if h_id in self.app_connections and self.app_connections[h_id]["ws"] == websocket:
            del self.app_connections[h_id]

    async def get_app_websocekt(self, input_o_id: str) -> WebSocket:
        """ o_id를 가지는 websocket(app)를 반환한다.
            - input : o_id
            - return 
                - app이 연결되지 않은 경우 : False
                - app이 연결되어 있는 경우 : websocket
        """
        if self.app_connections == None:
            return False
        
        for h_value in self.app_connections.values():
            if input_o_id in h_value["order"]:
                return h_value["ws"]
        return False
                   
    async def get_web_websockets(self, input_h_id:str) -> dict:
        """ app_connections에서 h_id로 저장된 s_id를 찾아 web_connections에서 websocket(web)를 반환한다.
            - input : h_id
            - return
                - web이 연결되어 있는 경우 : {o_id : {s_id : websocket}}
                - web이 연결되지 않은 경우 : {o_id : {s_id : websocket}}
        """
        clients = {}
        if self.web_connections == None:
            return clients
        
        if input_h_id in self.app_connections:
            for o_id, s_id in self.app_connections[input_h_id]["order"].items():
                clients[o_id] = {s_id : ""}
        
        for o_id, o_value in clients.items():
            for s_id in o_value:
                if s_id in self.web_connections:
                    clients[o_id][s_id] = self.web_connections[s_id]
                
        return clients
                
    async def get_web_websocket(self, input_s_id: str) -> WebSocket:
        """ s_id의 websocket을 반환한다. (router/order.py 에서 store에게 전송 여부를 전송한다.)
            - input : s_id
            - return 
                - web이 연결되지 않은 경우 : False
                - web이 연결되어 있는 경우 : client{s_id, s_websocket}
        """
        if input_s_id in self.web_connections:
            return self.web_connections[input_s_id]
        else:
            False
        
            

    async def send_create(self, h_id:str):
        """ (POST order) app 생성한 주문을 web에게 알린다.
            - input : h_id
            - 전송 성공 
                - web : {"type": "create_order", "result": "success"}
                - app : result = {"type": "create_order", "result": "success"}
            - return : result(전송 여부 list)
        """
        result = {"type": "create_order", "result": "success"}
        web_clients = await self.get_web_websockets(h_id)

        if web_clients:
            for o_value in web_clients.values():
                for s_id, ws in o_value.items():
                    if ws != "":
                        await self.send_client_data(ws, result)
                        print({"type": "create_order", "result": "success", "reason": s_id})
                    else:
                        print({"type": "create_order", "result": "fali", "reason": f'web client({s_id}) is not connected'})
        else:
            print({"type": "create_order", "result": "fali", "reason": f'all web client is not connected'})

    
    async def send_update(self, o_id : str):
        """ (PUT order) web이 변경한 상태를 app에게 알린다.
            - input : o_id
            - 전송 성공 
                - app : {"type": "update_status", "result": "success", "o_id" : o_id, "status" : int}
                - web : {"type": "update_status", "result": "success"}
            - 전송 실패 
                - app :  {"type": "update_status", "result": "fail"}
            - return : data(전송 여부)
        """
        result = {"type": "update_status", "result": "success", "o_id" : o_id}
        app_client = await self.get_app_websocekt(o_id)

        if app_client:
            response = DB.read_by_id('order', o_id)
            status = response['status']
            if status < 3:
                result['status'] = status
                await self.send_client_data(app_client, result)
                print({"type": "update_status", "result": "success"})
            else:
                print({"type": "update_status", "result": "fail", "reason": "status is already finish"})
        else:
            print({"type": "update_status", "result": "fail", "reason": "app client is not connected"})


    async def send_alarm_gaze(self, websocekt : WebSocket, h_id : str):
        """ (POST order/gaze) app에게 gaze를 보내라고 알린다.
            - input : websocekt, websocekt
            - return : X
        """
        result = {"type": "request", "result": "gaze_omission"}
        history = DB.read_by_id('history', h_id)
        
        if history['gaze_path'] == None:
            while self.app_connections[h_id]['gaze'] != True:
                await asyncio.sleep(3)
                await self.send_client_data(websocekt, result)
                print(result)

        result["result"] = "gaze_success"
        await self.send_client_data(websocekt, result)
        print(result)



def check_client_in_db(db:str, id:str):
    try:
        if DB.read_by_id(db, id):
            return True
    except Exception:
        pass
    return False