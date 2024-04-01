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
def modeltocsv():
    spark = SparkSession.builder.appName("TravelRecommendation").getOrCreate()

    # 连接到MySQL数据库并提取数据
    try:
        connection = mysql.connector.connect(
            host='192.168.88.161',
            database='Travel',
            user='root',
            password='123456'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # 提取地点详细信息
            query_all = "SELECT Name, Place, Picture_Address, Web_Address, User_Evaluation, Score FROM `all`"
            cursor.execute(query_all)
            data_records = cursor.fetchall()
            column_names_all = [i[0] for i in cursor.description]
            data_df = pd.DataFrame(data_records, columns=column_names_all)
            
            # 提取用户行为数据
            location = 'qgj'  # 用户的表名
            query_user = "SELECT id,Name, Score FROM `%s`" % location
            cursor.execute(query_user)
            user_records = cursor.fetchall()
            column_names_user = [i[0] for i in cursor.description]
            user_behavior_df = pd.DataFrame(user_records, columns=column_names_user)

    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()

    # 将Pandas DataFrame转换为Spark DataFrame
    data_spark_df = spark.createDataFrame(data_df)
    user_behavior_spark_df = spark.createDataFrame(user_behavior_df)

    # 重命名列以匹配ALS模型的输入格式
    # 为数据集添加用户ID列
    data = data_spark_df.withColumn("User_ID", when((rand() * 10000).cast("integer") < 2500, lit("qgj")).otherwise((rand() * 10000).cast("integer").cast("string"))) \
                        .withColumnRenamed("Place","Place_Address")\
                        .withColumnRenamed("Name", "Place") \
                        .withColumnRenamed("Picture_Address", "ImagePath") \
                        .withColumnRenamed("Web_Address", "Link") \
                        .withColumnRenamed("User_Evaluation", "Evaluation")\
                        .dropna(how='any')
    # 显示数据集
    user_behavior = user_behavior_spark_df.withColumnRenamed("id", "User_ID") \
                                        .withColumnRenamed("Name", "Place") \
                                        .withColumnRenamed("Score", "Score") \
                                        .withColumn("Score", col("Score").cast("float")) 
    spark = SparkSession.builder.appName("TravelRecommendation").getOrCreate()
    indexer = StringIndexer(inputCols=["User_ID", "Place", "Score"],
                            outputCols=["User_Index", "Place_Index", "Score_index"])
    indexer.setHandleInvalid("skip")
    indexerModel = indexer.fit(data)
    indexedData = indexerModel.transform(data)
    # indexedData.show()
    # 对用户行为数据集进行索引
    indexedBehavior = indexerModel.transform(user_behavior)
    indexedBehavior.show()
    # 创建ALS模型
    als = ALS(maxIter=5, regParam=0.01, userCol="User_Index", itemCol="Place_Index", ratingCol="Score",
            coldStartStrategy="drop")

    # 拆分数据集为训练集和测试集
    (training, test) = indexedBehavior.randomSplit([0.8, 0.2])

    # 训练ALS模型
    model = als.fit(training)
    
    # 对测试集进行预测
    predictions = model.transform(test)

    # 处理推荐结果
    userRecs = model.recommendForAllUsers(10)
    userRecs = userRecs.withColumn("recommendation", explode("recommendations")) \
        .select("User_Index", "recommendation.Place_Index", "recommendation.rating")

    # 将索引列转换回原始的地点名称
    indexToStringPlace = IndexToString(inputCol="Place_Index", outputCol="Place_Name", labels=indexerModel.labelsArray[1])
    userRecs = indexToStringPlace.transform(userRecs)

    # 将用户索引列转换回原始的用户ID
    indexToStringUser = IndexToString(inputCol="User_Index", outputCol="User_ID", labels=indexerModel.labelsArray[0])
    userRecs = indexToStringUser.transform(userRecs)

    # 将推荐结果与原始数据关联，获取地点的详细信息
    userRecs = userRecs.join(indexedData, userRecs["Place_Name"] == indexedData["Place"], "inner") \
        .select(userRecs["User_ID"], indexedData["Place"], indexedData["Score"],indexedData["Imagepath"],indexedData["Evaluation"],indexedData["Link"])
    userRecs.show(10, truncate=False)
    userRecs_pandas = userRecs.toPandas()
    usercsv_shuffled = userRecs_pandas.sample(frac=1).reset_index(drop=True)
    usercsv_shuffled.to_csv('user_recommendations.csv', index=False)
    spark.stop()
modeltocsv()
