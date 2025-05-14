from flask import render_template
from dotenv import load_dotenv
import logging
import os

from app import create_app

# Load environment variables from .env
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

# print(f"---------- basedir in run.py ------- : {basedir}")

# Create the application instance
app = create_app(basedir=basedir)

@app.route("/")
def index():
    return render_template('index.html')

# Run the application
if __name__ == '__main__':
    # print(f" run.py ")
    logging.info(f" run.py ")
    
    app.run(debug=True, host='0.0.0.0', port=20000)