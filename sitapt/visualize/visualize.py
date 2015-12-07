import numpy as np
from bokeh.plotting import figure, show, output_file, vplot
import pandas as pd
from bokeh.models.ranges import Range1d
from bokeh.io import save
import statsmodels.api as sm
from statsmodels.tsa.stattools import acf  
from statsmodels.tsa.stattools import pacf
from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib.pyplot as plt
from bokeh.io import gridplot, output_file, show
from bokeh.plotting import figure

def _draw_multiple_line_plot(filename, title, X, y, colors, legend, line_dash, line_width, x_axis_type, x_axis_label, y_axis_label, y_start=0, y_end=100, width=800, height=400):
    
    #output_file(filename, title=title)
    p1 = figure(x_axis_type = x_axis_type, plot_width=width, plot_height=height, y_range=(y_start, y_end))   

    for i in range(len(y)):
        p1.line(X[i], y[i], color=colors[i], legend=legend[i], line_dash=line_dash[i], line_width=line_width[i])
    #p1.multi_line(X, y, color=colors, legend=legend, line_dash=line_dash, line_width=line_width)
    # p1.multi_line(xs=X,
    #             ys=y,
    #             line_color=colors,
    #             line_width=5)
    p1.title = title
    #p1.grid.grid_line_color='Black'
    #p.ygrid[0].grid_line_alpha=0.5
    p1.legend.orientation = "bottom_left"
    p1.grid.grid_line_alpha=0.75
    p1.xaxis.axis_label = x_axis_label
    p1.yaxis.axis_label = y_axis_label
    p1.ygrid.band_fill_color="olive"
    p1.ygrid.band_fill_alpha = 0.25

    save(vplot(p1), filename=filename, title=title)  

def _draw_decomposition_plot(filename, X, decomposition, legend, x_axis_type, x_axis_label, width=800, height=400):

    # create a new plot
    s1 = figure(x_axis_type = x_axis_type, width=width, plot_height=height, title='observed')
    s1.line(X, decomposition.observed, color="navy", alpha=0.5)

    # create another one
    s2 = figure(x_axis_type = x_axis_type, width=width, plot_height=height, title='trend')
    s2.line(X, decomposition.trend, color="navy", alpha=0.5)

    # create and another
    s3 = figure(x_axis_type = x_axis_type, width=width, plot_height=height, title='residual')
    s3.line(X, decomposition.resid, color="navy", alpha=0.5)

    s4 = figure(x_axis_type = x_axis_type, width=width, plot_height=height, title='seasonal')
    s4.line(X, decomposition.seasonal, color="navy", alpha=0.5)

    # put all the plots in a grid layout
    p = gridplot([[s1, s2], [s3, s4]])

    save(vplot(p), filename=filename, title='seasonal_decompose')  

df2 = pd.read_csv('applications.csv')
X = np.array(df2['Date'], dtype=np.datetime64)


_draw_multiple_line_plot('web.html', 
                         'web traffic', 
                         [X, X],
                         [np.array(df2['http']), np.array(df2['https'])],
                         ['navy', 'red'], 
                         ['non-secure web traffic', 'secure web traffic'],
                         [None, None],
                         [1, 1],
                         'datetime', 'Date', 'Traffic Share Percentage')


df = pd.read_csv('applications.csv')
X = np.array(df['Date'], dtype=np.datetime64)
y = np.array(df['https'])

_draw_multiple_line_plot('TCP_observed.html', 
                         'transport layer protocols', 
                         [X],
                         [np.array(df['https'])],
                         ['navy'], 
                         ['observed packets percentage'],
                         [None],
                         [1],
                         'datetime', 'Date', 'Packets Percentage')

#df['First Difference'] = df['https'] - df['https'].shift()  
y = np.array(df['https'] - df['https'].shift())
_draw_multiple_line_plot('protocols_diff.html', 
                         'transport layer protocols', 
                         [X],
                         [y],
                         ['navy'], 
                         ['packets percentage delta'],
                         [None],
                         [1],
                         'datetime', 'Date', 'Packets Percentage Delta', y_start=-100, y_end=100)


df['first difference'] = df['https'] - df['https'].shift()
lag_correlations = acf(df['first difference'].iloc[1:])  
lag_partial_correlations = pacf(df['first difference'].iloc[1:])  

print 'lag_correlations'
print lag_correlations
y = lag_correlations
_draw_multiple_line_plot('lag_correlations.html', 
                         'lag_correlations', 
                         [X],
                         [y],
                         ['navy'], 
                         ['lag_correlations'],
                         [None],
                         [1],
                         'datetime', 'Date', 'lag_correlations', y_start=-1, y_end=1)


print 'lag_partial_correlations'
print lag_partial_correlations
y = lag_partial_correlations
_draw_multiple_line_plot('lag_partial_correlations.html', 
                         'lag_partial_correlations', 
                         [X],
                         [y],
                         ['navy'], 
                         ['lag_partial_correlations'],
                         [None],
                         [1],
                         'datetime', 'Date', 'lag_partial_correlations', y_start=-1, y_end=1)

decomposition = seasonal_decompose(np.array(df['https']), model='additive', freq=30)  
_draw_decomposition_plot('decomposition.html', X, decomposition, 'seasonal decomposition', 'datetime', 'decomposition', width=600, height=400)

model = sm.tsa.ARIMA(np.array(df['https'].iloc[1:]), order=(2,0,0))  
results = model.fit(disp=-1)  

#predict next 10 values
num_predictions = 12
predicted_dates = []
last_date = X[-1]
for i in range(num_predictions):
    next_date = last_date + 30
    predicted_dates.append(next_date)
    last_date = next_date

#predicted_dates=np.array(['2015-10-17', '2015-12-19', '2016-03-19', '2016-06-19', '2016-09-19'], dtype=np.datetime64)
#print predicted_dates
predicted = results.predict(start=len(df), end=len(df) + num_predictions)

_draw_multiple_line_plot('TCP_forecast.html', 
                         'transport layer protocols', 
                         [X[1:],X[1:], predicted_dates],
                         [np.array(df['https']), results.fittedvalues, predicted],
                         ['navy', 'green', 'red'], 
                         ['observed packets percentage', 'fitted packets percentage', 'predicted'],
                         [None, None, None],
                         [1,1,1],
                         'datetime', 'Date', 'Packets Percentage')

print results.summary()
