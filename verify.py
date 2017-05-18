# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from werkzeug import secure_filename
from subprocess import check_output
app = Flask(__name__)

@app.route('/verify')
def upload_file():
   return render_template('verify.html')

@app.route('/verification', methods = ['GET', 'POST'])
def uploaded_file():
   if request.method == 'POST':
      f = request.files['file']
      f.save(secure_filename(f.filename))
      #if f exists and is file do check......
      result = check_output(["validate-certificates", "-t", "-p",
                             "554c616e6420", "-f", f.filename])
      return result.decode("utf-8")
      #return render_template('verification.html')

if __name__ == '__main__':
   app.run(debug = False, host='0.0.0.0', port=8080)

