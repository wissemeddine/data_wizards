# import dependencies
import csv
import calendar
from pprint import pprint

# API Dependencies
import requests
import json
from pandas.io.json import json_normalize # deal with nested columns in api

# data science libraries
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

#formatting detail for visualizations.


# Config file keys.  We can import multiple keys variables in here
from config import av_key # api key for alpha vantage

# determine the top companies from datahub stock cli
data_url = "https://datahub.io/core/s-and-p-500-companies-financials/r/constituents-financials.csv"
datahub_df = pd.read_csv(data_url) # raw_df

datahub_df.head()

# Sector Analysis

# sector data - sum vs mean for groupby analaysis
sector_df = datahub_df.groupby("Sector").sum() 

# whichever sectors have the highest market cap will be shown following the call below. 
top_4_market_cap_df = sector_df.nlargest(4, 'Market Cap')

#display(top_4_market_cap_df)

# Figure 1 - Pie chart

# create data series
Market_Cap = sector_df["Market Cap"]
Sectors = sector_df.index

# Plot
plt.pie(Market_Cap, labels=Sectors, startangle=10, autopct='%.1f%%')
plt.title('S&P 500 Market Cap')

# Sector Analysis:  Top Companies in S and P 500
# this part of the analysis will determine the top 4 companies in each of the top sectors in the S & P 500
# symbols will be a list of lists, with each sector occupying a row

# store the top 4 sectors in a list
top_four_sectors_array = top_4_market_cap_df.index

symbols = [] # initialize list to store symbols of the top 4 companies from each sector
# loop through each sector to find the top 4 companies
for asector in top_four_sectors_array:
    companies_in_sector_df = datahub_df.loc[datahub_df['Sector'] == asector]
    top_companies_in_sector_df = companies_in_sector_df.nlargest(4, 'Market Cap')  
    symbols.append(top_companies_in_sector_df['Symbol'].tolist()) # append the list to the list symbols

print(symbols)

# To access one symbol I will be using variables "i" and "j." This is a very important point.
# It will allow us to generate multiple charts. (i.e. symbols[i][j])

# ***Change i and j to show graph for individual stock you want to see, k for sector.
k=1
i=0
j=0

#controls which list we want to look in.

# ALPHA VANTAGE API SCRAPING

# will need function, symbol, and api key in order to import the json from the api
url_alpha_vantage = "https://www.alphavantage.co/" 

# url variables
function = "TIME_SERIES_DAILY"
symbol = "MSFT"
outputsize = "full" # full or compact (100 latest vs all data)

# Following the query will show you a xml(?) page, which you should do because it is good for understanding.
# I've uncommented the print(query) command so you can click on the link and see for yourself (don't abuse Ram's key!)

# making the querying APIs a json so we can query four at once below in the group.
def url_response(ticker):
    query = url_alpha_vantage + "query?" + "function=" + function + "&symbol=" + ticker +"&outputsize=" + outputsize + "&apikey=" + av_key  
    url_response = requests.get(query).json()
    return url_response

print(symbols[k])


json_responses1 = []
for tickers in symbols[k]:
    response = url_response(tickers)
    json_responses1.append(response)
    
# pprint(json_responses1) #confirm that it works.
# pretty print the json
# print(json.dumps(url_response, indent=4, sort_keys=True))

#ts_df2 = pd.DataFrame.from_dict(url_response2["Time Series (Daily)"])

# artifacts from testing (ignore unless you want to try things out yourself.)
# microsoft_df = pd.DataFrame.from_dict(url_response, orient = 'columns')
#microsoft_df = microsoft_df.tail(730)

ts_df = pd.DataFrame({'A' : []})

#create definition so we don't have to manipulate each stock time series.
def manipulation (ts_df):
# create a data frame from the json
# I'm renaming this thing two times to show the logic - we are getting three year data for one company, Microsoft.
# Then, we are accessing the Time Series (Daily) dict metadata (first out of five), then I am abbreviating it.
    timeseries_df = ts_df = pd.DataFrame.from_dict(json_responses1[j]["Time Series (Daily)"])
# Rename the index to actually be accurate.
    ts_df.index.name = "Date"
# only look at data from the past 3 years 
    ts_df = ts_df.T.head(810)
#sort so that the dates go from 2016 to 2019 instead of the reverse.
    ts_df = ts_df.loc[::-1,:]
    ts_df = ts_df.head(769)
    #display(ts_df)
# Rename columns so they don't look unprocessed and bad.
# create the dictionary to pass to the rename method.
    re_col = {"1. open": "Open", "2. high": "High", "3. low": "Low","4. close": "Close", "5. volume": "Volume"}
# baptize the columns.
    ts_df = ts_df.rename(columns = re_col)
    
    return ts_df
#display(ts_df.head(730)) #use to show the data we are plotting.
#begin visualization of stock

def SMA(ts_df):
    ts_df = manipulation(ts_df)
    ts_df["20 Day SMA"] = ts_df["High"].rolling(window=20).mean()
    #ts_df=ts_df.fillna(0)
    return (ts_df)


# RKY: See the note I made after print(symbols)
#Remember i=0
#j=1
def visualization (ts_df,i,j):
    colors = ["red","green","blue","orange"]
    #ts_df = manipulation(ts_df) 
    ts_df = SMA(ts_df)
    
    index = list(ts_df.index)
    vis_df = pd.DataFrame({f"High for {symbols[i][j]}":ts_df["High"],"20-Day SMA":ts_df["20 Day SMA"]}, index = index)
    vis_df = vis_df.astype(float)

    plt.style.use('seaborn-white')
    vis_df.plot(grid=True,title=f'Three Year Data for Sector Leaders', xticks=([w*7*12 for w in range(10)]),rot=45)
    plt.xlabel("Date")
    plt.ylabel("Price ($)")
    plt.show()

    
while i < len(symbols):
    while j < len(symbols[0]):
        visualization(ts_df,k,j)
        j+=1
    i+=1
