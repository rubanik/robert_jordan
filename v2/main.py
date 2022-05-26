import datetime
import pyads
import psycopg2


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
        db.send_select_query('SELECT * from cl_list')
        db.disconnect()


class DataInit:
    """Класс в котором мы через запрос к ДБ получаем список контролируемых параметров"""

    RAW_DATA = None # Data collected after SQL request
    CL_LIST_FROM_DB = [] # It's the result. List with dictionaries with a cl inside. 
    DATA_INIT_QUERY = 'SELECT cl_type_id,cl_equip_group_id,cl_name,cl_setpoint,cl_plc_path,cl_data_type FROM cl_list' # SQL query for pulling cl_list from the CL_LIST table.
    DATA_STRUCTURE = ('cl_type_id', 'cl_equip_group_id', 'cl_name', 'cl_setpoint','cl_plc_path','cl_data_type') # TODO: GET DATA STRUCTURE()

    def __init__(self,db=None):
        """При инициировании вытягиваем данные из таблицы. Если в конструктор не передать дб ничего не получится"""
        self.db = db
        self.start_it()


    @property
    def cl_list(self):
        """ Метод, возвращающий подготовленный для создания объекта Center Line список со словарями""" # TODO: Изменить описание.
        if len(self.CL_LIST_FROM_DB) > 0:
            return self.CL_LIST_FROM_DB
        else:
            return self.generate_cl_list()
    
    def start_it(self):
        try:
            self._get_cl_list_() # Get the data.
        except FileNotFoundError:
            print('Тут что то не так с подключением к db')
        except Exception as e:
            print(e)


    def _get_cl_list_(self):
        if self.db:
            self.RAW_DATA = self.db.send_select_query(self.DATA_INIT_QUERY)
        else:
            raise FileNotFoundError
    
    def generate_cl_list(self):
        if self.RAW_DATA:
            for data in self.RAW_DATA:
                data_dict = dict(zip(self.DATA_STRUCTURE, data))
                self.CL_LIST_FROM_DB.append(data_dict)
            return self.CL_LIST_FROM_DB    


class Plc:
    def __init__(self,address,port,name='Unnamed'):
        self.address = address
        self.port = port
        self.plc_connection = self.connect()
        self._open_connection()
        self.test_state = False

    def connect(self):
        return pyads.Connection(self.address, self.port)
    
    def _open_connection(self):
        if self.plc_connection:
            self.plc_connection.open()
            print('PLC CONNECTION IS OPEN')

    def close_connection(self):
        if self.plc_connection.is_open:
            self.plc_connection.close()
            print('PLC CONNECTION IS CLOSE')
    
    def read_by_name(self,path,name):
        return self.plc_connection.read_by_name(path,name)
  

class Variable:

    def __init__(self,path,var_type,plc,
                name='',ctrl_type = 'state', test = None):
        self.path = path
        self.name = name if name else path
        self.var_type = var_type
        self.plc = plc
        self.test = test

    @property
    def value(self):
        if self.test == True:
            return self.test
        else: 
            return self.plc.read_by_name(self.path,self.var_type)# read from plc


class StateControler:

    QUERY = 'BASIC_QUERY'

    def __init__(self,var):
        self.var = var
        self.prev_state = self.var.value

    @property
    def change_detected(self):
        return self.var.value != self.prev_state


    def set_previous_state(self):
        self.prev_state = self.var.value

    def check_state(self):
        
        if self.change_detected:
            print('State is changed')
            self.execute_query()
            self.set_previous_state()

    def get_data(self):
        return 'Some DATA'

    def execute_query(self):
        if self.var.test:    
            db_execute(self.QUERY, self.get_data())
        else:
            database.send_query(self.QUERY, self.get_data())


class SwitchControl(StateControler):
    """
    Наследник StateController.  Описывает поведение переменной "переключатель".
    Фиксирует изменение состояния Bool переменной. Идёт фиксация времени и состояние.
    """

    QUERY = 'SWITCH_QUERY'

    last_change_time = ''

    @property
    def time_of_switch(self):
        """ Фиксация времени изменения переменной """
        return datetime.datetime.now()

    def get_data(self):
        name = self.var.name
        value = self.var.value
        timest = self.time_of_switch

        return (name,timest,value)


class SwitchEventControl(StateControler):
    
    QUERY = '''INSERT INTO process_flow_log
                    (
                        start_date, 
                        finish_date, 
                        event_duration, 
                        variable, 
                        user_name
                    )
                    VALUES (%s, %s, %s, %s, %s)'''


    def __init__(self, var, good_state ,condition=None):
        StateControler.__init__(self,var)
        self.condition = condition
        self.start_time = ''
        self.finish_time = ''
        self.flag = False
        self.good_state = good_state
        
    @property
    def change_detected(self):
        return self.var.value != self.good_state

    
    @property
    def duration(self):
        """ Возвращает длительность события - Tfinish - Tstart """
        duration = self.finish_time - self.start_time
        return duration.seconds


    def _set_time(self):
        if self.start_time:
            self.finish_time = datetime.datetime.now()
        else:
            self.start_time = datetime.datetime.now()


    def _set_flag(self):
        self.flag = not self.flag
        print(self.flag)


    def check_state(self):
        changes = self.change_detected 
        if not changes and self.flag:
            print('Завершаем Событие')
            self.finish_event()
            self._set_flag()
            self.execute_query()
        if changes and self.flag != True:
            print('Начинаем Событие')
            self.start_event()
            self._set_flag()


    def get_data(self):
        return (self.start_time,
                self.finish_time,
                self.duration,
                self.var.name,
                'PLACE_FOR_CONDITION')

    def start_event(self):
            self._set_time()

    def finish_event(self):
            self._set_time()