from ..BaseModel import DBInitialize

db_session = DBInitialize()

def insert(tp, ip, sent, recv, packet_sent, packet_recv, current_t):
    sql = """INSERT INTO networkInfo(type, ipaddress,sent,recv, packetSent, packetRecv, currentTime) VALUES(%s, %s, %s, %s, %s, %s, %s)"""
    data = (tp, ip, sent, recv, packet_sent, packet_recv, current_t)
    db_session.db_insert(sql, data)
