
## Autoregressive Moving Average (ARMA): Sunspots data

from __future__ import print_function
import numpy as np
from scipy import stats
import pandas as pd
import matplotlib.pyplot as plt

import statsmodels.api as sm
import pandas as pd


from statsmodels.graphics.api import qqplot


### Sunpots Data

# print(sm.datasets.sunspots.NOTE)


# dta = sm.datasets.sunspots.load_pandas().data


# dta.index = pd.Index(sm.tsa.datetools.dates_from_range('1700', '2008'))
# del dta["YEAR"]

df = pd.read_csv('applications.csv')
df2 = df[['Date', 'https']]

df2.index = pd.Index(sm.tsa.datetools.dates_from_str(df2['Date']))
#df2.index = list(df2['Date'])
del df2["Date"]

df2.plot(figsize=(12,8));
#plt.show()



fig = plt.figure(figsize=(12,8))
ax1 = fig.add_subplot(211)
fig = sm.graphics.tsa.plot_acf(df2.values.squeeze(), lags=40, ax=ax1)
ax2 = fig.add_subplot(212)
fig = sm.graphics.tsa.plot_pacf(df2, lags=40, ax=ax2)
#plt.show()

#arma_mod30 = sm.tsa.ARMA(endog = np.array(df2['https']), order = (3,0), dates=np.array(df2.index)).fit()
arma_mod30 = sm.tsa.ARMA(df2, (3,0)).fit()
print(arma_mod30.params)
print(arma_mod30.aic, arma_mod30.bic, arma_mod30.hqic)

# * Does our model obey the theory?

sm.stats.durbin_watson(arma_mod30.resid.values)


fig = plt.figure(figsize=(12,8))
ax = fig.add_subplot(111)
ax = arma_mod30.resid.plot(ax=ax);
#plt.show()

resid = arma_mod30.resid


stats.normaltest(resid)


fig = plt.figure(figsize=(12,8))
ax = fig.add_subplot(111)
fig = qqplot(resid, line='q', ax=ax, fit=True)
#plt.show()


# * In-sample dynamic prediction. How good does our model do?
predicted_dates = sm.tsa.datetools.dates_from_str(['2013-05-29', '2015-09-17'])

predict_https = arma_mod30.predict(72, 90, dynamic=True)
print(predict_https)


# fig, ax = plt.subplots(figsize=(12, 8))
# ax = df2.ix['2008-03-19':].plot(ax=ax)
# fig = arma_mod30.plot_predict('2008-04-30', '2015-09-17', dynamic=True, ax=ax, plot_insample=False)
# #plt.show()
