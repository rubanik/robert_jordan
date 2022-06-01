import test_db


class DataInit:
    """Класс в котором мы через запрос к ДБ получаем список контролируемых параметров"""

    RAW_DATA = None # Data collected after SQL request
    CL_LIST_FROM_DB = [] # It's the result. List with dictionaries with a cl inside. 
    DATA_INIT_QUERY = 'SELECT cl_id,cl_type_id,cl_equip_group_id, \
                        cl_name,cl_setpoint,cl_plc_path,cl_data_type, \
                        cl_control_type_id FROM cl_list' # SQL query for pulling cl_list from the CL_LIST table.
                        
    DATA_STRUCTURE = ('cl_id','cl_type_id', 'cl_equip_group_id', 'cl_name',
                      'cl_setpoint','cl_plc_path','cl_data_type','cl_control_type_id') # TODO: GET DATA STRUCTURE()

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
            result = []
            for data in self.RAW_DATA:
                data_dict = dict(zip(self.DATA_STRUCTURE, data))
                #  вместо использования атрибута класса создам ка я временный лист
                result.append(data_dict)

                #self.CL_LIST_FROM_DB.append(data_dict)
            return result
            #return self.CL_LIST_FROM_DB
    
class db_test:

    def execute(self,query):
        return [(1,1,1,'cl_position'),(2,2,1,'cl_position'),(3,1,4,'cl_position'),(3,1,1,'cl_position')]


if __name__ == '__main__':
    
    db = test_db.Database()
    
    DataInit(db).generate_cl_list()
    
    db.disconnect()