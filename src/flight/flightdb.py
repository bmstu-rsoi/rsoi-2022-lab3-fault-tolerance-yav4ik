import psycopg2

# DB_URL = "host='localhost' port = '5432' dbname='postgres' user='post' password='1234'"
# DB_URL = "host='postgres' port = '5432' database='flights' user='program' password='test'"
# DB_URL = "postgresql://program:test@postgres:5432/flights"
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

class Flightdb:
    def __init__(self):
        DB_URL = "postgresql://program:test@postgres:5432/flights"
        self.db = psycopg2.connect(DB_URL)
        self.cursor = self.db.cursor()
        self.create_flightsdb()

    def __del__(self):
        self.disconect()

    def disconect(self):
        self.cursor.close()
        self.db.close()

    def create_flightsdb(self):
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS airport
                            (
                                id      SERIAL PRIMARY KEY,
                                name    VARCHAR(255),
                                city    VARCHAR(255),
                                country VARCHAR(255)
                            );
                               """)
        self.cursor.execute("""
                                CREATE TABLE IF NOT EXISTS flight
                                (
                                    id              SERIAL PRIMARY KEY,
                                    flight_number   VARCHAR(20)              NOT NULL,
                                    datetime        TIMESTAMP WITH TIME ZONE NOT NULL,
                                    from_airport_id INT REFERENCES airport (id),
                                    to_airport_id   INT REFERENCES airport (id),
                                    price           INT                      NOT NULL
                                );
                               """)
        self.db.commit()

        self.cursor.execute(f"SELECT name FROM airport WHERE name = 'Шереметьево'")
        a = self.cursor.fetchone()
        if not a:
            self.cursor.execute(f"INSERT INTO airport (id, name, city, country) "
                           f"VALUES (DEFAULT, 'Шереметьево', 'Москва', 'Россия');")
            self.db.commit()

        self.cursor.execute(f"SELECT name FROM airport WHERE name = 'Пулково'")
        a = self.cursor.fetchone()
        if not a:
            self.cursor.execute(f"INSERT INTO airport (id, name, city, country) "
                           f"VALUES (DEFAULT, 'Пулково', 'Санкт-Петербург', 'Россия');")
            self.db.commit()

        self.cursor.execute(f"SELECT flight FROM flight WHERE flight_number = 'AFL031'")
        a = self.cursor.fetchone()
        if not a:
            self.cursor.execute(f"INSERT INTO flight (id, flight_number, datetime, from_airport_id, to_airport_id, price) "
                           f"VALUES (DEFAULT, 'AFL031', timestamp '2021-10-08 20:00:00', 1, 2, 1500);")
            self.db.commit()
        return

    def get_flights(self, page: int, size: int):
        left = str(page * size - size)
        right = str(page * size)
        self.cursor.execute(f"""SELECT flight.flight_number, airport_from.city, airport_from.name, airport_to.city, 
                           airport_to.name, flight.datetime, flight.price 
                           FROM flight 
                           JOIN airport AS airport_from ON airport_from.id = flight.from_airport_id 
                           JOIN airport AS airport_to ON airport_to.id = flight.to_airport_id 
                           WHERE flight.id > {left} and flight.id <= {right};""")
        flights = self.cursor.fetchall()
        self.cursor.close()
        self.db.close()
        return flights

    def get_flights_bynum(self, flight_num: str):
        self.cursor.execute(f""" SELECT flight.flight_number, airport_from.city, airport_from.name, airport_to.city, 
                            airport_to.name, flight.datetime, flight.price 
                            FROM flight  
                            JOIN airport AS airport_from ON airport_from.id = flight.from_airport_id 
                            JOIN airport AS airport_to ON airport_to.id = flight.to_airport_id
                            WHERE flight.flight_number = '{flight_num}';""")
        flight = self.cursor.fetchone()
        self.cursor.close()
        self.db.close()
        return flight
