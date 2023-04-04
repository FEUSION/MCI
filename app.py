from flask import Flask, render_template, request
import pandas as pd
import xlrd
import openpyxl
import os
def abspathgen(path:str):
    dir_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(dir_path,path).replace('/','\\')


app=Flask(__name__, template_folder=abspathgen('templates'))

@app.route("/")
def default():
    return render_template("home.html")

@app.route("/home.html")
def home():
    return render_template("home.html")

@app.route("/index.html")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
