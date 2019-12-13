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
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from flask_cors import cross_origin
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
    p.add_argument('--blockchain_services', type=str,
                   default='{ "services": [ {"blockcypher":{} } ], "required_successes": 1}',
                   help='Which blockchain services to use and the minimum required successes')
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

def render_invalid_template(error, original_filename, temp_filename):
    app.logger.error('Unexpected error trying to validate ' +
        original_filename + " (" + temp_filename +
        ") --- " + repr(error) )
    result = { 'status': 'invalid' }
    return render_template('verification-v0.html', result = result, filename = original_filename, **app.custom_config)

def delete_tmp_file(temp_filename):
    # if file was written, delete
    if os.path.isfile(temp_filename):
        os.remove(temp_filename)


@app.route('/verification-api', methods = ['OPTIONS', 'POST'])
@cross_origin()
def uploaded_file_api():
    try:
        f = request.files['file']
        original_filename = f.filename
        temp_filename = ''.join(random.choice(string.ascii_lowercase) for i in range(6)) + "-" + secure_filename(f.filename)

        f.save(temp_filename)

        # if not a valid pdf or sth else is wrong an exception will be raised "Unexpected error"
        pdf = pdfrw.PdfReader(temp_filename)

        issuer = cleanPdfString(pdf.Info.issuer)
        chainpoint_proof_string = cleanPdfString(pdf.Info.chainpoint_proof)
        if '/version' in pdf.Info:
            version = pdf.Info.version
            if version == '1':
                # TODO: Remove empty metadata_object from metadata v1
                # issuer is a json string in metadata v1
                issuer_json = json.loads(issuer)
                address = issuer_json['identity']['address']
                issuer = issuer_json['name'].encode('ascii').decode('unicode_escape')
                metadata_string = cleanPdfString(pdf.Info.metadata).encode('ascii').decode('unicode_escape')
            else:
                res = {'detail': 'Invalid metadata version in the PDF.'}
                return make_response(jsonify(res), 400)
        else:
            version = '0'
            address = cleanPdfString(pdf.Info.issuer_address)
            # get metadata string and convert literal unicode escape
            # sequences (only way to store unicode in PDF metadata)
            # to unicode string
            metadata_string = cleanPdfString(pdf.Info.metadata_object).encode('ascii').decode('unicode_escape')

        if metadata_string:
            metadata = json.loads(metadata_string)
            # If we have a metadata version, sort items by order and remove those with hide: True
            if version != '0':
                visible_metadata = [val for val in metadata.values() if (
                    not 'hide' in val or not val['hide']
                )]
                metadata = sorted(
                    visible_metadata,
                    key = lambda val: val['order'] if 'order' in val else 0
                )
            else:
                # It's the old metadata format, transform to the new one
                # Extract issuer and address and transform metadata into list of objects
                issuer = metadata.pop('issuer')
                if not address:
                    address = metadata.pop('issuer_address')
                metadata_list = []

                LABELS_ORDERING = [
                    'First Name',
                    'Fathers Name',
                    'Last Name',
                    'Degree Type',
                    'Program of Study',
                    'Date of Issue'
                ]

                i = 0
                for l in LABELS_ORDERING:
                    if l in metadata and metadata[l]:
                        metadata_list.append({ 'label': l, 'order': i, 'value': metadata[l] })
                    i += 1
                metadata = metadata_list
        else:
            metadata = {}

        # initialize txid
        txid = ""

        if chainpoint_proof_string:
            chainpoint_proof = json.loads(chainpoint_proof_string)
            txid = chainpoint_proof['anchors'][0]['sourceId']
    except pdfrw.errors.PdfParseError:
        delete_tmp_file(temp_filename)
        app.logger.info('Not a pdf file: ' + original_filename + " (" + temp_filename + ")")
        res = {'detail': 'Not a valid PDF file.'}
        return make_response(jsonify(res), 400)
    except Exception as error:
        delete_tmp_file(temp_filename)
        res = {'detail': 'Could not extract the validation proof from the PDF file'}
        return make_response(jsonify(res), 400)

    # Check if all of these exist in the PDF:
    # - txid
    # - address
    if not (txid and address and issuer):
        delete_tmp_file(temp_filename)
        res = {'detail': 'Could not extract the validation proof from the PDF file'}
        return make_response(jsonify(res), 400)

    try:
        conf = Namespace(
            testnet = bool(app.custom_config.get('testnet')),
            f = [temp_filename], # validate_certificates as a lib requires a list of filenames
            issuer_identifier = None, # needs a value
            blockchain_services = app.custom_config.get('blockchain_services')
        )

        result = validate_certificates(conf)['results'][0]
        if 'reason' in result and result['reason'] is not None:
            if ('valid until: ' in result['reason']) or ('expired at:' in result['reason']):
                timestamp = int(result['reason'].split(':')[1].strip())
                result['expiry_date'] = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            elif result['reason'] == 'address was revoked':
                result['revoked'] = 'address'
            elif result['reason'] == 'batch was revoked':
                result['revoked'] = 'batch'
            elif result['reason'] == 'cert hash was revoked':
                result['revoked'] = 'certificate'
        if version == '0':
            id_proofs = None
        else:
            id_proofs = 0
            if 'verification' in result and result['verification'] is not None:
                for _, value in result['verification'].items():
                    if value['success']:
                        id_proofs += 1

        return jsonify(dict(result = result, filename = original_filename, issuer = issuer, id_proofs=id_proofs, address=address, txid=txid, metadata=metadata))
    except Exception as error:
        app.logger.error('Unexpected error trying to validate ' +
                        original_filename + " (" + temp_filename +
                        ") --- " + repr(error) )
        res = {}
        if "incompatible with current block chain" in str(error):
            res['result'] = {"result": {"status": "invalid"}}
            res['filename'] = original_filename
        else:
            res['detail'] = "There was an unexpected error. Please try again later or contact support"
        return jsonify(res)
    finally:
        delete_tmp_file(temp_filename)


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
            chainpoint_proof_string = cleanPdfString(pdf.Info.chainpoint_proof)
            if '/version' in pdf.Info:
                version = pdf.Info.version
                if version == '1':
                    # TODO: Remove empty metadata_object from metadata v1
                    # issuer is a json string in metadata v1
                    issuer_json = json.loads(issuer)
                    address = issuer_json['identity']['address']
                    issuer = issuer_json['name'].encode('ascii').decode('unicode_escape')
                    metadata_string = cleanPdfString(pdf.Info.metadata).encode('ascii').decode('unicode_escape')
                else:
                    raise ValueError('Unsupported metadata version')
            else:
                version = '0'
                address = cleanPdfString(pdf.Info.issuer_address)
                # get metadata string and convert literal unicode escape
                # sequences (only way to store unicode in PDF metadata)
                # to unicode string
                metadata_string = cleanPdfString(pdf.Info.metadata_object).encode('ascii').decode('unicode_escape')

            if metadata_string:
                metadata = json.loads(metadata_string)
                # If we have a metadata version, sort items by order and remove those with hide: True
                if version != '0':
                    visible_metadata = [val for val in metadata.values() if (
                        not 'hide' in val or not val['hide']
                    )]
                    metadata = sorted(
                        visible_metadata,
                        key = lambda val: val['order'] if 'order' in val else 0
                    )
            else:
                metadata = {}

            # initialize txid
            txid = ""

            if chainpoint_proof_string:
                chainpoint_proof = json.loads(chainpoint_proof_string)
                txid = chainpoint_proof['anchors'][0]['sourceId']
        except pdfrw.errors.PdfParseError:
            delete_tmp_file(temp_filename)
            app.logger.info('Not a pdf file: ' + original_filename + " (" + temp_filename + ")")
            return render_template('verification-v0.html', error = "Not a pdf file.", filename = original_filename, **app.custom_config)
        except Exception as error:
            delete_tmp_file(temp_filename)
            return render_invalid_template(error, original_filename, temp_filename)

        # Check if all of these exist in the PDF:
        # - txid
        # - address or 'issuer_address' inside the metadata object
        if not (txid and (address or ('issuer_address' in metadata and metadata['issuer_address']))):
            delete_tmp_file(temp_filename)
            return render_invalid_template(
                'Could not find txid in PDF file', original_filename, temp_filename)

        try:
            conf = Namespace(
                testnet = bool(app.custom_config.get('testnet')),
                f = [temp_filename], # validate_certificates as a lib requires a list of filenames
                issuer_identifier = None, # needs a value
                blockchain_services = app.custom_config.get('blockchain_services')
            )

            result = validate_certificates(conf)['results'][0]
            if 'reason' in result and result['reason'] is not None:
                if ('valid until: ' in result['reason']) or ('expired at:' in result['reason']):
                    timestamp = int(result['reason'].split(':')[1].strip())
                    result['expiry_date'] = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                elif result['reason'] == 'address was revoked':
                    result['revoked'] = 'address'
                elif result['reason'] == 'batch was revoked':
                    result['revoked'] = 'batch'
                elif result['reason'] == 'cert hash was revoked':
                    result['revoked'] = 'certificate'
            if version == '0':
                id_proofs = None
            else:
                id_proofs = 0
                if 'verification' in result and result['verification'] is not None:
                    for _, value in result['verification'].items():
                        if value['success']:
                            id_proofs += 1

            app.logger.info('Successfully validated ' + original_filename + " (" + temp_filename + ")")

            template = 'verification-v{}.html'.format(version)
            return render_template(template, result = result, filename = original_filename, issuer = issuer, id_proofs=id_proofs, address = address, txid = txid, metadata = metadata, **app.custom_config)
        except Exception as error:
            app.logger.error('Unexpected error trying to validate ' +
                            original_filename + " (" + temp_filename +
                            ") --- " + repr(error) )
            return render_template('verification-v0.html', error = "There was an unexpected error. Please try again later or contact support", filename = original_filename, **app.custom_config)
        finally:
            delete_tmp_file(temp_filename)
    else:
        return redirect(url_for('upload_file'))


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

