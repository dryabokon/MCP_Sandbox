import pandas as pd
from sqlalchemy import create_engine, text
from tabulate import tabulate
#----------------------------------------------------------------------------------------------------------------------
class SQLServerClient(object):
    def __init__(self,config):
        self.folder_out = './output/'
        self.config = config
        self.engine = create_engine(self.config.SQL_connect)
        return
    # ----------------------------------------------------------------------------------------------------------------------
    def execute_query(self, SQL):
        with self.engine.connect() as conn:
            df = pd.read_sql(text(SQL), conn)

        return df
    # ----------------------------------------------------------------------------------------------------------------------
    def get_table(self,schema_name, table_name,limit=100):
        df = self.execute_query(f'SELECT * FROM {schema_name}.{table_name} limit {limit}')
        return df
    # ----------------------------------------------------------------------------------------------------------------------
    def get_table_size(self, schema_name, table_name):
        df = self.execute_query(f'SELECT count(*) FROM {schema_name}.{table_name}')
        return df.iloc[0,0]
    # ----------------------------------------------------------------------------------------------------------------------
    def get_tables(self,schema_name=None):
        Q = "SELECT TABLE_SCHEMA,TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
        if schema_name is not None:
            Q+= f" AND TABLE_SCHEMA = '{schema_name}'"

        df = self.execute_query(Q)
        df['TABLE_SIZE_BYTES'] = 0
        for r in range(len(df)):
            df.loc[r,'TABLE_RECORDS'] = self.get_table_size(df.loc[r,'TABLE_SCHEMA'],df.loc[r,'TABLE_NAME'])

        df = df.sort_values(by=['TABLE_SCHEMA', 'TABLE_NAME'])
        return df
    # ----------------------------------------------------------------------------------------------------------------------
    def get_table_structure(self, schema_name, table_name):
        df = self.execute_query(f'SELECT COLUMN_NAME as column_name, DATA_TYPE as data_type FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = \'{table_name}\' AND TABLE_SCHEMA = \'{schema_name}\' ORDER BY ORDINAL_POSITION')
        return df
    # ----------------------------------------------------------------------------------------------------------------------
    def get_full_structure(self):
        df_tables = self.get_tables()
        df_res = pd.DataFrame()
        for r in range(len(df_tables)):
            df = self.get_table_structure(df_tables.loc[r,'TABLE_SCHEMA'],df_tables.loc[r,'TABLE_NAME'])
            df.insert(0, 'TABLE_NAME', df_tables.loc[r,'TABLE_NAME'])
            df.insert(0, 'TABLE_SCHEMA', df_tables.loc[r, 'TABLE_SCHEMA'])
            df_res = pd.concat([df_res,df])

        return df_res
    # ----------------------------------------------------------------------------------------------------------------------
    def prettify(self,df, showheader=True, showindex=True, tablefmt='psql', desc='', maxcolwidths=None, floatfmt='.2f',filename_out=None):
        if df.shape[0] == 0 or df.shape[1] == 0:
            res = ''
        else:
            df_fmt = df.copy()
            for col in df_fmt.select_dtypes(include=['float']):
                df_fmt[col] = df_fmt[col].map(lambda x: format(x, floatfmt))

            res = tabulate(df_fmt, headers=df_fmt.columns if showheader else [], tablefmt=tablefmt, showindex=showindex,maxcolwidths=maxcolwidths)

        if desc != '':
            bar = '-' * len(res.split('\n')[0])
            res = f"{bar}\n| {desc}\n{res}"

        if filename_out is not None:
            with open(filename_out, 'w', encoding='utf-8') as f:
                f.write(res)

        return res
    # ----------------------------------------------------------------------------------------------------------------------
    def pretty_save(self,df,filename):
        txt = self.prettify(df, showindex=False)
        with open(self.folder_out + filename, "w", encoding="utf-8", errors="replace") as f:
            f.write(txt)
        return
    #----------------------------------------------------------------------------------------------------------------------
