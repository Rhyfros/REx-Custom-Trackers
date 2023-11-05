# REx-Tracker

## Summary

Hi I made this originally for the REx: Reincarnated community to do basically anything they want with the trackers but this has since been evolved into a discord bot with tracking!

**_YOU NEED A BASIC KNOWLEDGE OF PYTHON TO CREATE THE BOT!!!_**

THIS MAY TAKE TIME TO SETUP

## Instructions:

### Step 1. Download the project files.

- Code > Local > Download ZIP

- Unzip the file with your software of choice!

### Step 2. Get bot and client tokens

#### Bot

- Go to the discord developer portal
- - https://discord.com/developers/
- - - Sometimes logs you out? Not entirely sure why this happens though. Just log in if it does I guess...

- Portal > Applications
- Applications > New Application (button)
- - Set up your basic bot, add a picture and description if you want.
- - Once you have set it up, go to Bot and click Reset Token
- - - Copy the token and put it in the .env file later in the "BOT_TOKEN" section

#### Client

- Go to discord on the web in a chromium based browser
- - Open developer tools
- - - Mac: Option + Command + i
- - Go to network until developer tools
- - Click on almost any Fetch/XHR network request
- - And find "Authorization" and put the token under "TOKEN" in the .env file

### Step 3. Edit the project files.

#### Open it in your IDE of choice.

- Examples being: IDLE, VSCode, or PyCharm.

#### Create a .env file in the ./**src**/ folder.

- Your .env file should be this format:
- - TOKEN='TOKEN'
- - BOT_TOKEN = 'BOT_TOKEN'

(Your IDE might warn you if you created the .env file wrong.)

### Step 4. Run the Python code.

Make sure to open your terminal/console of choice

#### Go to the /REx-Custom-Trackers/ folder

- Depends on operating system (WILL ADD MORE AS MORE PEOPLE USE THIS)
- dir = directory/path

- - Mac + Windows: cd (dir)

(It should show the directory on your current line in your terminal/console)

#### Install needed packages

- Depends on operating system (WILL ADD MORE AS MORE PEOPLE USE THIS)
- Pip explained here: https://en.wikipedia.org/wiki/Pip_(package_manager)

- - It depends on PC and OS so try out these commands to figure out which works, I will further call this the "python base command" (the command without the "--version")

- - - python3 --version
- - - python --version
- - - py --version

(If none of these works make sure you installed python to the correct path variable.)

- - Now install the required packages

- - - (python base command) -m pip install -r requirements.txt

#### Run the file

- - (python base command) src/main.py

## Done!

### You are now done with the code setup! What can you do with this?

#### Download the trackers!

- Can be done with an SQL database such as SQLite with the sqlite3 package or just dumping them into a json file.

## Adding to the project

(Currently I am allowing forks of this to be made!)

### Adding to the main branch

- Feel free to contact me with the source code and what you added and I will review it in my free time

- If you have any improvements, suggestions, or constructive criticism feel free to send a message in the discord or DM me it# REx-Custom-Trackers
