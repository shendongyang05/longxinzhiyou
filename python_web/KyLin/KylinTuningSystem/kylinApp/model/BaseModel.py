import pymysql
from django.conf import settings


class DBBase:

    def __init__(self, user, password, host, port, db, charset):
        self.mydb = pymysql.connect(user=user,
                                    password=password,
                                    host=host,
                                    port=port,
                                    db=db,
                                    charset=charset)
        self.cursor = self.mydb.cursor(pymysql.cursors.DictCursor)

    def db_cursor(self):
        """返回游标"""
        return self.cursor

    def db_rollback(self):
        """发生错误回滚"""
        self.mydb.rollback()

    def db_commit(self):
        """提交"""
        self.mydb.commit()

    def db_close(self):
        """关闭"""
        self.cursor.close()
        self.mydb.close()

    def db_insert(self, sql, format_sql: tuple):
        """"占位符Insert Into Table Values(s%,s%,s%,s%),format_slq=(value1,value2,value3,value4)"""
        try:
            if not format_sql:
                self.cursor.execute(sql)
            else:
                self.cursor.execute(sql, format_sql)
            self.db_commit()
        except Exception as e:
            self.db_rollback()
            print("错误：%s" % e)

    def db_delete(self, sql, format_sql):
        self.cursor.execute(sql, format_sql)
        affected_rows = self.cursor.rowcount
        self.db_commit()
        return affected_rows

    def db_select(self, sql, format_sql):
        self.cursor.execute(sql, format_sql)
        query_data = self.cursor.fetchall()
        return query_data


class DBInitialize(DBBase):
    def __init__(self):
        db_info = settings.DATABASES["default"]
        user = db_info.get("USER")
        password = db_info.get("PASSWORD")
        host = db_info.get("HOST")
        port = int(db_info.get("PORT"))
        db = db_info.get("NAME")
        charset = "utf8"
        super().__init__(user, password, host, port, db, charset)


class SelectDBInitialize(DBBase):
    def __init__(self, user, password, host,db , port, charset):
        super().__init__(user, password, host, port, db, charset)
