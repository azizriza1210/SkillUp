# Library Imports
from datetime import datetime, timedelta
import os
import pandas as pd
import re
import requests
import json
import psycopg2
from psycopg2 import pool
from psycopg2.extras import execute_values

# Azure OpenAI Integration
url = "https://skillupllm.openai.azure.com/openai/deployments/SkillUp-Embedding/embeddings?api-version=2024-02-01"
headers = {'Content-Type': 'application/json', 'api-key': '8575d0680b2e48599a9058bf62713335'}

# PostgreSQL Configuration
conn_string = (
    "host=c-skillup-vector.hh3bwvk75ljfl6.postgres.cosmos.azure.com "
    "user=citus dbname=skillup-citus password=SkillUp123 sslmode=require"
)

# Create Connection Pool
postgreSQL_pool = psycopg2.pool.SimpleConnectionPool(1, 20, conn_string)

if postgreSQL_pool:
    conn = postgreSQL_pool.getconn()
    cursor = conn.cursor()

def select_data(cursor, conn, folder_path='D:\\Codelabs\\Kompetisi\\AIC Compfest\\Projek\\Done Embed'):
    for csv_file in [f for f in os.listdir(folder_path) if f.endswith('.csv')]:
        file_path = os.path.join(folder_path, csv_file)
        df_data = pd.read_csv(os.path.join(folder_path, csv_file)).drop_duplicates().fillna("")
        try : 
            print(type(df_data['Skill']))
        except Exception as e :
            df_data['Skill'] = ""

        df_data['Posted On'] = df_data['Posted On'].apply(convert_posted_on)
        df_data['Text Embed'] = df_data['Job Titles'] + ' ' + df_data['Job Details'] + ' ' + df_data['Skill']
        df_data['Text Embed'] = df_data['Text Embed'].str.replace('\n', '').apply(embed_text)
        store_data(cursor, conn, df_data.dropna(subset=["Text Embed"]))

        # Ubah nama file dengan menambahkan '_done.csv'
        new_file_name = csv_file.replace('.csv', '_done.csv')
        new_file_path = os.path.join(folder_path, new_file_name)
        os.rename(file_path, new_file_path)
        print(f"File {csv_file} telah diubah namanya menjadi {new_file_name}")

def embed_text(text):
    try:
        response = requests.post(url, headers=headers, data=json.dumps({"input": text}))
        return response.json()['data'][0]['embedding']
    except Exception:
        return None

def convert_posted_on(posted_on):
    num, unit = int(re.findall(r'\d+', posted_on)[0]), posted_on.split()[1]
    units = {'Reposted': num, 'week': num, 'weeks': num, 'month': num * 4, 'day': num, 'hours': num / 24}
    return datetime.now() - timedelta(weeks=units.get(unit, 0))

def store_data(cursor, conn, df_data):
    execute_values(cursor, """
        INSERT INTO data_scrapping (
            company_names, job_titles, posted_on, job_details, skill, 
            images, type_location, location, embedding
        ) VALUES %s
    """, df_data.apply(lambda row: tuple(row), axis=1))
    conn.commit()

# Execute Data Selection and Storage
select_data(cursor, conn)
