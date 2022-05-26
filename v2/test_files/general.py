import datetime
import pyads
import psycopg2 #as psycopg2

import test_db
import test_init

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
            
if __name__ == "__main__":

    db = test_db.Database() # инициируем базу данных
    
    param_dict = test_init.DataInit(db).generate_cl_list() # достаём данные {} из таблицы cl_list
    print(*param_dict,sep="\n")
    
    plc = Plc('192.168.1.177.1.1',801,'Combiner') # Подключаемся к ПЛК
    
    var_1 = None # И тут мне надо сделать так, что бы класс Variable Кушал DICT Как параметр
    
    plc.close_connection()
    db.disconnect()