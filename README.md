# USSM - Ultra-Simple Stock Monitor

Small fancy afternoon'ish-project Python script that monitors a list of stock quotes. 
Displays 5y,2y and 3mo price history, auto-circles over all quotes every 15 seconds, 
downloads the data from YAHOO every hour. Uses the tkinter (Tk interface), Matplotlib 
and the yahooquery package, which have to be installed. 
Configuration at the top of the script itself. Tickers loaded from text file passed 
to the script, one ticker per line.

![Screenshot](https://raw.githubusercontent.com/imifos/us-stockmonitor/master/ussm.jpg)

