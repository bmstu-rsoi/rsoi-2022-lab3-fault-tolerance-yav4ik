from privilegedb import Privilegedb
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

@app.route('/manage/health', methods=["GET"])
def health():
    return {}, 200

@app.route('/api/v1/privilege/<user>', methods=["GET"])
def get_base_privilege(user: str):
    privilegedb = Privilegedb()
    privilege = privilegedb.get_base_privilege(user)
    if privilege:
        json_privilege = {
            "balance": privilege[1],
            "status": privilege[0]
        }
        return json_privilege, 200
    else:
        return 404

@app.route('/api/v1/privileges/<user>', methods=["GET"])
def get_all_privilege(user: str):
    print(user)
    privilegedb = Privilegedb()
    privilege, history = privilegedb.get_all_privilege(user)
    print(privilege)
    if privilege:
        json_history = []
        if history:
            for i in history:
                histor = {
                    "date": i[0],
                    "ticketUid": i[1],
                    "balanceDiff": i[2],
                    "operationType": i[3]
                }
                json_history.append(histor)

        json_privilege = {
            "balance": privilege[1],
            "status": privilege[0],
            "history": json_history
        }
        return json_privilege, 200
    else:
        return {}, 404


@app.route("/api/v1/buy", methods=["POST"])
def minus_bonuses():
    privilegedb = Privilegedb()
    user = request.headers
    user = user["X-User-Name"]
    json_buy = request.json

    if not json_buy["paidFromBalance"]:
        prvilege = privilegedb.add_percent(int(json_buy["price"] * 0.1), user, json_buy["ticketUid"])
        json_privil = {
            "paidByMoney": json_buy["price"],
            "paidByBonuses": 0,
            "balance": prvilege[0],
            "status": prvilege[1]
        }

    else:
        privil = privilegedb.minus_bonuses(json_buy["price"], user, json_buy["ticketUid"])
        json_privil = {
                "paidByMoney": privil[0],
                "paidByBonuses": privil[1],
                "balance": privil[2],
                "status": privil[3]
        }
    return json_privil, 200


@app.route("/api/v1/back_bonuses", methods=["POST"])
def back_bonuses():
    privilegedb = Privilegedb()
    user = request.headers
    user = user["X-User-Name"]
    json_buy = request.json

    isdone = privilegedb.back_bonuses(user, json_buy["ticketUid"])
    if isdone:
        return {}, 200
    else:
        return {}, 400


if __name__ == '__main__':
    app.run(port=8050)

