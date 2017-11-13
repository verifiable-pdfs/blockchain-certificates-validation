# -*- coding: utf-8 -*-
import os
import json
import random
import string
import logging
import pdfrw
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request
from werkzeug import secure_filename
from subprocess import check_output

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
        try:
            f = request.files['file']
            original_filename = f.filename
            temp_filename = ''.join(random.choice(string.ascii_lowercase) for i in range(6)) + "-" + secure_filename(f.filename)

            f.save(temp_filename)

            # if not a valid pdf or sth else is wrong an exception will be raised "Unexpected error"
            pdf = pdfrw.PdfReader(temp_filename)

            issuer = cleanPdfString(pdf.Info.issuer)
            address = cleanPdfString(pdf.Info.issuer_address)
            # get metadata string and convert literal unicode escape
            # sequences (only way to store unicode in PDF metadata)
            # to unicode string
            metadata_string = cleanPdfString(pdf.Info.metadata_object).encode('ascii').decode('unicode_escape')
            chainpoint_proof_string = cleanPdfString(pdf.Info.chainpoint_proof)

            if(metadata_string):
                metadata = json.loads(metadata_string)
            else:
                metadata = {}

            if(chainpoint_proof_string):
                chainpoint_proof = json.loads(chainpoint_proof_string)
                txid = chainpoint_proof['anchors'][0]['sourceId']

            # testnet "ULand " prefix
            #result = check_output(["validate-certificates", "-t", "-p", "554c616e6420", "-f", temp_filename])
            #print(result.decode("utf-8"))

            # testnet "UNicDC " prefix
            #result = check_output(["validate-certificates", "-t", "-p", "554e6963444320", "-f", temp_filename])

            # mainnet
            result = check_output(["validate-certificates", "-f", temp_filename])

            app.logger.info('Successfully validated ' + original_filename + " (" + temp_filename + ")")
            return render_template('verification.html', result_text = result.decode("utf-8"), filename = original_filename, issuer = issuer, address = address, txid = txid, metadata = metadata)

        except pdfrw.errors.PdfParseError:
            app.logger.info('Not a pdf file: ' + original_filename + " (" + temp_filename + ")")
            return render_template('verification.html', result_text = "Not a pdf file.", filename = original_filename)
#        except json.decoder.JSONDecodeError:
#            app.logger.info('No valid JSON chainpoint_proof metadata: ' + original_filename + " (" + temp_filename + ")")
#            return render_template('verification.html', result_text = "Pdf without valid JSON chainpoint_proof", filename = original_filename)
        except:
            app.logger.info('Unexpected error trying to validate ' + original_filename + " (" + temp_filename + ")")
            return render_template('verification.html', result_text = "There was an unexpected error. Please try again later.", filename = original_filename)
        finally:
            # if file was written, delete
            if os.path.isfile(temp_filename):
                os.remove(temp_filename)


def cleanPdfString(pdfString):
    if pdfString != None:
        if(pdfString.startswith('(') and pdfString.endswith(')')):
            return pdfString[1:-1]
        else:
            return pdfString
    else:
        return ""


if __name__ == '__main__':
    app.run(debug = False, host='0.0.0.0', port=8080)

