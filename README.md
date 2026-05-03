# Created by Matt Roberts and Debbie Forbeck
# ATP Database WEb Application
A Flask based web application that allows users to explore ATP tennis match data from 2000 to 2015 and utilizes Python, SQLite, Flask, and Bootstrap. 

Features

Match Search
- Filter by player name, tournament, surface, level, round and year with cilcikable links to players, tournament, and match detail pages. 

Player Pages
- Preview player match histories and player profile

Tournament Pages
-Tournament overview with matches played and includes data on the tournament (year, surface, etc.)

Head to head comparison page
-allows users to query a head to head record between two players with filters
- displays a bar chart visualization

Match Detail Page
- winner and loser information
- full statistics summary table

Project Structure
- the app.py and atp.db should be in the main file directory with the HTML templates in a subfolder
- a virtual environment should be ran and the dependencies installed
- run the flask app and the application will run locally
- Deployed via Python Anywhere as well
