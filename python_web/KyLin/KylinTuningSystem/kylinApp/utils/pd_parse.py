import pandas as pd
from sqlalchemy import create_engine
from django.conf import settings


def connect_mysql():
    db_info = settings.DATABASES["default"]
    user = db_info.get("USER")
    password = db_info.get("PASSWORD")
    host = db_info.get("HOST")
    db = db_info.get("NAME")
    # MySQL 连接字符串格式：mysql+pymysql://<username>:<password>@<hostname>/<database_name>
    engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:3306/{db}')
    return engine


def get_table_data(engine):
    sqls = [
        'SELECT * FROM DfInfo',
        'SELECT * FROM memoryInfo',
        'SELECT * FROM cpuInfo'
    ]
    dfs = []
    for sql in sqls:
        df = pd.read_sql(sql,con=engine)
        dfs.append(df)
    return dfs


def get_variance(dfs=None):
    variances = []
    if dfs:
        for df in dfs:
            variance = df["percent"].var()
            variances.append(variance)
    return variances


def get_mean(dfs=None):
    means = []
    if dfs:
        for df in dfs:
            mean = df["percent"].mean()
            means.append(mean)
    return means


def main():
    engine = connect_mysql()
    dfs = get_table_data(engine)
    variance = get_variance(dfs)
    mean = get_mean(dfs)
    print(f"磁盘、内存、CPU使用率方差分别为：{variance}")
    print(f"磁盘、内存、CPU使用率均值为：{mean}")


main()


