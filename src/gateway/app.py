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
        print("queue empty")
    else:
        status = 0
        n = 0
        while status != 200 or n == 10:
            req = requests.get(url=f"http://{privilege_ip}:8050/api/v1/health")
            status = req.status_code
            n += 1

        if status == 200:
            status_200 = True
            while not back_bonuses_queue.empty() and status_200:
                json_uid, user = back_bonuses_queue.get()
                req = requests.post(url=f"http://{privilege_ip}:8050/api/v1/back_bonuses", json=json_uid,
                                    headers={"X-User-Name": user})

                if req.status_code != 200:
                    back_bonuses_queue.put((json_uid, user))
                    status_200 = False

scheduler = BackgroundScheduler()
scheduler.add_job(func=task, trigger="interval", seconds=10)
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
    global flights_not_response

    flight_response = requests.get(url=f"http://{flights_ip}:8060/api/v1/flights?page={page}&size={size}")

    if flight_response.status_code == 200:
        return flight_response.json(), 200
    elif flight_response.status_code == 404:
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
    tickets_info = requests.get(url=f"http://{ticket_ip}:8070/api/v1/tickets/{user}")
    privilege_info = requests.get(url=f"http://{privilege_ip}:8050/api/v1/privilege/{user}")

    if tickets_info.status_code == 200 and privilege_info.status_code == 200:
        user_info = {
            "tickets": tickets_info.json(),
            "privilege": privilege_info.json()
        }
        return user_info, 200

    elif tickets_info.status_code != 200 and privilege_info != 200:
        if tickets_info.status_code == 404 and privilege_info == 404:
            return {}, 404
        return {}, 503

    elif tickets_info.status_code != 200:
        user_info = {
            "tickets": tickets_info.json(),
            "privilege": "fallback"
        }
        return user_info, 200

    elif tickets_info.status_code != 200:
        user_info = {
            "tickets": "fallback",
            "privilege": privilege_info.json()
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

    tickets_info = requests.get(url=f"http://{ticket_ip}:8070/api/v1/tickets/{user}")
    if tickets_info.status_code == 200:
        return tickets_info.json(), 200
    elif tickets_info.status_code == 404:
        return "не найдены билеты пользователя", 404
    else:
        return {}, 503


# Получить информацию о всех билетах пользователя
# X-User-Name: {{username}}
@app.route('/api/v1/tickets/<ticketUid>', methods=["GET"])
def get_ticket(ticketUid: str):
    user = request.headers
    user = user["X-User-Name"]
    ticket_info = requests.get(url=f"http://{ticket_ip}:8070/api/v1/tickets/{user}/{ticketUid}")
    if ticket_info.status_code == 200:
        return ticket_info.json(), 200
    else:
        return "не найдены билеты пользователя", 404


# Возврат билета
# X-User-Name: {{username}}
@app.route('/api/v1/tickets/<ticketUid>', methods=["DELETE"])
def delete_ticket(ticketUid: str):
    user = request.headers
    user = user["X-User-Name"]
    ticket_info = requests.delete(url=f"http://{ticket_ip}:8070/api/v1/tickets/{user}/{ticketUid}")
    if ticket_info.status_code != 200:
        if ticket_info.status_code == 404:
            return "Не найден билет", 404
        return {}, 503

    json_uid = {
        "ticketUid": ticketUid
    }
    status = requests.post(url=f"http://{privilege_ip}:8050/api/v1/back_bonuses", json=json_uid,
                           headers={"X-User-Name": user})
    if status.status_code != 200:
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

    flight_info = requests.get(url=f'http://{flights_ip}:8060/api/v1/flights/{json_req["flightNumber"]}')
    if flight_info.status_code != 200:
        if flight_info.status_code == 404:
            return "не найден рейс", 404
        else:
            return {}, 503

    json_flight = flight_info.json()

    ticket_info = requests.post(url=f"http://{ticket_ip}:8070/api/v1/tickets", json=json_req,
                                headers={"X-User-Name": user})
    if ticket_info.status_code != 200:
        if ticket_info.status_code == 400:
            return "Ошибка валидации данных", 400
        else:
            return {}, 503
    json_ticket = ticket_info.json()

    priv_json_send = {
        "paidFromBalance": json_req["paidFromBalance"],
        "ticketUid": json_ticket["ticketUid"],
        "price": json_req["price"]
    }

    privil_info = requests.post(url=f"http://{privilege_ip}:8050/api/v1/buy", json=priv_json_send,
                                headers={"X-User-Name": user})
    if privil_info.status_code != 200:
        requests.delete(f'http://{ticket_ip}:8070/api/v1/tickets/delete/<user_login>/<ticketUid>')
        return {}, 503

    json_privil = privil_info.json()

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
    privilege_info = requests.get(url=f"http://{privilege_ip}:8050/api/v1/privileges/{user}")
    if privilege_info.status_code == 200:
        return privilege_info.json(), 200
    elif privilege_info == 404:
        return "Привелегии не найдены", 404
    else:
        return {}, 503


@app.route(f"/api/v1/flights/<ticketUid>", methods=["GET"])
def get_flight_byticket(ticketUid: str):
    req = requests.get(f"http://{flights_ip}:8060/api/v1/flights/{ticketUid}")
    return req.json(), 200

if __name__ == '__main__':
    app.run(port=8080, debug=True)
    atexit.register(lambda: scheduler.shutdown())
