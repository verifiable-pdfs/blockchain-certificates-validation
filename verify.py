# -*- coding: utf-8 -*-
import os
import sys
import json
import configargparse
import random
import string
import logging
import pdfrw
from blockchain_certificates import __version__ as corelib_version
from blockchain_certificates.validate_certificates import validate_certificates
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request
from argparse import Namespace
from werkzeug import secure_filename
from datetime import datetime

app = Flask(__name__)
handler = RotatingFileHandler('verify.log', maxBytes=100000, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

'''
Loads and returns the configuration options (either from --config or from
specifying the specific options.
Warning: Using `flask run` for running a development server does not allow
passing custom command line options to the underlying app
'''
def load_config():
    base_dir = os.path.abspath(os.path.dirname(__file__))

    # default config is the user customized one -- defaults to sample config in
    # root directory
    default_config = os.path.join(base_dir, 'customize', 'config.ini')
    if not os.path.isfile(default_config):
        default_config = os.path.join(base_dir, 'config.ini')

    p = configargparse.getArgumentParser(default_config_files=[default_config])
    p.add('-c', '--config', required=False, is_config_file=True, help='config file path')
    p.add_argument('-t', '--testnet', action='store_true', help='specify if testnet or mainnet will be used')
    p.add_argument('--logo_text', type=str, help='text to appear under the logo')
    p.add_argument('--upload_label_text', type=str, help='text to appear above the upload PDF button')
    p.add_argument('--issuer_name', type=str, help='name of the organisation or person that issued the certificate')
    p.add_argument('--contact_name', type=str, help='name to contact for manual verification')
    p.add_argument('--contact_email', type=str, help='email to contact for manual verification')
    p.add_argument('--general_text', type=str, help='text to appear at the top of the upload PDF page')
    p.add_argument('--main_site_url', type=str, help='the URL of the website for the "Back to main website" link')
    args, _ = p.parse_known_args()
    return args

# vars() casts the Namespace object returned by configargparse
# to a dict for easier handling in the template
app.custom_config = vars(load_config())
app.custom_config['installed_version'] = corelib_version
print('Using v%s of the blockchain-certificates library' % (corelib_version,))

@app.route('/verify')
def upload_file():
    return render_template('verify.html', **app.custom_config)

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
                # app.logger.info(metadata_string)
                metadata = json.loads(metadata_string)
            else:
                metadata = {}

            # initialize txid
            txid = ""

            if(chainpoint_proof_string):
                chainpoint_proof = json.loads(chainpoint_proof_string)
                txid = chainpoint_proof['anchors'][0]['sourceId']

            # testnet "ULand " prefix
            # result = check_output(["validate-certificates", "-t", "-p", "554c616e6420", "-f", temp_filename])
            # print(result.decode("utf-8"))

            conf = Namespace(
                testnet = bool(app.custom_config.get('testnet')),
                f = [temp_filename], # validate_certificates as a lib requires a list of filenames
                issuer_identifier = None # needs a value
            )
            result = validate_certificates(conf)['results'][0]
            if 'reason' in result and result['reason'] is not None:
                if ('valid until: ' in result['reason']) or ('expired at:' in result['reason']):
                    timestamp = int(result['reason'].split(':')[1].strip())
                    result['expiry_date'] = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                elif result['reason'] == 'cert hash was revoked':
                    result['revoked'] = True

            app.logger.info('Successfully validated ' + original_filename + " (" + temp_filename + ")")

            return render_template('verification.html', result = result, filename = original_filename, issuer = issuer, address = address, txid = txid, metadata = metadata, **app.custom_config)

        except pdfrw.errors.PdfParseError:
            app.logger.info('Not a pdf file: ' + original_filename + " (" + temp_filename + ")")
            return render_template('verification.html', error = "Not a pdf file.", filename = original_filename, **app.custom_config)
    #    except json.decoder.JSONDecodeError:
    #        app.logger.info('No valid JSON chainpoint_proof metadata: ' + original_filename + " (" + temp_filename + ")")
    #        return render_template('verification.html', result_text = "Pdf without valid JSON chainpoint_proof", filename = original_filename)
        except:
            app.logger.info('Unexpected error trying to validate ' +
                            original_filename + " (" + temp_filename +
                            ") --- " + str(sys.exc_info()) )
            return render_template('verification.html', error = "There was an unexpected error. Please try again later.", filename = original_filename, **app.custom_config)
        finally:
            # if file was written, delete
            if os.path.isfile(temp_filename):
                os.remove(temp_filename)

'''
PDF metadata enclose strings with '(' and ')'. This method removes them so that
it can be properly read as json.
'''
def cleanPdfString(pdfString):
    if pdfString != None:
        if(pdfString.startswith('(') and pdfString.endswith(')')):
            clean_out_parenthesis = pdfString[1:-1]
            # if any user defined metadata contain ( or ) it is escaped
            # breaking the json conversion... so remove the escape char \
            # when before a parenthesis -- TODO: replace with re!
            return clean_out_parenthesis.replace('\\(','(').replace('\\)',')')
        else:
            return pdfString
    else:
        return ""


if __name__ == '__main__':
    app.run(debug = False, host='0.0.0.0', port=18080)

