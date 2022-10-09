import pandas as pd                        
from pytrends.request import TrendReq

pytrend = TrendReq()
# Get Google Hot Trends data
df = pytrend.trending_searches(pn='united_states')
df.head()