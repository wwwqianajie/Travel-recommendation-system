from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, lit, when

# 创建SparkSession
spark = SparkSession.builder.appName("DataExploration").getOrCreate()

# 文件路径
file_paths = [
    "/data/丽江_cleaned_utf8.csv",
    "/data/南京_cleaned_utf8.csv",
    "/data/厦门_cleaned_utf8.csv",
    "/data/上海_cleaned_utf8.csv",
    "/data/苏州_cleaned_utf8.csv",
    "/data/台北_cleaned_utf8.csv",
    "/data/天津_cleaned_utf8.csv",
    "/data/武汉_cleaned_utf8.csv",
    "/data/香港_cleaned_utf8.csv",
    "/data/重庆_cleaned_utf8.csv"
]

# 加载所有数据集到一个DataFrame列表
dataframes = [spark.read.csv(file_path, header=True, inferSchema=True) for file_path in file_paths]

# 显示每个DataFrame的前几行以了解结构
for i, df in enumerate(dataframes):
    print(f"Dataset {i+1}:")
    df.show()

# 检查'Name'字段的列名
column_names = [df.columns for df in dataframes]

# 计算每个数据集中'Name'的出现次数
name_counts = [df.groupBy("Name").count() for df in dataframes]

# 创建一个DataFrame以更好地呈现name计数
name_counts_df = name_counts[0]
for i, df in enumerate(name_counts[1:]):
    name_counts_df = name_counts_df.union(df.withColumnRenamed('count', f'count{i+1}'))

# 为更好的可读性转置DataFrame
name_counts_df.show()

# 预处理：用空字符串填充'Name'列的NaN值
for df in dataframes:
    df = df.na.fill({'Name': ''})

# 初始化categorized_names DataFrame
categorized_names = spark.createDataFrame([], schema='')

for category, keywords in categories.items():
    # 为每个类别初始化一个列为False
    categorized_names = categorized_names.withColumn(category, lit(False))

    for keyword in keywords:
        for i, df in enumerate(dataframes):
            # 如果在'Name'中找到关键字，则标记为True
            categorized_names = categorized_names.withColumn(category, when(col("Name").contains(keyword), True).otherwise(col(category)))

# 计算每个城市每个类别的True数量
category_counts = categorized_names.groupBy("City").sum()

# 为更好的可读性转置DataFrame
category_counts.show()

# 显示每个城市的'Name'值的随机样本
sample_names = {city: df.select("Name").orderBy(rand()).limit(10).collect() for city, df in zip(name_counts_df.index, dataframes)}
print(sample_names)

# 根据关键词进行分类逻辑
def classify_name(top_keywords, categories):
    classified_categories = []
    for keywords in top_keywords:
        category_assigned = False
        for category, category_keywords in categories.items():
            if any(keyword in category_keywords for keyword in keywords):
                classified_categories.append(category)
                category_assigned = True
                break
        if not category_assigned:
            classified_categories.append("未分类")
    return classified_categories

classified_categories = classify_name(top_keywords, refined_categories)

# 显示部分结果
classified_categories.show()

# 停止SparkSession
spark.stop()