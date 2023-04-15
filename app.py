from flask import Flask, render_template, request, session, redirect, url_for, flash
import pandas as pd
import io
import xlrd
import xlwt
import openpyxl
import os
import secrets
import plotly.graph_objs as go
from plotly.offline import plot
import LocalMeltcurveAnalysis.meltcurve_interpreter as mlt
import threading
from queue import Queue
import psycopg2
from sqlalchemy import create_engine
from ydata_profiling import ProfileReport
import ydata_profiling.config as config
config.Html.navbar_show:bool = True


hostname = '192.168.0.146'
meltdatabase = 'MeltFiles'
username = 'postgres'
pwd = 1100
portid = 5432
melt_conn = psycopg2.connect(
    host=hostname,
    dbname=meltdatabase,
    user=username,
    password=pwd,
    port=portid
)


ctdatabase = 'CTFiles'
ct_conn = psycopg2.connect(
    host=hostname,
    dbname=ctdatabase,
    user=username,
    password=pwd,
    port=portid
)
obj = mlt.MeltcurveInterpreter()


def genrate_token():
    token = secrets.token_hex(2)
    return token


def abspathgen(path: str):
    dir_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(dir_path, path).replace('/', '\\')

def type_definer(text:str):
    if 'Text' in text:
        return 'varchar(50)'
    else:
        return 'FLOAT(50)'

ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

app = Flask(__name__, template_folder=abspathgen('templates'))

app.secret_key = '123'


@app.after_request
def clear_session(response):
    if request.method == 'GET':
        session.clear()
    return response


@app.route("/")
def default():
    return render_template("home.html")


@app.route("/home.html")
def home():
    return render_template("home.html")


@app.route("/index.html")
def index():
    return render_template("index.html")


@app.route("/Melt_file_upload", methods=['POST', 'GET'])
def Melt_file_upload():
    if request.method == 'POST':

        username = request.form.getlist("input-text")[0]
        username = str(username)
        print(type(username))
        file = request.files.get('file')
        file_data = file.read()
        print(file.filename)
        if file.filename.endswith('.xlsx') or file.filename.endswith('.xls') and 'Melt Extracted' in file.filename:
            try:
                data = pd.read_excel(io.BytesIO(file_data), engine='xlrd')
            except:
                data = pd.read_excel(io.BytesIO(file_data))
            gen_token = genrate_token()
            gen_token_path = str(gen_token) + '.xlsx'
            table_name = str(username) + str(gen_token)
            # filepath = os.path.join(app.config["UPLOAD_FOLDER1"], username + ' ' + gen_token_path).replace('/', '\\')
            # data.to_excel(filepath)
            cur = melt_conn.cursor()
            values = '('
            for cols in data.columns:
                cols = cols.replace('.', '')
                values += cols + ' ' + type_definer(cols) + ','
            values = values[:-1]
            values = values + ')'

            query = 'create table' + ' ' + table_name + ' ' + values

            cur.execute(query)
            melt_conn.commit()
            engine = create_engine("postgresql://postgres:1100@192.168.0.146/MeltFiles")
            data.to_sql(str(table_name), engine, if_exists='replace')
            cur.close()


            del file
            # return render_template("index.html", success_message='File Uplaoded Successfully!')
            flash(f'File Uplaoded Successfully! Your Token : {gen_token}')
            return redirect(url_for('Melt_file_upload'))
        else:
            if not file.filename.endswith('.xlsx') and not file.filename.endswith('.xls'):
                return render_template("index.html", message='Invalid File Format!!')
            elif 'MELT' not in file.filename:
                return render_template("index.html", message='Please only Upload MELT Extracted Data!')
            else:
                return render_template("index.html", message='No file selected')
    return render_template("index.html")


@app.route("/Ct_file_upload", methods=['POST', 'GET'])
def Ct_file_upload():
    if request.method == 'POST':

        username = request.form.getlist("input-text")[0]
        username = str(username)
        file = request.files.get('file')
        file_data = file.read()
        if file.filename.endswith('.xlsx') or file.filename.endswith('.xls') and 'CT Extracted' in file.filename:
            try:
                data = pd.read_excel(io.BytesIO(file_data), engine='xlrd')
            except:
                data = pd.read_excel(io.BytesIO(file_data))
            gen_token = genrate_token()
            gen_token_path = str(gen_token) + '.xlsx'
            table_name = str(username) + str(gen_token)
            # filepath = os.path.join(app.config["UPLOAD_FOLDER1"], username + ' ' + gen_token_path).replace('/', '\\')
            # data.to_excel(filepath)
            cur = ct_conn.cursor()
            values = '('
            for cols in data.columns:
                cols = cols.replace('.', '')
                values += cols + ' ' + type_definer(cols) + ','
            values = values[:-1]
            values = values + ')'

            query = 'create table' + ' ' + table_name + ' ' + values

            cur.execute(query)
            ct_conn.commit()
            engine = create_engine("postgresql://postgres:1100@192.168.0.146/CTFiles")
            data.to_sql(str(table_name), engine, if_exists='replace')
            cur.close()

            del file
            # return render_template("index.html", success_message='File Uplaoded Successfully!')
            flash(f'File Uplaoded Successfully! Your Token : {gen_token}')
            return redirect(url_for('Ct_file_upload'))
        else:
            if not file.filename.endswith('.xlsx') and not file.filename.endswith('.xls'):
                return render_template("index.html", message='Invalid File Format!!')
            elif 'MELT' not in file.filename:
                return render_template("index.html", message='Please only Upload CT Extracted Data!')
            else:
                return render_template("index.html", message='No file selected')
    return render_template("index.html")


