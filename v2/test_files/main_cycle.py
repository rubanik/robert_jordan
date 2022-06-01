import test_db
import test_init
import general


PLC_ADS_ADDRESS = '10.44.1.14.1.1'
PLC_ADS_PORT = 801


class MainCycle:
    
    db_connection = None
    init_parameters_dict = None
    plc_connection = None
    variables_list = []

    
    def __init__(self,work_to_do,cycle_time=0.100):
        self.__cycle_time__ = ct
        
    def start(self):
        # step 1:Create DB connection
        self.set_db_connection()
        # step 2:Get initial parameters from DB
        self.set_parameter_dict()
        # step 3:Set PLC connection
        self.set_plc_connection()
        # step 4:Create all Variables() with self.init_param_list
        self.generate_var_list()
            
    def set_db_connection(self):
        try:
            if not self.db_connection:
                self.db_connection = test_db.Database()
            else:
                print('Соединение с DB уже есть')
        except Exception as ex_db:
            print('Возникла проблема при соединении с Базой данных',ex_db,sep='\n')
    
    
    def set_parameter_dict(self):
        try:
            if not self.init_parameters_dict:
                self.init_parameters_dict = test_init.DataInit(self.db_connection).generate_cl_list()
            else:
                return self.init_parameters_dict
        except Exception as ex_init:
            print('Возникла проблема при получении начальных данных',ex_init,sep='\n')
    
    
    def set_plc_connection(self):
        try:
            if not self.plc_connection:
                self.plc_connection = general.Plc(PLC_ADS_ADDRESS,PLC_ADS_PORT)
            else:
                print('Соединение с контроллером уже установлено')
        except Exception as ex_plc:
            print('Возникла проблема при соединении с Базой данных', ex_plc, sep='\n')

            
    def generate_var_list(self):
        try:
            if (self.init_parameters_dict and
                self.plc_connection):
                for parameter in self.init_parameters_dict:
                    self.variables_list.append(
                        general.Variable(self.plc_connection,parameter))
        except Exception as ex_var_gen:
            print('Возникла проблема при генерации переменных', ex_var_gen, sep='\n')
