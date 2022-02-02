import mariadb
import sys

class Column:

    def __init__(self, name: str, data_type: str, data_length: int=None, not_null: bool=False, default_value=None, auto_increment: bool=False, constraint: str=None):
        self.name, self.data_type, self.data_length, self.not_null, self.default_value, self.auto_increment, self.constraint = name, data_type, data_length, not_null, default_value, auto_increment, constraint
    
    def __str__(self):
        res = f'{self.name} {self.data_type}'
        if self.data_length is not None: res+=f'({self.data_length})'
        if self.not_null: res+=f' not null'
        if self.default_value is not None: res+=f' {self.default_value}'
        if self.auto_increment: res+=f' auto_increment'
        if self.constraint is not None: res+=f' {self.constraint}'

        return res

class DBConnector:
    def __init__(self, database: str):
        self.database = database

    def with_cursor(f):

        def with_connection(f):
            '''
                Connection decorator
                Could be upgraded to a Connection Pool
            '''
            def wrapper(self, *args, **kwargs):
                try:
                    conn = mariadb.connect(
                        user="baptiste",
                        password="fantaServer99",
                        database=self.database
                    )
                            
                    try:
                        result = f(self, *args, connection=conn, **kwargs)
                    except:
                        conn.rollback()
                        print("SQL failed")
                        raise
                    else:
                        conn.commit()
                    finally:
                        conn.close()

                    return result

                except mariadb.Error as e:
                    print(f'Error connecting to MariaDB : {e}')
                    sys.exit(1)

            return wrapper

        @with_connection
        def wrapper(self, *args, **kwargs):
            conn = kwargs.pop("connection")
            cursor = conn.cursor()
            return f(self, *args, cursor=cursor, **kwargs)

        return wrapper


    @with_cursor
    def executeRequest(self, query: str, dml: bool = False, *args, **kwargs) -> list:
        '''
            Perform basic Data Definition Language (DDL) or Data Manipulation Language (DML) operations
        '''
        cursor = kwargs.pop("cursor")

        if(query[-1] != ';'): query += ';'

        # print(f"> Perform request {query}")
        cursor.execute(query)
        #print("Request successful")
        if dml: 
            return [c for c in cursor.fetchall()]

    def get_field_info(self, cur)->list[str]:
        '''
            Retrieves the fields info associated with a cursor
        '''
        field_info = mariadb.fieldinfo()
        field_info_text = []

        for column in cur.description:
            column_name = column[0]
            column_type = field_info.type(column)
            column_flags = field_info.flag(column)
            field_info_text.append(f"{column_name}: {column_type} {column_flags}")

        return field_info_text


    def get_table_field_info(self, cur, table):
        """Retrieves the field info associated with a table"""

        # Fetch Table Information
        cur.execute(f"SELECT * FROM {table} LIMIT 1")

        field_info_text = self.get_field_info(cur)

        return field_info_text

    @with_cursor
    def describeDB(self, *args, **kwargs):
        '''
            Display global informations about the database
        '''
        cursor = kwargs.pop("cursor")
        cursor.execute("SHOW TABLES")

        print('\n[Database description]')
        res : list[tuple] = cursor.fetchall()
        for (table,) in res:
            cursor.execute(f"SELECT * FROM {table} LIMIT 1")
            field_info_text = self.get_field_info(cursor)

            print(f"- Columns in table [{table}] :")
            print('\t' + "\n\t".join(field_info_text))
            print("\n\n")

        if len(res) == 0:
            print("Empty database\n")

    def createTable(self, tableName: str, columns: list[Column], constraints: list[str] = [], *args, **kwargs) -> None:

        columns = [col.__str__() for col in columns]
        query = 'CREATE TABLE IF NOT EXISTS ' + tableName + '(' + ','.join(columns+constraints) + ');'

        self.executeRequest(query)
        return

    def dropTable(self, tableName: str):
        query = 'DROP TABLE IF EXISTS ' + tableName + ';'
        self.executeRequest(query)

