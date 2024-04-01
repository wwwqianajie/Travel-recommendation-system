import mysql.connector
def users_login():
    cnx = mysql.connector.connect(
        host="192.168.88.161",
        user="root",
        password="123456",
        database="Travel"
    )
    cursor = cnx.cursor()
    query = "SELECT * FROM users"
    cursor.execute(query)
    lis1=[]
    for i in cursor:
        lis1.append(list(i))
    lis2=[]
    for i in lis1:
        my_dict={"name":i[0],"password":i[1]}
        lis2.append(my_dict)
    return lis2
print(users_login())
        