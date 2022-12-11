import psycopg2


# DB_URL = "host='localhost' port = '5432' dbname='postgres' user='post' password='1234' "
# DB_URL = "host='postgres' port = '5432' database='privileges' user='program' password='test'"
# DB_URL = "postgresql://program:test@postgres:5432/privileges"
# password = "test"
# user = "program"
# dbname = "postgres"
# port = "5432"
# host = "postgres"
# database = "flight"

# password = "1234"
# user = "post"
# port = "5432"
# host = "localhost"
# database = "postgres"

class Privilegedb:
    def __init__(self):
        DB_URL = "postgresql://program:test@postgres:5432/privileges"
        self.db = psycopg2.connect(DB_URL)
        self.cursor = self.db.cursor()
        self.create_privilegedb()

    def __del__(self):
        self.disconect()

    def disconect(self):
        self.cursor.close()
        self.db.close()

    def create_privilegedb(self):
        self.cursor.execute("""
                        CREATE TABLE IF NOT EXISTS privilege
                        (
                            id       SERIAL PRIMARY KEY,
                            username VARCHAR(80) NOT NULL UNIQUE,
                            status   VARCHAR(80) NOT NULL DEFAULT 'BRONZE'
                            CHECK (status IN ('BRONZE', 'SILVER', 'GOLD')),
                            balance  INT
                        );
                       """)
        self.db.commit()
        self.cursor.execute("""
                        CREATE TABLE IF NOT EXISTS privilege_history
                        (
                            id             SERIAL PRIMARY KEY,
                            privilege_id   INT REFERENCES privilege (id),
                            ticket_uid     uuid        NOT NULL,
                            datetime       TIMESTAMP   NOT NULL,
                            balance_diff   INT         NOT NULL,
                            operation_type VARCHAR(20) NOT NULL
                            CHECK (operation_type IN ('FILL_IN_BALANCE', 'DEBIT_THE_ACCOUNT'))
                        );
                       """)
        self.db.commit()

        self.cursor.execute(f"SELECT privilege FROM privilege WHERE username = 'Test Max'")
        a = self.cursor.fetchone()
        if not a:
            self.cursor.execute(f"INSERT INTO privilege (id, username, status, balance) "
                                f"VALUES (DEFAULT, 'Test Max', DEFAULT, 150);")
            self.db.commit()
        return


    def get_base_privilege(self, user: str):
        self.cursor.execute(f"SELECT status, balance, id "
                       f"FROM privilege "
                       f"Where username = '{user}'")
        privilege = self.cursor.fetchone()
        self.db.commit()
        return privilege


    def get_all_privilege(self, user: str):
        self.cursor.execute(f"SELECT status, balance, id "
                       f"FROM privilege "
                       f"Where username = '{user}'")
        privilege = self.cursor.fetchone()
        self.cursor.execute(f"SELECT datetime, ticket_uid, balance_diff, operation_type FROM privilege_history "
                       f"WHERE privilege_id = '{privilege[2]}';")
        history = self.cursor.fetchall()
        self.db.commit()
        return privilege, history


    def minus_bonuses(self, req_pay: int, user: str, ticket_uid: str):
        self.cursor.execute(f"SELECT username FROM privilege WHERE username = '{user}';")
        username = self.cursor.fetchone()
        if not username:
            self.cursor.execute(f"INSERT INTO privilege (id, username, status, balance) "
                           f"VALUES (DEFAULT, '{user}', DEFAULT, 0);")
            self.db.commit()

        self.cursor.execute(f"SELECT balance, status, id FROM privilege WHERE username = '{user}';")
        status = self.cursor.fetchone()
        if req_pay >= status[0]:
            paid_money = req_pay - status[0]
            paid_bonus = status[0]
        else:
            paid_money = 0
            paid_bonus = req_pay

        bonuses_now = status[0] - paid_bonus
        self.cursor.execute(f"UPDATE privilege SET balance = {bonuses_now} WHERE username = '{user}';")
        self.db.commit()
        self.cursor.execute(
            f"INSERT INTO privilege_history (id, privilege_id, ticket_uid, datetime, balance_diff, operation_type) "
            f"VALUES (DEFAULT, '{status[2]}', '{ticket_uid}', LOCALTIMESTAMP, {paid_bonus}, 'DEBIT_THE_ACCOUNT')")
        self.db.commit()
        return [paid_money, paid_bonus, bonuses_now, status[1]]

    def back_bonuses(self, user: str, ticket_uid: str):
        self.cursor.execute(f"SELECT id, balance FROM privilege WHERE username = '{user}';")
        status = self.cursor.fetchone()
        old_balance = status[1]
        idd = status[0]
        self.cursor.execute(
            f"SELECT balance_diff, operation_type FROM privilege_history WHERE privilege_id = '{idd}' and ticket_uid = '{ticket_uid}';")
        status = self.cursor.fetchone()
        balance_diff = status[0]

        if status[1] == "DEBIT_THE_ACCOUNT":
            self.cursor.execute(
                f"INSERT INTO privilege_history (id, privilege_id, ticket_uid, datetime, balance_diff, operation_type)"
                f"VALUES (DEFAULT, '{idd}', '{ticket_uid}', LOCALTIMESTAMP, {balance_diff}, 'FILL_IN_BALANCE';")
            self.db.commit()
            new_balance = old_balance + balance_diff

        else:
            self.cursor.execute(
                f"INSERT INTO privilege_history (id, privilege_id, ticket_uid, datetime, balance_diff, operation_type)"
                f"VALUES (DEFAULT, '{idd}', '{ticket_uid}', LOCALTIMESTAMP, {balance_diff}, 'FILL_IN_BALANCE');")
            self.db.commit()
            new_balance = old_balance - balance_diff

        self.cursor.execute(f"UPDATE privilege SET balance = {new_balance} WHERE username = '{user}';")
        self.db.commit()
        return True

    def add_percent(self, added_bonuses: int, user: str, ticket: str):
        self.cursor.execute(f"SELECT username FROM privilege WHERE username = '{user}';")
        username = self.cursor.fetchone()
        if not username:
            self.cursor.execute(f"INSERT INTO privilege (id, username, status, balance) "
                           f"VALUES (DEFAULT, '{user}', DEFAULT, 0);")
            self.db.commit()

        self.cursor.execute(f"SELECT balance, status, id FROM privilege WHERE username = '{user}';")
        status = self.cursor.fetchone()
        new_balance = status[0] + added_bonuses

        self.cursor.execute(f"UPDATE privilege SET balance = {new_balance} WHERE username = '{user}';")
        self.db.commit()

        self.cursor.execute(
            f"INSERT INTO privilege_history (id, privilege_id, ticket_uid, datetime, balance_diff, operation_type)"
            f"VALUES (DEFAULT, '{status[2]}', '{ticket}', LOCALTIMESTAMP, {added_bonuses}, 'FILL_IN_BALANCE');")

        self.db.commit()
        return [new_balance, status[1]]
