import datetime
import pyads


def db_execute(query,data):
    print(f'OK -----   {query} + ',data)


class Plc:
    """
    
    Класс в котором происходит работа с контроллером. 

    """
    def __init__(self,address):
        self.address = address
        self.connect()

    def connect(self):
        return (True,f'Connected to {self.address}')
    
    def read_by_name(self,path,name):
        return '200'

    

class Variable:

    def __init__(self,path,var_type,plc,
                name='',ctrl_type = 'state', test = False):
        self.path = path                    # Path to variable according to PLC variable path in the symbol table.
        self.name = name if name else path  # Human-readable name, it will be the self.path if you don't want to set it.
        self.var_type = var_type            # TYPE of PLC variable - pyads types.( INT, BOOL, STRING, ARRAY etc)
        self.plc = plc                      # Instance of the plc object.
        self.test = test                    # Use it if you do not have PLC. Set to TRUE if you need to do small test...

    @property
    def value(self):
        if self.test:
            return self.test
        else: 
            return self.plc.read_by_name(self.path,self.var_type)# read from plc


class StateControler:
    """
    Контроллер состояния переменной. Базовый класс описывающий общие
    функции работы с переменной и ёё состояниями. 
    """

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
        db_execute(self.QUERY, self.get_data())


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
    
    QUERY = 'SWITCH EVENT QUERY'

    def __init__(self, var, condition=None):
        StateControler.__init__(self,var)
        self.condition = condition
        self.start_time = ''
        self.finish_time = ''

    def _set_time(self):
        if self.start_time:
            self.finish_time = datetime.datetime.now()
        else:
            self.start_time = datetime.datetime.now()

    def _set_flag(self):
        self.flag = not self.flag

    def start_event(self):
            self._set_time()

    def finish_event(self):
            self._set_time()