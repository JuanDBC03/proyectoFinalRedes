from fastapi import FastAPI
from pyspark.sql import SparkSession
import os

app = FastAPI()

mongo_uri = os.getenv("MONGO_CONNECTION_STRING", "mongodb://mongo:27017")
database_name = "test" # Base de datos por defecto de mongo

@app.get("/api/v1/analytics/estadisticas")
def get_estadisticas():
    # Inicializar PySpark con soporte para MongoDB
    spark = SparkSession.builder \
        .appName("EventosAnalytics") \
        .config("spark.mongodb.input.uri", "mongodb://mongo:27017/db_eventos.evento") \
        .config("spark.mongodb.output.uri", "mongodb://mongo:27017/db_eventos.evento") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1") \
        .getOrCreate()
        
    try:
        # Extraer datos de MongoDB a un DataFrame de Spark
        df = spark.read.format("mongo").load()
        
        # Validar si hay datos
        if df.count() == 0:
            return {
                "status": "success",
                "message": "No hay datos suficientes para procesar analíticas en la colección 'eventos' de MongoDB."
            }
        
        # Transformación y Agregaciones con PySpark (ETL)
        df.createOrReplaceTempView("eventos_view")
        
        # 1. Conteo total de registros
        total_eventos = spark.sql("SELECT count(*) as total FROM eventos_view").collect()[0]["total"]
        
        columnas = df.columns
        resumen_agrupado = {}
        
        # 2. Agrupaciones analíticas (ETL Distribuido)
        if "estado" in columnas:
            df_estado = spark.sql("SELECT estado, count(*) as cantidad FROM eventos_view GROUP BY estado")
            resumen_agrupado["por_estado"] = [row.asDict() for row in df_estado.collect()]
            
        if "tipo" in columnas:
            df_tipo = spark.sql("SELECT tipo, count(*) as cantidad FROM eventos_view GROUP BY tipo")
            resumen_agrupado["por_tipo"] = [row.asDict() for row in df_tipo.collect()]
            
        if "cupoMaximo" in columnas and "participantes" in columnas:
            # Ocupación global de la universidad
            df_ocupacion = spark.sql("""
                SELECT 
                    SUM(size(participantes)) as total_inscritos,
                    SUM(cupoMaximo) as total_cupos_ofertados,
                    ROUND(AVG(size(participantes) / cupoMaximo) * 100, 2) as ocupacion_promedio_porcentual
                FROM eventos_view 
                WHERE cupoMaximo > 0
            """)
            resumen_agrupado["ocupacion"] = [row.asDict() for row in df_ocupacion.collect()][0]
            
        if "creadoPor" in columnas:
            df_docentes = spark.sql("SELECT creadoPor, count(*) as cantidad_eventos FROM eventos_view GROUP BY creadoPor ORDER BY cantidad_eventos DESC LIMIT 5")
            resumen_agrupado["top_docentes"] = [row.asDict() for row in df_docentes.collect()]
            
        return {
            "status": "success",
            "message": "Procesamiento de datos con PySpark completado exitosamente",
            "metadata": {
                "motor": "Apache Spark",
                "version": spark.version,
                "arquitectura": "Docker Swarm"
            },
            "estadisticas": {
                "total_registros_procesados": total_eventos,
                "columnas_detectadas": columnas,
                "agrupaciones": resumen_agrupado
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Hubo un error durante el job de PySpark",
            "error_detail": str(e)
        }
