import psycopg2
from psycopg2 import pool 
from psycopg2.extras import execute_values

host = "c-skillup-vector.hh3bwvk75ljfl6.postgres.cosmos.azure.com"
dbname = "skillup-citus"
user = "citus"
password = "SkillUp123"
sslmode = "require"

conn_string = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(host, user, dbname, password, sslmode)

postgreSQL_pool = None
if (not postgreSQL_pool):
    print("Connection pool created successfully")
    postgreSQL_pool = psycopg2.pool.SimpleConnectionPool(1, 20,conn_string)
    
    conn = postgreSQL_pool.getconn()

cursor = conn.cursor()

# Create table to store embeddings and metadata
table_create_command = """
CREATE TABLE data_scrapping (
    id bigserial primary key, 
    company_names text,
    job_titles text,
    posted_on date,
    job_details text,
    skill text,
    images text,
    type_location text,
    location text
);
            """

cursor.execute(table_create_command)
cursor.close()
conn.commit()
