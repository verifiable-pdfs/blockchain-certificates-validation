## Blockchain certificates validation
Simple webapp to validate blockchain certificates issued to the blockchain. Uses [blockchain-certificates](https://github.com/UniversityOfNicosia/blockchain-certificates) code to validate.


### Installation
This project requires python3. Clone this repository and inside the project directory:
* Create a python virtual environment with `python3 -m venv venv`
* Activate the virtual environment: `. venv/bin/activate`
* Install the requirements: `pip install -r requirements.txt`
* To start a development server on port 18080: `python verify.py`. To start a production server on port 8080: `./start_gunicorn.sh`

You may edit the `start_gunicorn.sh` script to fit your needs (see [Gunicorn options](http://docs.gunicorn.org/en/stable/settings.html)). Stop the gunicorn server with `./stop_gunicorn.sh`

If any changes are made to the code or configuration (config.ini), the development or production server needs to be restarted in order for the changes to take effect.


### Customization
In order to customize the webapp you can put your custom `config.ini`, `logo.png` and `main.css` inside the `customize/` folder and run `./customize.sh` script inside the project directory to copy them to the relevant directories.

If you pull an updated version of the webapp (e.g. with `git pull`), you need to rerun `./customize.sh` in order for your custom files to be in the correct locations again. Also, after updating check `config.ini` for any new or changed options.


### Updating
When a new version of the underlying libraries is available, there will be a warning displayed at the top of every page of the webapp. Follow the procedure below to update to the latest version.
> cd blockchain-certificates-validation  
> git pull  
> . venv/bin/activate  
> pip install --upgrade blockchain-certificates

You must rerun the `customize.sh` script in order to copy your custom files to the relevant locations.
> ./customize.sh

Restart the server and refresh the webpage for the changes to take effect.


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
