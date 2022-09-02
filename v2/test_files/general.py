import datetime
import pyads
import psycopg2 #as psycopg2

import test_db
import test_init

class Plc:
    """Create connection to a PLC and reading variables from it."""
    def __init__(self,address:str,port:int,name='Unnamed'):
        self.address = address
        self.port = port
        self.plc_connection = self.connect()
        self._open_connection()
        self.test_state = False

    def connect(self) -> pyads.Connection:
        """ Get pyads PLC connection object """
        return pyads.Connection(self.address, self.port)
    
    def _open_connection(self) -> None:
        """ Open the PLC Connection( open new session )"""
        if self.plc_connection:
            self.plc_connection.open()
            print('PLC CONNECTION IS OPEN')

    def close_connection(self):
        """ Close existing PLC connection """
        if self.plc_connection.is_open:
            self.plc_connection.close()
            print('PLC CONNECTION IS CLOSE')
    
    def read_by_name(self,path,name):
        return self.plc_connection.read_by_name(path,name)
    
    def read_group(self,group) -> dict:
        return self.plc_connection.read_list_by_name(group)
  

class Variable:

    def __init__(self,plc,param):
        self.plc = plc # Controller with PLC inside
        self.cl_id = param['cl_id'] 
        self.cl_type = param['cl_type_id'] # type like KEY,MASTER,BRAND
        self.cl_equip_group_id = param['cl_equip_group_id'] # Group is like GD, GIMA, etc
        self.cl_name =  param['cl_name'] if param['cl_name'] else param['cl_plc_path'] # If there is no name use plc.path
        self.cl_path = param['cl_plc_path']
        self.var_type = self.choose_pyads_plc_type(param['cl_data_type'])
        self.control_type = param['cl_control_type_id']
        self.group = None
        
    def __repr__(self):
        return self.cl_name
        
    @property
    def value(self):
        try:
            if self.group:
                return self.group.act_values[self.cl_path]
            else:
                value = self.plc.read_by_name(self.cl_path,self.var_type)# read from plc
                
            return self.set_value_type(value)
                
        except Exception as ex:
            print('Проблема при считывании переменной', ex, self.cl_path, sep='\n')
    

    def set_value_type(self,value):
        if self.var_type == pyads.PLCTYPE_STRING :
            return str(value)
        elif self.var_type in (pyads.PLCTYPE_DINT,pyads.PLCTYPE_INT,pyads.PLCTYPE_LREAL,pyads.PLCTYPE_BOOL):
            return round(float(value),2)
        else:
            print('WRONG VALUE TYPE')

    def choose_pyads_plc_type(self,cl_var_type):
        """ Выбираем на основе полученной str с типом тип pyads.PLCTYPE..."""
        var_type = None

        if cl_var_type == 'INT':
            var_type = pyads.PLCTYPE_INT
        elif cl_var_type == 'BOOL':
            var_type = pyads.PLCTYPE_BOOL
        elif cl_var_type == 'LREAL':
            var_type = pyads.PLCTYPE_LREAL
        elif cl_var_type == 'DINT':
            var_type = pyads.PLCTYPE_DINT
        elif cl_var_type == 'STRING':
            var_type = pyads.PLCTYPE_STRING            
        return var_type

class VarGroup:

    def __init__(self,group,plc):
        self.group = group
        self.plc = plc
        self.path_name_dict = {}
        self.act_values = {}
        self.generate_paths_and_names()
        self.attach_to_group()

    def attach_to_group(self):
        for variable in self.group:
            if not variable.group:
                variable.group = self
    
    def generate_paths_and_names(self):
        return {x.cl_path : x.cl_name for x in self.group}

    def update_group(self):
        self.act_values = plc.read_group(list(self.path_name_dict.keys()))


class StateControler:

    QUERY = 'BASIC_QUERY'
    INIT_QUERY = "SELECT cl_value FROM cl_last_changes_view WHERE cl_id = %s"

    def __init__(self,var,db):
        self.var = var
        self.db = db
        self.init = True
        self.prev_state = self.get_previous_state()

    @property
    def change_detected(self):
        return self.var.value != self.prev_state
        

    def get_previous_state(self):
        """ Возвращаем последнее значение переменной. Если создаём переменную, при первом запуске нужно вытащить последнее зафиксированное значение из БД"""
        if self.init:
            try:
                last_value =  float(self.db.send_select_query(self.INIT_QUERY,(self.var.cl_id,))[0][0])
                actual_value = float(self.var.value)
                print(round(last_value,2), round(actual_value,2))
                if round(last_value,2) == round(actual_value,2):
                    return actual_value
                else:
                    return last_value
            except:
                print('Что то пошло не так при попытке получить последнее значение переменной')
            finally:
                init = False
        else:
            return self.var.value
    

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
        print(self.get_data())
        self.db.send_query(self.QUERY, self.get_data())


class SwitchControl(StateControler):
    """
    Наследник StateController.  Описывает поведение переменной "переключатель".
    Фиксирует изменение состояния Bool переменной. Идёт фиксация времени и состояние.
    """

    QUERY = """INSERT INTO cl_change_log
                    (
                        tstamp,
                        cl_id,
                        cl_value
                    )
                    VALUES (%s,%s,%s)
                    """

    last_change_time = ''

    @property
    def time_of_switch(self):
        """ Фиксация времени изменения переменной """
        return datetime.datetime.now()

    def get_data(self):
        cl_id = self.var.cl_id
        value = self.var.value
        timest = self.time_of_switch

        return (timest,cl_id,value)


class StopMsgControl(SwitchControl):

    QUERY = """INSERT INTO stop_msg_log
                    (
                        tstamp,
                        cl_id,
                        msg_text
                    )
                    VALUES (%s,%s,%s)
                    """
    
    INIT_QUERY = """SELECT msg_text FROM stop_msg_log WHERE cl_id=%s ORDER BY tstamp DESC LIMIT 1"""
    
    def get_previous_state(self):
        last_msg = self.db.send_select_query(self.INIT_QUERY,(self.var.cl_id,))[0][0]
        act_msg = self.var.value
        print('StopMsgControl: Last Message: ',last_msg)
        return last_msg

class SwitchEventControl(StateControler):
    
    QUERY = '''INSERT INTO cl_change_log
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

class ActValControl():

    QUERY = """INSERT INTO cl_change_log
                    (
                        tstamp,
                        cl_id,
                        cl_value
                    )
                    VALUES (%s,%s,%s)
                    """
    def __init__(self,group,db, timeout = 1) -> None:
        self.group = group
        self.db = db
        self.timeout = timeout
    
    def check_state(self):
        pass
    

if __name__ == "__main__":

    db = test_db.Database() # инициируем базу данных
    
    param_dict = test_init.DataInit(db).generate_cl_list() # достаём данные {} из таблицы cl_list
    print(*param_dict,sep="\n")
    
    plc = Plc('10.44.1.14.1.1',801,'Combiner') # Подключаемся к ПЛК
    
    var_list = []
    contrl_list = []
    
    for entry in param_dict:
        variable = Variable(plc,entry)
        var_list.append(variable)
        contrl_list.append(SwitchControl(variable))

    
    
    #var_1 = Variable(plc,param_dict[1])
    #sc = SwitchControl(var_1)
    #print(var_1.value)
    
    try:
        while 1:
            for item in contrl_list:
                item.check_state()
    except Exception as e:
        print(e)
    finally:
        plc.close_connection()
        db.disconnect()