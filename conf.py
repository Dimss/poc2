import os
from configparser import ConfigParser

# Load configs file
config = ConfigParser(os.environ)
app_ini_file = 'dev.app.ini'
PROFILE = os.environ.get('PROFILE')
if PROFILE and os.environ['PROFILE'] == 'prod':
    app_ini_file = 'prod.app.ini'
config.read("{current_dir}/{ini_file}".format(current_dir=os.path.dirname(__file__), ini_file=app_ini_file))

RABBITMQ_IP = config.get('rabbitmq', 'ip')
RABBITMQ_QUEUE = config.get('rabbitmq', 'queue')
