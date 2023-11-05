import os

import dotenv

dotenv.load_dotenv()

TOKEN = str(os.getenv("TOKEN"))
BOT_TOKEN = str(os.getenv("BOT_TOKEN"))
