from ..BaseModel import DBInitialize

db_session = DBInitialize()


def insert(tp, ip, user_t, system_t, wait_io, idle, count, percent, current_t):
    sql = """INSERT INTO cpuInfo(type, ipaddress, userTime, SystemTime, waitIO, Idle, count, percent, currentTime) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    data = (tp, ip, user_t, system_t, wait_io, idle, count, percent, current_t)
    db_session.db_insert(sql, data)




