## Blockchain certificates validation 
Simple webapp to validate blockchain certificates issued to the blockchain. Uses [blockchain-certificates](https://github.com/UniversityOfNicosia/blockchain-certificates) code to validate.

### Installation
This project requires python3. Clone this repository and inside the project directory:
* Create a python virtual environment with `python3 -m venv venv` 
* Activate the virtual environment: `. venv/bin/activate`
* Install the requirements: `pip install -r requirements.txt`
* To start a development server on port 5000: `flask run`. To start a production server on port 8080: `./start_gunicorn.sh`

You may edit the `start_gunicorn.sh` script to fit your needs (see [Gunicorn options](http://docs.gunicorn.org/en/stable/settings.html)). Stop the gunicorn server with `./stop_gunicorn.sh`

### Customization
In order to customize the webapp you can put your custom `config.ini`, `logo.png` and `main.css` inside the customize folder and run `./customize.sh` script inside the project directory to copy them to the relevant directories.

### config.ini options

Option | Explanation and example
-------|------------------------
**Blockchain related** |
testnet | if this option exists with any value, testnet will be used for verification instead of mainnet. Comment it out to use mainnet. *Example:* `True`
**Appearance related** |
logo_text | text to appear under the logo (accepts HTML). *Example:* `CERTIFICATE VERIFICATION`
upload_label_text | text to appear above the upload PDF button. *Example:* `Please upload a certificate for verification`
issuer_name | name of the organisation or person that issued the certificate (accepts HTML). *Example:* `University of Neverland`
contact_name | name to contact for manual verification. *Example:* `Mr. John Smith`
contact_email | email to contact for manual verification. *Example:* `foo@example.com`
general_text | text to appear at the top of the upload PDF page (accepts HTML). *Example:* `<p>Sample text 1</p><p>Sample text 2</p>`

To override the logo that appears at the top of the page, overwrite the `static/logo.png` file with your own logo. You may also customize colors and other styles by editing `static/main.css`.


### Compatibility
- Supports all UNic published certificates except those with index file
  . blockchain-certificates <= v0.9
  . this is a TODO
- validates self-contained certificates with old pdf metadata structure
  . blockchain-certificates v0.9.0
  . expects pdf metadata with keys: issuer, issuer_address and chainpoint_proof
- validates self-contained certificates with new pdf metadata structure
  . blockchain-certificates v0.10.0
  . expects pdf metadata with keys: metadata_object and chainpoint_proof
  . metadata_object is JSON that requires keys: issuer and issuer_address
- validates self-contained certificates with CRED meta-protocol support
  . blockchain-certificates v1.0.0
