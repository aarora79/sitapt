import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose

import numpy as np
from bokeh.plotting import figure, show, output_file, vplot
import pandas as pd
from bokeh.models.ranges import Range1d
from bokeh.io import save
from bokeh.plotting import ColumnDataSource, figure, show, output_file

import matplotlib.pyplot as plt
from bokeh.io import gridplot, output_file, show
from bokeh.plotting import figure

import bokeh.plotting as bp
from bokeh.models import HoverTool 
from bokeh._legacy_charts import Bar, output_file, show


def _draw_multiple_line_plot(filename, title, X, y, colors, legend, line_dash, line_width, x_axis_type, x_axis_label, y_axis_label, y_start=0, y_end=10, width=800, height=400):
    
    #output_file(filename, title=title)
    p1 = figure(x_axis_type = x_axis_type, plot_width=width, plot_height=height)#, y_range=(y_start, y_end))   

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
    p1.ygrid.minor_grid_line_color = 'navy'
    p1.ygrid.minor_grid_line_alpha = 0.1

    save(vplot(p1), filename=filename, title=title) 


#df = pd.read_csv('applications.csv')
df = pd.read_csv('packet_size_distribution.csv')
date_series = np.array(df['Date'], dtype=np.datetime64)


df = df[df.columns[2:]]

col_list = df.columns

# present_every_year =[]
# for col in col_list:
#     if df[col][df[col] > 0].count() == len(df):
#         present_every_year.append(col)

# print present_every_year


name_list = []
diff_list = []
total_list = []
present_every_year = col_list
decreasing_trend_feature_list = []
for col in present_every_year:
    if df[col].mean() < 100:
        #print('feature ' + col + 'mean ' + str(df[col].mean()))
        #decomposition = seasonal_decompose(np.array(df[col]), model='additive', freq=15)  
        #x = np.array(decomposition.trend)
        x = np.array(df[col])

        #there is a growth trend if sum of logarithmic difference is +ve and last term of the series is > first term
        sum_of_logs = sum((np.log(x[1:]) - np.log(x[:-1])))
        if sum_of_logs > 0: # and (x[-1] > x[0]):
            name_list.append(col)
            diff_list.append(np.log(x[1:]) - np.log(x[:-1]))
            total_list.append(sum_of_logs)
        else:
            print('decreasing trend in ' + col)
            decreasing_trend_feature_list.append(col)
    else:
        print('skipping '  + col + 'mean is ' + str(df[col].mean()))

print('decreasing trend seen in %d protocols' % len(decreasing_trend_feature_list) )
df2 = pd.DataFrame(columns = ['name', 'differences', 'total_delta'])
df2['name'] = name_list
df2['differences'] = diff_list
df2['total_delta'] = total_list

df2.sort_values(by= ['total_delta'], inplace = True, ascending = False)
x = df2.head(100)
print x


#seasonal decompae to extract seasonal trends
X = []
y = []
labels = []
line_width = []
dash_type = []
color_palette = [ 'Pink', 'Red', 'Orange', 'Yellow', 'Brown', 'Green', 'Cyan', 'Blue', 'Purple', 'Black']
c = []
for i in range(len(df2)):

    if df2['name'][i] == 'https' or df2['name'][i] == '0-100':
        continue
    decomposition = seasonal_decompose(np.array(df[df2['name'][i]]), model='additive', freq=5)  
    X.append(date_series)
    y.append(decomposition.trend)
    labels.append(df2['name'][i])
    line_width.append(2)
    dash_type.append(None)
    c.append(color_palette[i % len(color_palette)])

_draw_multiple_line_plot('growth_trends.html', 
                         'growth_trend', 
                         X,
                         y,
                         c, 
                         labels,
                         dash_type,
                         line_width,
                         'datetime', 'Date', 'growth_trend', y_start=0, y_end=2)
# X = []
# y = []
# labels = []
# line_width = []
# dash_type = []
# color_palette = [ 'Pink', 'Red', 'Orange', 'Yellow', 'Brown', 'Green', 'Cyan', 'Blue', 'Purple', 'Black']
# c = []
# growth_list = ['http', 'https', 'unknown', 'macromedia-fcs']
# for i in range(len(growth_list)):

#     decomposition = seasonal_decompose(np.array(df[growth_list[i]]), model='additive', freq=30)  
#     X.append(date_series)
#     y.append(decomposition.trend)
#     labels.append(growth_list[i])
#     line_width.append(1)
#     dash_type.append(None)
#     c.append(color_palette[i % len(color_palette)])

# _draw_multiple_line_plot('growth_trends1.html', 
#                          'growth_trend', 
#                          X,
#                          y,
#                          c, 
#                          labels,
#                          dash_type,
#                          line_width,
#                          'datetime', 'Date', 'growth_trend', y_start=0, y_end=100)
