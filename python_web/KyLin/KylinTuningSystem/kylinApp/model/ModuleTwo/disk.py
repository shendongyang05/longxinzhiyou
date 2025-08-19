from ..BaseModel import DBInitialize

db_session = DBInitialize()


def insert(tp, ip, total, used, free, percent, r_count, w_count, r_bytes, w_bytes, r_time, w_time, current_t):
    sql = """INSERT INTO DfInfo(type, ipaddress,total,used,free,percent, readCount, writeCount, readBytes, writeBytes, readTime, writeTime, currentTime) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    data = (tp, ip, total, used, free, percent, r_count, w_count, r_bytes, w_bytes, r_time, w_time, current_t)
    db_session.db_insert(sql, data)
