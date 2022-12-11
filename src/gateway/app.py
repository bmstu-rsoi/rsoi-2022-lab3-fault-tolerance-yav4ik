import requests
import time
import atexit

from multiprocessing import Queue
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)
back_bonuses_queue = Queue()


def task():
    if back_bonuses_queue.empty():
        pass
    else:
        status = 503
        n = 0
        while not (status == 200 or n == 1):
            try:
                req = requests.get(url=f"http://{privilege_ip}:8050/manage/health")
                status = req.status_code
            except:
                n += 1

        if status == 200:
            while not back_bonuses_queue.empty() and status == 200:
                json_uid, user = back_bonuses_queue.get()
                status = 0
                try:
                    req = requests.post(url=f"http://{privilege_ip}:8050/api/v1/back_bonuses", json=json_uid,
                                        headers={"X-User-Name": user})
                    status = req.status_code
                except:
                    pass

                if status != 200:
                    back_bonuses_queue.put((json_uid, user))


scheduler = BackgroundScheduler()
scheduler.add_job(func=task, trigger="interval", seconds=10, max_instances=10)
scheduler.start()

# ports
# gateway 8080
# flights 8060
# privilege 8050
# ticket 8070

flights_ip = "flight"
privilege_ip = "privilege"
ticket_ip = "ticket"

# flights_ip = "localhost"
# privilege_ip = "localhost"
# ticket_ip = "localhost"


# Получить список всех перелетов
@app.route('/manage/health', methods=["GET"])
def health():
    return {}, 200


@app.route('/api/v1/flights', methods=["GET"])
def get_flights():
    page = request.args.get("page")
    size = request.args.get("size")

    flight_status = 503
    json_flight = {}
    try:
        flight_response = requests.get(url=f"http://{flights_ip}:8060/api/v1/flights?page={page}&size={size}")
        flight_status = flight_response.status_code
        json_flight = flight_response.json()
    except:
        pass

    if flight_status == 200:
        return json_flight, 200
    elif flight_status == 404:
        return "не найдены полеты", 404
    else:
        return {}, 503


# Получить полную информацию о пользователе
# Возвращается информация о билетах и статусе в системе привилегии.
# X-User-Name: {{username}}
@app.route('/api/v1/me', methods=["GET"])
def get_person():
    user = request.headers
    user = user["X-User-Name"]
    ticket_status = 503
    privilege_status = 503
    json_ticket = {}
    json_privilege = {}
    try:
        tickets_info = requests.get(url=f"http://{ticket_ip}:8070/api/v1/tickets/{user}")
        ticket_status = tickets_info.status_code
        json_ticket = tickets_info.json()
    except:
        pass

    try:
        privilege_info = requests.get(url=f"http://{privilege_ip}:8050/api/v1/privilege/{user}")
        privilege_status = privilege_info.status_code
        json_privilege = privilege_info.json()
    except:
        pass

    if ticket_status == 200 and privilege_status == 200:
        user_info = {
            "tickets": json_ticket,
            "privilege": json_privilege
        }
        return user_info, 200

    elif ticket_status != 200 and privilege_status != 200:
        if ticket_status == 404 and privilege_status == 404:
            return {}, 404
        return {}, 503

    elif ticket_status != 200:
        user_info = {
            "tickets": json_ticket,
            "privilege": []
        }
        return user_info, 200

    elif privilege_status != 200:
        user_info = {
            "tickets": [],
            "privilege": json_privilege
        }
        return user_info, 200
    else:
        return {}, 503


# Получить информацию о всех билетах пользователя
# X-User-Name: {{username}}
@app.route('/api/v1/tickets', methods=["GET"])
def get_tickets():
    user = request.headers
    user = user["X-User-Name"]
    ticket_status = 0
    json_ticket = {}
    try:
        tickets_info = requests.get(url=f"http://{ticket_ip}:8070/api/v1/tickets/{user}")
        ticket_status = tickets_info.status_code
        json_ticket = tickets_info.json()
    except:
        pass

    if ticket_status == 200:
        return json_ticket, 200
    elif ticket_status == 404:
        return "не найдены билеты пользователя", 404
    else:
        return {}, 503


# Получить информацию о всех билетах пользователя
# X-User-Name: {{username}}
@app.route('/api/v1/tickets/<ticketUid>', methods=["GET"])
def get_ticket(ticketUid: str):
    user = request.headers
    user = user["X-User-Name"]
    ticket_status = 503
    json_ticket = {}
    try:
        ticket_info = requests.get(url=f"http://{ticket_ip}:8070/api/v1/tickets/{user}/{ticketUid}")
        ticket_status = ticket_info.status_code
        json_ticket = ticket_info.json()
    except:
        pass

    if ticket_status == 200:
        return json_ticket, 200
    else:
        return "не найдены билеты пользователя", 404


