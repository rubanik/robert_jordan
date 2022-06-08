from time import sleep
import signal

import test_db
import test_init
import general


PLC_ADS_ADDRESS = '10.44.1.14.1.1'
PLC_ADS_PORT = 801

def ctrl_c_handler(signum, frame):
    """" Обработчик нажатия CTRL+C. После нажатия аккуратно закрывает всё"""

    res = input("Ctrl-c was pressed. Do you really want to exit? y/n ")
    if res == 'y':
        cycle.stop_cycle()
        exit(1)

class MainCycle:
    """Логика работы основного цикла скрипта"""
    db_connection = None # Переменная для хранения ссылки на ДБ коннектор
    init_parameters_dict = None # Словарь в котором хранятся изначальные параметры из БД
    plc_connection = None # Ссылка на PYADS соедениение с PLC
    variables_list = [] # Список для хранения объектов Variable
    controller_list = [] # Список для хранения Contreller объектов
    act_values_group = None
    act_values_controller = None
    
    def __init__(self,cycle_time=0.100):
        self.__cycle_pause_time__ = cycle_time # Время паузы перед след циклом
        
    def start(self) -> None:
        """ 
        Поэтапное выполнение всех шагов программы, неоходимых для работы.
        Сначала создаём подключения к ДБ, ПЛК. Собираем начальные данные.
        последний шаг - запуск цикла опроса\основного рабочего цикла.
        """
        # step 1:Create DB connection
        self.set_db_connection()
        # step 2:Get initial parameters from DB
        self.set_parameter_dict()
        # step 3:Set PLC connection
        self.set_plc_connection()
        # step 4:Create all Variables() with self.init_param_list
        self.generate_var_list()
        # step 5:Create list of State Controllers 
        self.generate_state_ctrl_list()
        # step 6:Create Group of act. values
        self.generate_group()
        # step 7:Create Controller for Act.Val Group
        self.generate_act_val_controller()
        # step 99:Run state_check() task
        self.run_task()
            
    def set_db_connection(self):
        """Создаём объект db_connection для работы с БД, с которым будт работать скрипт. """
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
                return self.init_parameters_dict # Зачем что-то возвращать если оно уже имеется? 
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
    
    
    def generate_state_ctrl_list(self):
        try:
            if self.variables_list:
                for variable in self.variables_list:
                    if variable.control_type == 2:
                        self.controller_list.append(
                            general.SwitchControl(variable, self.db_connection))
        except Exception as ex_st_ctrl:
            print('Возникла проблема при генерации State Controllers', ex_st_ctrl, sep='\n')
    
    def generate_group(self):
        group_list = [var for var in self.variables_list if var.control_type == 4]
        self.act_values_group = general.VarGroup(group_list,self.plc_connection)

    def generate_act_val_controller(self):
        self.controller_list.append(general.ActValControl(self.act_values_group,self.db_connection))
        

    def task_cycle(self,tasks):
        for item in tasks:
            item.check_state()
        
    def run_task(self):
        while 1:
            try:
                self.task_cycle(self.controller_list)
                sleep(self.__cycle_pause_time__)
            except Exception as ex_task:
                print('Main cycle stopped',ex_task,sep='\n')
                self.db_connection.disconnect()
                self.plc_connection.close_connection()
                break
    
    def stop_cycle(self):       
        
        self.db_connection.disconnect()
        self.plc_connection.close_connection()
        
if __name__ == '__main__':
    
    signal.signal(signal.SIGINT, ctrl_c_handler)
    cycle = MainCycle()
    cycle.start()