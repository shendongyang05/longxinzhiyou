from ..BaseModel import DBInitialize
db_session = DBInitialize()


def insert(tp, info, version, release, name, processor_name,architecture,cpu_model):
    sql = """INSERT INTO otherInfo(type, os_info, os_version, os_release, os_name, os_processor_name, os_processor_architecture,cpu_model) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"""
    data = map(str,(tp, info, version, release, name, processor_name, architecture, cpu_model))
    db_session.db_insert(sql, tuple(data))