# Возврат билета
# X-User-Name: {{username}}
@app.route('/api/v1/tickets/<ticketUid>', methods=["DELETE"])
def delete_ticket(ticketUid: str):
    user = request.headers
    user = user["X-User-Name"]

    ticket_status = 503
    json_ticket = {}
    try:
        ticket_info = requests.delete(url=f"http://{ticket_ip}:8070/api/v1/tickets/{user}/{ticketUid}")
        ticket_status = ticket_info.status_code
        json_ticket = ticket_info.json()
    except:
        pass

    if ticket_status != 200:
        if json_ticket == 404:
            return "Не найден билет", 404
        return {}, 503

    json_uid = {
        "ticketUid": ticketUid
    }
    status_code = 0
    try:
        status = requests.post(url=f"http://{privilege_ip}:8050/api/v1/back_bonuses", json=json_uid,
                               headers={"X-User-Name": user})
        status_code = status.status_code
    except:
        pass

    if status_code != 200:
        back_bonuses_queue.put((json_uid, user))
        return "Не найдена программа боунусов, билет возвращен", 204
    return "Билет успешно возвращен", 204


# Покупка билета
# POST {{baseUrl}}/api/v1/tickets
# Content-Type: application/json
# X-User-Name: {{username}}
#
# {
#   "flightNumber": "AFL031",
#   "price": 1500,
#   "paidFromBalance": true
# }
@app.route('/api/v1/tickets', methods=["POST"])
def post_ticket():
    # проверка существования рейса (flightNumber), если флаг привелегий установлен то списываем привелегии
    # если нет то добавляем 10 процентов от стоимости билета
    user = request.headers
    user = user["X-User-Name"]
    json_req = request.json

    status_flight = 503
    json_flight = {}
    try:
        flight_info = requests.get(url=f'http://{flights_ip}:8060/api/v1/flights/{json_req["flightNumber"]}')
        status_flight = flight_info.status_code
        json_flight = flight_info.json()
    except:
        pass

    if status_flight != 200:
        if status_flight == 404:
            return "не найден рейс", 404
        else:
            return {}, 503

    json_flight = json_flight

    status_ticket = 503
    json_ticket = {}
    try:
        ticket_info = requests.post(url=f"http://{ticket_ip}:8070/api/v1/tickets", json=json_req,
                                    headers={"X-User-Name": user})
        status_ticket = ticket_info.status_code
        json_ticket = ticket_info.json()
    except:
        pass

    if status_ticket != 200:
        if status_ticket == 400:
            return "Ошибка валидации данных", 400
        else:
            # "Bonus Service unavailable"
            return {"message": "Bonus Service unavailable"}, 503
    json_ticket = json_ticket

    priv_json_send = {
        "paidFromBalance": json_req["paidFromBalance"],
        "ticketUid": json_ticket["ticketUid"],
        "price": json_req["price"]
    }

    status_privil = 503
    json_privil = {}
    try:
        privil_info = requests.post(url=f"http://{privilege_ip}:8050/api/v1/buy", json=priv_json_send,
                                    headers={"X-User-Name": user})
        status_privil = privil_info.status_code
        json_privil = privil_info.json()
    except:
        pass

    if status_privil != 200:
        print(2)
        requests.delete(f'http://{ticket_ip}:8070/api/v1/tickets/delete/{user}/{json_ticket["ticketUid"]}')
        return {"message": "Bonus Service unavailable"}, 503

    json_privil = json_privil

    json_out = {
        "ticketUid": json_ticket["ticketUid"],
        "flightNumber": json_req["flightNumber"],
        "fromAirport": json_flight["fromAirport"],
        "toAirport": json_flight["toAirport"],
        "date": json_flight["date"],
        "price": json_req["price"],
        "paidByBonuses": json_privil["paidByBonuses"],
        "paidByMoney": json_privil["paidByMoney"],
        "status": json_ticket["status"],
        "privilege": {
            "balance": json_privil["balance"],
            "status": json_privil["status"]
        }
    }

    return json_out, 200

    # return app.redirect(location=f'{request.host_url}api/v1/persons/{int(person_id)}', code=201)


# Получить информацию о состоянии бонусного счета
# X-User-Name: {{username}}
@app.route('/api/v1/privilege', methods=["GET"])
def get_privilege():
    user = request.headers
    user = user["X-User-Name"]

    status_privilege = 503
    json_privilege = {}
    try:
        privilege_info = requests.get(url=f"http://{privilege_ip}:8050/api/v1/privileges/{user}")
        status_privilege = privilege_info.status_code
        json_privilege = privilege_info.json()
    except:
        pass


    if status_privilege == 200:
        return json_privilege, 200
    elif status_privilege == 404:
        return "Привелегии не найдены", 404
    else:
        # Bonus Service unavailable
        return {"message": "Bonus Service unavailable"}, 503


@app.route(f"/api/v1/flights/<ticketUid>", methods=["GET"])
def get_flight_byticket(ticketUid: str):
    status_req = 503
    status_json = {}
    try:
        req = requests.get(f"http://{flights_ip}:8060/api/v1/flights/{ticketUid}")
        status_req = req.status_code
        status_json = req.json()
    except:
        pass

    return status_json, status_req


if __name__ == '__main__':
    app.run(port=8080, debug=False)
    atexit.register(lambda: scheduler.shutdown())
