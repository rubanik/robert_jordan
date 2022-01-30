Q_CREATE_TABLE = """
                CREATE TABLE process_flow_log (
                    record_id serial PRIMARY KEY,
                    start_date timestamp without time zone,
                    finish_date timestamp without time zone,
                    event_duration integer,
                    variable char(255),
                    user_name char(255));
                """
Q_INSERT_IN_LOG = '''INSERT INTO process_flow_log
                    (
                        start_date, 
                        finish_date, 
                        event_duration, 
                        variable, 
                        user_name
                    )
                    VALUES (%s, %s, %s, %s, %s)'''


