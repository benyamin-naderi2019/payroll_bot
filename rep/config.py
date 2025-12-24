import os

database_config = {

            'user' : os.environ.get('db_user'),
            'password' : os.environ.get('db_password'),
            'host' : os.environ.get('db_host'),
            'database': os.environ.get('database_name')
}


API_TOKEN = os.environ.get('API_TOKEN')             
CHANNEL_ID = int(os.environ.get('CHANNEL_ID'))
ADMIN_CID = int(os.environ.get('ADMIN_CID'))       # 6716225040

#'8387032076:AAGX-vOZTbn8eTNVJgf0584nKxrniUtekH0'