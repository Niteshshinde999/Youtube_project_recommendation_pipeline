def main():
    import psycopg2
    from pyspark.sql import SparkSession
    from pyspark.ml.feature import StringIndexer
    from pyspark.ml.recommendation import ALS
    from pyspark.sql.functions import col, explode, trim, regexp_replace, split, lit

    POSTGRES_JAR_PATH = "/mnt/c/spark/spark-3.5.2-bin-hadoop3/jars/postgresql-42.7.5.jar"

    # Initialize Spark Session with JDBC Driver
    spark = (
        SparkSession.builder
        .appName("Django-PySpark-Connection")
        .config("spark.jars", POSTGRES_JAR_PATH)  # Ensure Spark loads the JDBC driver
        .config("spark.driver.extraClassPath", POSTGRES_JAR_PATH)
        .config("spark.executor.extraClassPath", POSTGRES_JAR_PATH)
        .getOrCreate()
    )   
    
    db_url = "jdbc:postgresql://localhost:5433/youtube_project_ubuntu"
    db_user = 'user'
    db_password = 'password'
    db_properties = {"user": "user", "password": "password", "driver": "org.postgresql.Driver"}

    course_playlist = spark.read.format("jdbc")\
        .option('url', db_url)\
        .option('dbtable', "recommendations_c_playlist")\
        .option('user', db_user)\
        .option('password', db_password)\
        .option('driver', "org.postgresql.Driver")\
        .load()

    course_video = spark.read.format("jdbc")\
        .option('url',db_url)\
        .option('dbtable', "recommendations_c_videos")\
        .option('user', db_user)\
        .option('password', db_password)\
        .option('driver', "org.postgresql.Driver")\
        .load()

    user_view = spark.read.format("jdbc")\
        .option('url',db_url)\
        .option('dbtable', "recommendations_videos")\
        .option('user', db_user)\
        .option('password', db_password)\
        .option('driver', "org.postgresql.Driver")\
        .load()
    # user_view = spark.read.format("jdbc").option(url=db_url, dbtable="recommendations_videos", **db_properties).load()

    playlist_data = (
        course_playlist.select('user_id', 'thumbnail', 'category', 'playlist_id')
        .union(user_view.select('user_id', col('playlist_thumbnail').alias('thumbnail'), 'category', col('playlist').alias('playlist_id')))
    ).cache()

    video_data = (
        course_video.select('user_id', 'thumbnail', 'category', 'video_id')
        .union(user_view.select('user_id', col('video_thumbnail').alias('thumbnail'), 'category', 'video_id'))
    ).cache()

    rating_playlist_data = playlist_data.withColumn('rating', lit(1.0))
    rating_video_data = video_data.withColumn('rating', lit(1.0))

    def index(df, input_col, output_col):
        indexer = StringIndexer(inputCol=input_col, outputCol=output_col)
        model = indexer.fit(df)
        return model.transform(df).withColumn(output_col, col(output_col).cast('integer'))

    playlist_indexer = index(rating_playlist_data, 'playlist_id', 'playlist_index')
    video_indexer = index(rating_video_data, 'video_id', 'video_index')


    def train_als(df, user_col, item_col, rating_col):
        als = ALS(userCol=user_col, itemCol=item_col, ratingCol=rating_col)
        return als.fit(df)

    p_model = train_als(playlist_indexer, 'user_id', 'playlist_index', 'rating')
    v_model = train_als(video_indexer, 'user_id', 'video_index', 'rating')

    def get_recommendations(model, user_col, item_col):
        return model.recommendForAllUsers(5).withColumn('recommendation', explode(col('recommendations'))).select(user_col, col(f"recommendation.{item_col}").alias(item_col))

    p_recommendations = get_recommendations(p_model, 'user_id', 'playlist_index')
    v_recommendations = get_recommendations(v_model, 'user_id', 'video_index')

    # Mapping
    playlist_mapping = playlist_indexer.select('thumbnail', 'category', 'playlist_id', 'playlist_index').distinct()
    video_mapping = video_indexer.select('thumbnail', 'category', 'video_id', 'video_index').distinct()

    final_playlist_recommendation = p_recommendations.join(playlist_mapping, on='playlist_index', how='left').select('category', 'playlist_id', 'thumbnail', 'user_id')
    final_video_recommendation = v_recommendations.join(video_mapping, on='video_index', how='left').select('category', 'video_id', 'thumbnail', 'user_id')

    # Database cleanup and write recommendations
    conn = psycopg2.connect("dbname=youtube_project_ubuntu user=user password=password host=localhost port=5433")
    cur = conn.cursor()
    cur.execute("DELETE FROM recommendations_r_videos; ALTER SEQUENCE recommendations_r_videos_id_seq RESTART WITH 1;")
    cur.execute("DELETE FROM recommendations_r_playlists; ALTER SEQUENCE recommendations_r_playlists_id_seq RESTART WITH 1;")
    conn.commit()
    conn.close()

    final_playlist_recommendation.write.format("jdbc")\
        .option('url', db_url)\
        .option('dbtable', "recommendations_r_playlists")\
        .option('user', db_user)\
        .option('password', db_password)\
        .option('driver', "org.postgresql.Driver")\
        .mode('append')\
        .save()
    
    final_video_recommendation.write.format("jdbc")\
        .option('url', db_url)\
        .option('dbtable', "recommendations_r_videos")\
        .option('user', db_user)\
        .option('password', db_password)\
        .option('driver', "org.postgresql.Driver")\
        .mode('append')\
        .save()
    spark.stop()

if __name__ == '__main__':
    main()
