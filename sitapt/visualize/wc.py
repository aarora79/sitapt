import pandas as pd

df = pd.read_csv('applications.csv')

df = df[df.columns[1:]]
mean = df.mean()
mean.sort_values(inplace=True, ascending=False)
mean[:100].to_csv('appl_mean.csv')

df2 = pd.read_csv('appl_mean.csv', names=['application', 'percentage'])
df2.to_csv('appl_top100.csv', index=False)


df = pd.read_csv('protocols.csv')

df = df[df.columns[1:]]
mean = df.mean()
mean.sort_values(inplace=True, ascending=False)
mean[:100].to_csv('protocols_mean.csv')

df2 = pd.read_csv('protocols_mean.csv', names=['protocols', 'percentage'])
df2.to_csv('protocols_top100.csv', index=False)

