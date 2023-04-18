import pymysql as my


db = my.connect(
    host="db",
    port=3306,  # 임시
    user="root",
    password="12341234",
    charset="utf8",
    cursorclass=my.cursors.DictCursor,
)


def db_init():

    with db.cursor() as cur:
        # db 생성
        cur.execute(
            """
                    create database if not EXISTS user_db;
                    """
        )
        # db 사용
        cur.execute(
            """
                    use user_db;
                    """
        )
        # 테이블 세팅
        cur.execute(
            """
                    CREATE TABLE if not EXISTS user (
                        id int NOT NULL AUTO_INCREMENT,
                        username char(15) NOT NULL, 
                        password char(20) NOT NULL, 
                        PRIMARY KEY(id)
                        );
                    """
        )
    # 관리자 1 등록
    with db.cursor() as cur:
        cur.execute(
            """
            INSERT INTO `user_db`.`user` (`username`, `password`) VALUES ('user1', '1234');
            """
        )
    db.commit()
    return db


def db_select(username, password):
    sql = (
        f"select * from `user_db`.`user` where username = '{username}' && password = '{password}'; "
    )
    with db.cursor() as cur:
        result = cur.execute(sql)
    return result
