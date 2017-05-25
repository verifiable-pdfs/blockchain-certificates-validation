# -*- coding: utf-8 -*-
import os
import json
import random
import string
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request
from werkzeug import secure_filename
from subprocess import check_output
from pdfrw import PdfReader, PdfWriter, PdfDict

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
handler = RotatingFileHandler('verify.log', maxBytes=100000, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

@app.route('/verify')
def upload_file():
    return render_template('verify.html')

@app.route('/verification', methods = ['GET', 'POST'])
def uploaded_file():
    if request.method == 'POST':
        f = request.files['file']
        original_filename = f.filename
        temp_filename = ''.join(random.choice(string.ascii_lowercase) for i in range(6)) + "-" + secure_filename(f.filename)

        f.save(temp_filename)

        try:
            # testnet "ULand " prefix
            result = check_output(["validate-certificates", "-t", "-p", "554c616e6420", "-f", temp_filename])
            #print(result.decode("utf-8"))

            # mainnet "UNicDC " prefix
            #result = check_output(["validate-certificates", "-p", "554e6963444320", "-f", temp_filename])
        except:
            app.logger.info('Unexpected error trying to validate ' + original_filename + " (" + temp_filename + ")")
            return render_template('verification.html', result_text = "There was an unexpected error. Please try again later.", filename = original_filename)
        else:
            app.logger.info('Successfully validated ' + original_filename + " (" + temp_filename + ")")
            return render_template('verification.html', result_text = result.decode("utf-8"), filename = original_filename)
        finally:
            # if file was written, delete
            if os.path.isfile(temp_filename):
                os.remove(temp_filename)

if __name__ == '__main__':
    app.run(debug = False, host='0.0.0.0', port=8080)

