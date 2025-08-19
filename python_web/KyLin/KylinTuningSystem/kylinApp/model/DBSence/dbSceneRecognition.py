from ..BaseModel import SelectDBInitialize
from concurrent.futures import ThreadPoolExecutor
import mysql.connector
import time
# selectdbinitialize是一个自定义的数据库连接初始化类
# threadpoolexcutor是用于并发执行任务


# 连接数据库
def get_questions_count(host, user, password, db, port, charset):
    db_session = SelectDBInitialize(user=user,password=password,host=host,port=port,db=db,charset=charset)
    cursor = db_session.db_cursor()
    # 通过db_session对象获取了一个数据库游标cursor，用于执行sql查询
    cursor.execute("SHOW GLOBAL STATUS LIKE 'Threads_connected'")
    # 执行sql查询，用于获取当前数据库的连接线程数
    threads_connected = cursor.fetchone()['Value']
    # 获取查询结果的第一行，并提取value字段的值，即当前的连接线程数，存储在变量threads_connected

    cursor.execute("SHOW GLOBAL STATUS LIKE 'Questions'")
    # 执行sql查询语句，用户获取数据库的总查询数量
    result = cursor.fetchone()
    # 获取查询结果的第一行，存储在变量result中
    cursor.close()
    # 关闭游标，释放资源
    db_session.db_close()
    # 调用db_session.db_close方法，关闭数据库连接
    return int(result["Value"]), threads_connected
#     返回两个值：总查询数量（转换为整数）和连接线程数

def get_select_speed(host, user, password, database, port, charset):
    # 获取初始查询数量和时间
    initial_questions = get_questions_count(host, user, password, database, port, charset)[0]
    # 调用get_questions_count函数获取初始的查询数量（只取返回值的第一个函数）
    initial_time = time.time()
    # 记录当前时间，存储在变量initial_time中

    # 等待10秒，观察查询数量的变化
    time.sleep(10)

    # 获取新的查询数量和时间
    final_questions, threads_connected = get_questions_count(host, user, password, database, port, charset)
    # 再次调用函数获取10秒后的查询数量和连接线程数
    final_time = time.time()

    # 计算查询数量变化和时间差
    queries_difference = final_questions - initial_questions
    # 计算查询梳理狼的变化，即10秒内新增的查询数量
    time_difference = final_time - initial_time
    # 计算时间差，即实际经过的时间

    # 计算查询速率（每秒平均查询数）
    query_rate = queries_difference / time_difference

    return "{:.2f}".format(query_rate), threads_connected
# 返回格式化后的查询速率（保留两位小数）和连接线程数


# 数据库连接
def get_db_connection(host, user, password, database, port, charset):
    # print(host, user, password, database, port, charset)
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
        charset=charset
    )
    return conn
# 返回创建的数据库连接


   # 1.连接到mysql数据库并获取当前的查询数量和连接线程数
   # 2.计算在10秒内的查询速率
   # 3.提供一个函数用于创建数据库连接



# 收集数据库信息
def collect_db_info(conn):
    cursor = conn.cursor()

    # 获取数据库表结构
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()

    # 获取每个表的行数
    table_info = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        table_info[table_name] = row_count

    # 获取查询类型和执行频率（需要分析查询日志或其他方式收集）
    # 假设我们有查询日志，可以分析日志来获得查询类型和执行频率
    queries = [
        ("SELECT * FROM users WHERE id=1;" , "read" , 0.01) ,
        ("INSERT INTO orders (user_id, product_id) VALUES (1, 2);" , "write" , 0.02) ,
    ]

    return {
        "tables": table_info ,
        "queries": queries
    }


# 提取特征
def extract_features(db_info):
    # 提取表的数量和总行数
    total_tables = len(db_info['tables'])
    total_rows = sum(db_info['tables'].values())

    # 计算读写查询的数量
    read_queries = [q for q in db_info['queries'] if q[1] == 'read']
    write_queries = [q for q in db_info['queries'] if q[1] == 'write']
    read_count = len(read_queries)
    write_count = len(write_queries)

    # 计算读写比率
    read_write_ratio = read_count / write_count if write_count != 0 else float('inf')

    return {
        'total_tables': total_tables ,
        'total_rows': total_rows ,
        'read_count': read_count ,
        'write_count': write_count ,
        'read_write_ratio': read_write_ratio
    }


# 分类数据库场景
def classify_db_scene(features):
    if features['read_write_ratio'] > 2 and features['total_tables'] < 10 and features['total_rows'] < 1000000:
        return 'OLTP'  # 在线事务处理
    elif features['write_count'] > features['read_count'] and features['total_rows'] > 1000000:
        return 'OLAP'  # 在线分析处理
    elif features['total_tables'] > 50:
        return 'CMS'  # 内容管理系统
    else:
        return 'Normal scene'


def db_scene(host, user, password, database, port, charset):
    conn = get_db_connection(host, user, password, database, port, charset)
    db_info = collect_db_info(conn)
    features = extract_features(db_info)
    scene = classify_db_scene(features)
    return scene, features


def db_speed(host, user, password, database, port, charset):
    speed = get_select_speed(host, user, password, database, port, charset)
    return speed


def return_data_main(host, user, password, database, port, charset):
    with ThreadPoolExecutor(2) as executor:
        data = {}
        future1 = executor.submit(db_scene, host , user , password , database , port , charset)
        future2 = executor.submit(db_speed, host , user , password , database , port , charset)

        scene_connected = future1.result()
        "('Normal scene', {'total_tables': 19, 'total_rows': 1200, 'read_count': 1, 'write_count': 1, 'read_write_ratio': 1.0})"
        speed = future2.result()
        "('2.69', '8')"

        data.update({"connected": speed[1]})
        data.update({"db_state": scene_connected[1]})
        data.update({"speed": speed[0]})
        data.update({"scene": scene_connected[0]})
        return data

