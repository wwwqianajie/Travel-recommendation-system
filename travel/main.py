from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from model import modeltocsv
from connect import users_login
import mysql.connector
from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
from pyspark.ml.feature import StringIndexer, IndexToString
from pyspark.sql.functions import col, explode
import mysql.connector
import pandas as pd
from pyspark.sql.functions import rand
from mysql.connector import Error
from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
from pyspark.ml.feature import StringIndexer, IndexToString
from pyspark.sql.functions import col, explode
from pyspark.sql.functions import lit, rand
from pyspark.sql.functions import when, col
    # 创建SparkSession
from mysql.connector import Error 
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 设置一个密钥，用于维护会话安全

@app.route('/', methods=['GET', 'POST'])
def clf():
    return render_template("login.html")

@app.route("/login.html", methods=['POST'])
def login():
    modeltocsv()
    lis = users_login()  # 假设users_login是一个包含用户信息的列表
    username = request.form.get('username')
    password = request.form.get('password')
    found_user = False  # 记录是否找到匹配的用户

    for user in lis:
        if user["name"] == username and user["password"] == password:
            found_user = True
            break

    if found_user:
        session['user_name'] = username  # 保存当前用户的用户名
        return redirect(url_for('main'))
    else:
        return render_template('login.html')
@app.route("/main.html")
def main():
    return render_template('main.html')
@app.route("/recommend.html")
def recommend():
    return render_template("recommend.html")
@app.route('/update_images', methods=['POST'])
def update_images():
    location = request.form.get('location')
    # 连接数据库
    try:
        cnx = mysql.connector.connect(
            host="192.168.88.161",
            user="root",
            password="123456",
            database="Travel"
        )
        cursor = cnx.cursor()

        # 参数化查询，使用 location 来获取数据
        query = "SELECT Name,Place, Picture_Address, Web_Address, User_Evaluation, Score FROM %s" % location
        cursor.execute(query)
        
        # 获取查询结果并构建响应数据
        images = []
        for (name,place, picture_address, web_address, user_evaluation, score) in cursor:
            images.append({
                'name': name,
                'place':place,
                'imagePath': picture_address,
                'link': web_address,
                'evaluation': user_evaluation,
                'score': score
            })
    except Error as e:
        print("Error while connecting to MySQL", e)
        # 可以根据实际情况选择返回空列表或错误信息
        return jsonify({'images': []})
    print(images)
    return jsonify({'images': images})
@app.route('/save_click_image', methods=['POST'])
def save_click_image():
    data = request.json
    user_name = session.get('user_name', 'default_user_name')
    try:
        # 连接到数据库
        cnx = mysql.connector.connect(
            host="192.168.88.161",
            user="root",
            password="123456",
            database="Travel"
        )
        cursor = cnx.cursor()

        # 创建表（如果尚不存在）
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {user_name} (
                id VARCHAR(255),
                name VARCHAR(255) PRIMARY KEY,
                location VARCHAR(255),
                score FLOAT
            )
        """)

        # 插入数据
        add_image = (f"INSERT INTO {user_name} "
                     "(id, name, location,score) "
                     "VALUES (%s, %s, %s, %s)")
        image_data = (user_name, data['name'], data['place'],data['score'])
        cursor.execute(add_image, image_data)
        cnx.commit()
        print(user_name)
        cursor.close()
        cnx.close()
        return jsonify({'status': 'success'})
    except Error as e:
        print(f"Error: {e}")
        return jsonify({'status': 'failure', 'error': str(e)})

@app.route('/show', methods=['POST'])
def show():
    userRecs_pandas=pd.read_csv("user_recommendations.csv")
    images = []
    for row in userRecs_pandas.itertuples(index=False):
        images.append({
            'name': row.Place,
            'imagePath': row.Imagepath,
            'link': row.Link,
            'evaluation': row.Evaluation,
            'score': row.Score
        })
    print(images)
    return jsonify({'images': images})
if __name__ == '__main__':
    app.run()