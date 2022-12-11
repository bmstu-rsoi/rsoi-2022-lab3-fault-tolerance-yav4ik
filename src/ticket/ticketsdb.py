import psycopg2

# DB_URL = "host='localhost' port = '5432' dbname='postgres' user='post' password='1234' "
# DB_URL = "host='postgres' port = '5432' database='tickets' user='program' password='test'"
# DB_URL = "postgresql://program:test@postgres:5432/tickets"
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


class Ticketsdb:
    def __init__(self):
        DB_URL = "postgresql://program:test@postgres:5432/tickets"
        self.db = psycopg2.connect(DB_URL)
        self.cursor = self.db.cursor()
        self.create_ticketsdb()

    def __del__(self):
        self.disconect()

    def disconect(self):
        self.cursor.close()
        self.db.close()

    def create_ticketsdb(self):
        self.cursor.execute("""
                        CREATE TABLE IF NOT EXISTS ticket
                        (
                        id            SERIAL PRIMARY KEY,
                        ticket_uid    uuid UNIQUE NOT NULL,
                        username      VARCHAR(80) NOT NULL,
                        flight_number VARCHAR(20) NOT NULL,
                        price         INT         NOT NULL,
                        status        VARCHAR(20) NOT NULL
                            CHECK (status IN ('PAID', 'CANCELED'))
                        );
                       """)
        self.db.commit()
        return

    def get_user_flight(self, user: str):
        self.cursor.execute(f"""SELECT ticket_uid, flight_number, price, status
                           FROM ticket 
                           WHERE ticket.username = '{user}';""")
        flight = self.cursor.fetchall()
        return flight

    def get_one_flight(self, ticketUid: str, user: str):
        self.cursor.execute(f"""SELECT ticket_uid, flight_number, price, status 
                           FROM ticket  
                           WHERE ticket_uid = '{ticketUid}' and username = '{user}';""")
        flight = self.cursor.fetchone()
        return flight

    def add_ticker(self, ticketUid: str, user: str, flight_number: str, price: str):
        self.cursor.execute(f"INSERT INTO ticket (id, ticket_uid, username, flight_number, price, status) "
                            f"VALUES (DEFAULT, '{ticketUid}', '{user}', '{flight_number}', {price}, 'PAID');")
        self.db.commit()
        return True

    def change_ticker_status(self, ticketUid: str, user: str):
        self.cursor.execute(
            f"""UPDATE ticket SET status = 'CANCELED' WHERE ticket_uid = '{ticketUid}' and username = '{user}';""")
        self.db.commit()
        return True

    def delete_ticker_status(self, ticketUid: str, user: str):
        self.cursor.execute(f"DELETE FROM ticket WHERE ticket_uid = '{ticketUid}' and username = '{user}';")
        self.db.commit()
        return True
