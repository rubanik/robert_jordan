import psycopg as psycopg2

class Database:

    DB_NAME = 'RRP_FilterReceiverData'
    DB_USER = 'remote_user'
    DB_PASS = 'remote'
    DB_HOST = '10.143.253.45'
    DB_ALT = 'CSV'              # Альтернативная DB. На счучай сбоя в подключении.

    DB_CONNECTION_STR = f'dbname={DB_NAME} user={DB_USER} password={DB_PASS} host={DB_HOST}'

    def __init__(self):
        self.connected = False
        self.db_connection = self.connect()


    def connect(self):
        connection = psycopg2.connect(self.DB_CONNECTION_STR)
        self.connected = True
        print('DB CONNECTION IS OPEN')
        return connection
    
    @property # DELETE PROPERTY
    def cursor(self):
        return self.db_connection.cursor()

    def disconnect(self):
        self.db_connection.close()
        print('DB CONNECTION CLOSED')

    def send_query(self,query,data):
        if self.connected:
            self.cursor.execute(query,data) #TRY EXCEПТ
    
    def send_select_query(self,query):
        if self.connected:
            cur = self.cursor
            cur.execute(query) #TRY EXCEПТ
            return  cur.fetchall()
    
    
    def commit(self):
        self.db_connection.commit()
        self.cursor.close()

if __name__ == "__main__":
    db = Database()
    l = db.send_select_query('SELECT * from cl_list')
    print(l)
    db.disconnect()