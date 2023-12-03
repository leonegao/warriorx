import mysql.connector
db= mysql.connector.connect(
    host='localhost',
    user = 'root',
    passwd='root'

)
c = db.cursor()
c.execute("CREATE DATABASE profileDb")
print('all good')
