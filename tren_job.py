import json
from flask import Flask, request
from flask_cors import CORS

import requests
from psycopg2 import pool 
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import numpy as np
import pandas as pd
import re

from openai import AzureOpenAI

app = Flask(__name__)
CORS(app)

# CONNECT TO POSTGRESQL
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
# END POSTGRESQL

# EMBEDDING AZURE
url = "https://skillupllm.openai.azure.com/openai/deployments/SkillUp-Embedding/embeddings?api-version=2024-02-01"

headers = {
  'Content-Type': 'application/json',
  'api-key': '8575d0680b2e48599a9058bf62713335'
}
# END EMBEDDING AZURE

# AZURE OPENAI
client = AzureOpenAI(
    api_key="8575d0680b2e48599a9058bf62713335",  
    api_version="2024-02-01",
    azure_endpoint="https://skillupllm.openai.azure.com/"
)
    
deployment_name = 'SkillUp-4o'
# END AZURE OPENAI

# FUNCTION
# Fungsi untuk membersihkan job_titles
def clean_job_title(title):
    title = str(title).lower()
    if "science" in title.lower():
        title = title.lower().replace("science", "scientist")
    if "engineering" in title.lower():
        title = title.lower().replace("engineering", "engineer")
    if "analytics" in title.lower():
        title = title.lower().replace("analytics", "analyst")
    if "ds" in title.lower():
        title = title.lower().replace("ds", "data scientist")
    if "front end" in title.lower():
        title = title.lower().replace("front end", "frontend")
    if "(" in title.lower():
        title = title.lower().replace("(", ",")
    if "lead" in title.lower():
        title = title.lower().replace("lead", "")
    if "senior" in title.lower():
        title = title.lower().replace("senior", "")
    if "remote" in title.lower():
        title = title.lower().replace("remote", "")
    if "sr." in title.lower():
        title = title.lower().replace("sr.", "")
    title = re.sub(r'\b(intern(ship)?|freelance)\b', '', title, flags=re.IGNORECASE)
    title = re.sub(r'[()]', '', title)
            
    return title.strip()
# END FUNCTION

# GET RELEVANT DATA
@app.route("/tren_job", methods=['POST'])
def tren_job():
    # Extract input data from JSON request
    job_category = request.json.get('job_category')
    payload = json.dumps({"input": job_category})
    # Send a POST request and get the query embedding
    responses = requests.request("POST", url, headers=headers, data=payload)
    query_embedding = responses.json()['data'][0]['embedding']

    try:
        # Execute the SQL query to retrieve relevant data
        cursor.execute("""
                        SELECT company_names, job_titles, posted_on, job_details, skill, images, type_location, location,
                        (1 - (embedding <=> %s)) as similarity FROM data_scrapping 
                        WHERE 1 - (embedding <=> %s) > %s
                        ORDER BY similarity DESC
                        """, (str(query_embedding), str(query_embedding), str(0.1)))
    except Exception as e:
        print("error : ", e)

    # Fetch all the data
    data = cursor.fetchall()

    # Get the column names from the cursor description
    column_names = [desc[0] for desc in cursor.description]

    # Convert the data to a pandas DataFrame
    df = pd.DataFrame(data, columns=column_names)

    # Menerapkan fungsi ke kolom 'Job Title'
    df.drop_duplicates(inplace=True)
    df.drop_duplicates(subset=['company_names','job_titles','skill','type_location','location'])
    df['job_titles'] = df['job_titles'].apply(clean_job_title)

    prompt_final = '''
    ini adalah list job title Backend dari hasil pengambilan data di linkedin. berikan saya 5 job yang paling banyak dicari dari list berikut :
    '''+str(df['job_titles'].to_list())+'''

    Terdapat aturan yang harus kamu patuhi :
    1. Hasil keluaran wajib dalam format seperti contoh di bawah :
    [
    {'job_title':'Nama Job','total':45},
    {'job_title':'Nama Job','total':17},
    {'job_title':'Nama Job','total':11},
    {'job_title':'Nama Job','total':10},
    {'job_title':'Nama Job','total':6}
    ]
    2. Tidak boleh ada keluaran lain selain pada poin 1
    3. Jangan sampai ada nama tempat di hasilnya, betul betul hanya nama job
    4. Jangan sampe ada yang double job misal 'data warehouse data engineer'
    5. Pekerjaan yang dicari adalah yang berkaitan dengan '''+job_category+'''
    6. Jangan sampai ada nama job yang double, misal sebelumnya sudah ada "data engineer" namun di nama job berikutnya terdapat "it data engineer" cukup satu saja "data engineer""'''

    response = client.chat.completions.create(model=deployment_name, messages=[{"role": "user", "content": prompt_final}], stream=False, max_tokens=2000, temperature=0 )
    result = response.choices[0].message.content

    # Membersihkan string dan mengganti tanda kutip tunggal dengan kutip ganda
    cleaned_string = result.replace("'", '"').replace("\n", "").replace("```json", "").replace("```", "").strip()

    # Mengonversi string menjadi JSON
    json_data = json.loads(cleaned_string)

    # Menampilkan hasil
    return(json_data)
# END GET RELEVANT DATA

if __name__ == "__main__":
    app.run(debug=True)