@app.route("/Melt.html", methods=['POST', 'GET'])
def Melt():
    if request.method == 'POST':

        username = request.form.getlist("input-text")[0]
        token = request.form.getlist("input-text")[1]
        # file_name = username + ' ' + token + '.xlsx'
        # file_path = os.path.join('static\\uploaded_files\\Melt', file_name).replace('/', '\\')
        table_name = str(username) + str(token)
        query = "SELECT * FROM "+table_name
        sqldata= pd.read_sql(query,melt_conn)
        data = obj.data_read(data = sqldata, path=None, index=True)
        fig = obj.plot(data=data, save=True)
        plot_html = plot(fig, output_type='div')

        return render_template("Melt.html", plot_html=plot_html)
    else:
        return render_template("Melt.html")


@app.route("/CT.html", methods=['POST', 'GET'])
def CT():
    if request.method == 'POST':

        username = request.form.getlist("input-text1")[0]
        token = request.form.getlist("input-text1")[1]
        table_name = str(username) + str(token)
        query = "SELECT * FROM "+table_name
        sqldata= pd.read_sql(query,ct_conn)
        data = obj.data_read(data = sqldata,path=None, index=True)
        fig = obj.plot(data=data, save=True)
        plot_html = plot(fig, output_type='div')

        return render_template("CT.html", plot_html=plot_html)
    else:
        return render_template("CT.html")

    # return render_template("Melt.html")


@app.route("/help.html")
def help():
    return render_template("help.html")


@app.route("/homepage.html")
def homepage():
    return render_template("homepage.html")


def run_meltcurve_interpreter(table_name, queue):

    with app.app_context():
        obj2 = mlt.MeltcurveInterpreter()
        query = "SELECT * FROM " + table_name
        sqldata = pd.read_sql(query, melt_conn)
        data = obj2.data_read(data=sqldata, path=None, index=True)
        dataframe = obj2.feature_detection(return_values=True)
        table = dataframe.to_html(classes="table", header="true")
        queue.put(table)


def reportgen(table_name2,queue):

    with app.app_context():
        obj2 = mlt.MeltcurveInterpreter()
        query = "SELECT * FROM " + table_name2
        sqldata = pd.read_sql(query, melt_conn)
        data = obj2.data_read(data = sqldata,path=None, index=True)
        dataframe = obj2.feature_detection(return_values=True)
        obj2.report(dataa=dataframe, file_name=table_name2)
        queue.put(None)
def stats(table_name3,queue):

    with app.app_context():
        obj2 = mlt.MeltcurveInterpreter()
        query = "SELECT * FROM " + table_name3
        sqldata = pd.read_sql(query, melt_conn)
        data = obj2.data_read(data = sqldata,path=None, index=True)
        dataframe = obj2.feature_detection(return_values=True)3
        report = ProfileReport(dataframe, title="Profiling Report", config_file=abspathgen('config.json'))
        queue.put(report)

@app.route("/analytics.html", methods=['GET', 'POST'])
def analytics():
    if 'loaded' not in session:
        session['loaded'] = True

    if request.method == 'POST':
        username = request.form.getlist("input-text3")[0]
        token = request.form.getlist("input-text3")[1]
        table_name = str(username) + str(token)
        # query = "SELECT * FROM "+table_name
        # sqldata= pd.read_sql(query,melt_conn)

        result_queue = Queue()
        # Start the MeltcurveInterpreter in a separate thread
        thread = threading.Thread(target=run_meltcurve_interpreter, args=(table_name, result_queue))
        thread.start()
        table = result_queue.get()
        return render_template("analytics.html", table=table)
    else:
        return render_template("analytics.html")


@app.route("/report.html", methods=['GET', 'POST'])
def genreport():
    if 'loaded' not in session:
        session['loaded'] = True

    if request.method == 'POST':
        username2 = request.form.getlist("input-text4")[0]
        token2 = request.form.getlist("input-text4")[1]

        table_name2 = str(username2) + str(token2)

        result_queue2 = Queue()
        # Start the MeltcurveInterpreter in a separate thread
        thread2 = threading.Thread(target=reportgen, args=(table_name2, result_queue2))
        thread2.start()
        thread2.join()
        flash(f'Report Downloaded Successfully : Downloaded at {os.path.join(os.path.expanduser("~"),"Downloads")}')
        return render_template("report.html")

    else:
        return render_template("report.html")

@app.route("/statistics.html", methods=['GET','POST'])
def stat():
    if 'loaded' not in session:
        session['loaded'] = True

    if request.method == 'POST':
        username3 = request.form.getlist("input-text5")[0]
        token3 = request.form.getlist("input-text5")[1]

        table_name3 = str(username3) + str(token3)

        result_queue3 = Queue()
        # Start the MeltcurveInterpreter in a separate thread
        thread3 = threading.Thread(target=stats, args=(table_name3, result_queue3))
        thread3.start()
        thread3.join()
        pf = result_queue3.get()
        return render_template("statistics.html",profile_report=pf.to_html())

    else:
        return render_template("statistics.html")



app.run(debug=True, threaded=True)
