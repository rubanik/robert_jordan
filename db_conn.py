import queries
import datetime
import logging
from time import sleep
import random
import psycopg
import pyads

from time import sleep

# %(asctime)s
logging.basicConfig(
    format='[%(levelname)s]: %(asctime)s %(message)s', 
    level=logging.DEBUG)

#PLC_ADS_ADR = '10.44.1.14.1.1'
PLC_ADS_ADR_HOME = '192.168.1.177.1.1'
PLC_ADS_PORT = 801
USER_NAME = 'admin'

TEST_DATA = (datetime.datetime.now(),datetime.datetime.now(),random.randint(0,100),'PLC.TEST_BOOL','admin')

#connection_info = "dbname=combiner_data user=admin password=admin host=localhost"
connection_info = "dbname=combiner_data user=postgres password=1122 host=localhost"

variable_list = ['PF_Paper_Unwinding.bobbin_change_diameter_npr',
                'FC_M3_Receiver_Ch2_Interface.o_filter_sender_ok_dvr',
                'FC_M3_Receiver_Ch1_Interface.o_filter_sender_ok_dvr',
                'FC_M3_Receiver_Ch1_Safety.o_rear_switch_is_safely_closed_dvr',
                'FC_M3_Receiver_Ch2_Safety.o_rear_switch_is_safely_closed_dvr']


class Variable:

    def __init__(self,name,var_type,good_state):
        """
        Инициализация объекта 'Переменная'.
        var_type - тип данных, который использует pyads
        good_state - состояние сигнала, которое является OK
        state - сигнал, который отражает актуальное состояние переменной, отвечает за триггер alarm
        triggered - статус тревоги, появляется в момент перехода good_state из 1 в 0.
        start, finish - таймштампы для рачёта длительности
        """
        self.name = name
        self.var_type = var_type
        self.good_state = good_state
        self.state = self.good_state
        self.triggered = False
        self.start = ''
        self.finish = ''
        logging.debug(f'Variable init : Name: {self.name}')

        
    def set_start(self):
        """ Устанавливает текущее время как стартовое время события"""
        self.start = datetime.datetime.now()
        
    def set_finish(self):
        """ Устанавливает текущее время как время окончания события"""
        self.finish = datetime.datetime.now()
    
    @property
    def duration(self):
        """ Возвращает длительность события - Tfinish - Tstart """
        duration = self.finish - self.start
        return duration.seconds
    
    @property
    def alarm(self):
        """ Возвращает статус тревоги. Появляется при старте события"""
        return self.state != self.good_state
        
    def set_state(self):
        """ Устанавливает статус переменной"""
        self.state = self.good_state # TODO: Это что такое? Проверить и переделать UPD - Поправил, а нужен ли он вообще?
        
    def start_event(self):
        """ Здесь инициируется Событие"""
        self.triggered = True # Активируем триггер - сигнал говорит о том что текущее событие активно.
        self.set_start() # Устанавливаем время начала события
        logging.info(f'Alarm on event {self.name} started in {self.start}')
         
    def finish_event(self):
        """ Здесь закрывается Событие"""
        self.triggered = False # Деактивируем триггер
        self.set_finish() # Берем время окончания события
        logging.info(f'ALARM at {self.name} is released')
        
    def get_data(self):
        """ Метод необходим что бы вернуть все основные параметры События переменной"""
        return (self.start,
                self.finish,
                self.duration,
                self.name,
                USER_NAME) # Этому здесь не место

class Condition:
    """ 
    Класс, опысывающий объект Condition,наследуется от Variable(?)
    Суть - передать состояние оборудования при котором будет 
    активироваться состояние ALARM. Например - если важно мониторить
    состояние переменной только во время работы машины, но 
    переменная может менять своё состояние и во время остановки.
    """
    pass
    
def execute_query(query,conn,data=None):
    
    if data:
        logging.info(f'Executing query with data = {data}')
        conn.execute(query,data)
    else:
        logging.info(f'Executing query without data')
        conn.execute(query)
    conn.commit()
        
def get_datetime():
    return datetime.datetime.now()
    
def get_event_duration(start,finish):
    duration = start - finish
    return duration.seconds

   
def main():
    
    try:
        # Create DB connection
        connection_to_db = psycopg.connect(connection_info)
        logging.info('Conntcted to DB')
        # Create connection to PLC 
        connection_to_plc = pyads.Connection(PLC_ADS_ADR_HOME, PLC_ADS_PORT)
        connection_to_plc.open()
        logging.info(f'Conntcted to PLC. Address: {PLC_ADS_ADR_HOME}')
        # Make variable obj # TODO: Нормальный метод получения переменных
        obj = [Variable('FC_M3_Receiver_Ch1_Interface.o_filter_sender_ok_dvr',pyads.PLCTYPE_BOOL,True), 
               Variable('FC_M3_Receiver_Ch2_Interface.o_filter_sender_ok_dvr',pyads.PLCTYPE_BOOL,True)]
        
        logging.info('Main cycle running')
        while True:
            for variable in obj:
                variable.state = connection_to_plc.read_by_name(variable.name,variable.var_type)
                if variable.alarm and not variable.triggered:
                    logging.info(f'State ALARM set to {variable.name}.')
                    # Начинаем событие если ранее оно не было начато
                    variable.start_event()
                elif not variable.alarm and variable.triggered:
                    # Ошибка устранилась, но событие ещё активно, то завершаем его
                    variable.finish_event()
                    # Записываем в DB
                    execute_query(queries.Q_INSERT_IN_LOG,connection_to_db,variable.get_data())
                    logging.info(f'Query executed!')
            sleep(0.2)
                
    except Exception as e:
        print(e)
        connection_to_db.rollback()
    else:
        connection_to_db.commit()
    finally:
        connection_to_db.close()
        connection_to_plc.close()
        logging.info(f'All connections is closed.')


if __name__ == '__main__':
    main()