import re
import pandas as pd
import sqlite3 as sql3
from flask import Flask, jsonify, appcontext_popped

from flask import request
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from

app = Flask(__name__)

"""Review: Good, penempatan read data diimplementasi sesuai yang disarankn yah
tujuan ditaruh diatas setelah import library buat mudahin trace code kalau ada update data
"""
#load dari data tweet
data = pd.read_csv(r"DATA/data.csv", encoding="latin-1")

#Load dari data Kamus Alay
alay_dict = pd.read_csv(r"DATA/new_kamusalay.csv", encoding="latin-1", header=None)
alay_dict = alay_dict.rename(columns={0: 'original', 
                                      1: 'replacement'})

#Load dari data Abusive
abusive_dict = pd.read_csv("DATA/abusive.csv")

#Cleaning preprocessing
def lowercase(text):
    return text.lower()

def remove_unnecessary_char(text):
    text = re.sub('\n',' ',text) # Remove every '\n'
    text = re.sub('rt',' ',text) # Remove every retweet symbol
    text = re.sub('user',' ',text) # Remove every username
    text = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))',' ',text) # Remove every URL
    text = re.sub('  +', ' ', text) # Remove extra spaces
    return text

def remove_nonaplhanumeric(text):
    text = re.sub('[^0-9a-zA-Z]+', ' ', text) 
    return text

alay_dict_map = dict(zip(alay_dict['original'], alay_dict['replacement']))
def normalize_alay(text):
    return ' '.join([alay_dict_map[word] if word in alay_dict_map else word for word in text.split(' ')])

"""Review: ini masih eror. StopweordRemovalFactory buat apa ya? kalau mau dipake pastiin sudah di import library nya
silahkan install lib berikut: pip3 install stopwords
kalau nggk dipakai dalam preprocess(text) lebih baik dihapus aja karna akan memakan memory ketika execute
"""
# def stopword_remove(teks): 
#     from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
#     stop_factory = StopWordRemoverFactory()
#     data = stop_factory.get_stop_words()
#     teks = teks.split()
#     teks_normal = ''
#     for str in teks:
#         if(bool(str not in data)):
#             teks_normal = teks_normal + ' ' + str
#     return teks_normal


def preprocess(text):
    text = lowercase(text) # 1
    text = remove_nonaplhanumeric(text) # 2
    text = remove_unnecessary_char(text) # 2
    text = normalize_alay(text) # 3
    return text

conn = sql3.connect('database.db')
c = conn.cursor()
c.execute('SELECT name from sqlite_master where type= "table"')
print(c.fetchall())


app.json_encoder = LazyJSONEncoder
swagger_template = dict(
    info={
        'title': LazyString(lambda: 'API Documentation For Data Processing and Modeling'),
        'version': LazyString(lambda: '1.0.0'),
        'description': LazyString(lambda: 'Dokumentasi API untuk data Processing dan Modeling'),
    },
    host=LazyString(lambda: request.host)
)
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": '/docs',
            "route": '/docs.json',
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}
swagger = Swagger(app, template=swagger_template, 
                  config=swagger_config)

@swag_from("docs/landingpage.yml", methods=['GET'])
@app.route('/', methods=['GET'])
def hello_world():
    json_response = {
        'status_code': 200,
        'description': "DISINI KASIH JUDUL APLIKASI SESUAI REPORT",
        'data': "Binar Academy - Nama - DSC 7",
    }

    response_data = jsonify(json_response)
    return response_data

# End Flask Template

@swag_from("docs/text_processing.yml", methods=['POST'])
@app.route('/text-processing', methods=['POST'])
def text_processing():
    
    text = request.form.get('text')

    json_response = {
        'status_code': 200,
        'description': "Teks yang telah diproses",
        'data': preprocess(text),
    }

    response_data = jsonify(json_response)
    return response_data

@swag_from("docs/text_processing_file.yml", methods=['POST'])
@app.route('/text-processing-file1', methods=['POST'])
def text_processing_file():
    
    #Upload File
    file = request.files.getlist('file')[0]

    """Review: tambahin encoding='latin-1' sesuai hasil solving bareng2 di live FD"""
    #Import file csv ke pandas.
    data = pd.read_csv(file, encoding='latin-1')

    #ambil teks yang akan diproses dalam format list
    # text = data.text.to_list()

    #Lakukan Cleaning Pada Teks
    cleaned_text = []
    for text in data["Tweet"]:
        cleaned_text.append(preprocess(text))

    json_response = {
        'status_code': 200,
        'description': "Teks yang telah diproses",
        'data': cleaned_text,
    }

    response_data = jsonify(json_response)
    return response_data

if __name__ == '__main__':
    app.run()
