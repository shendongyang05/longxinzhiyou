from ..BaseModel import DBInitialize

db_session = DBInitialize()

def insert(tp, ip, total, used, free, buffers, cache, swap, percent,current_t):
    sql = """INSERT INTO memoryInfo(type, ipaddress, total, used, free, buffers, cache, swap, percent, currentTime) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    data = (tp, ip, total, used, free, buffers, cache, swap, percent, current_t)
    db_session.db_insert(sql, data)


