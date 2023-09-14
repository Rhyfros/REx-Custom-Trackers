import os

import dotenv

dotenv.load_dotenv()

TOKEN = str(os.getenv("TOKEN"))
WEBHOOK_URL = str(os.getenv("WEBHOOK_URL"))
