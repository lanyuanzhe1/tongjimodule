
import pandas as pd
print('---Internet---')
print(list(pd.read_csv('data/0412/分省互联网主要指标_多年期_面板数据.csv', nrows=0).columns))
print('---Pop---')
print(list(pd.read_csv('data/0412/分省人口_多年期_面板数据.csv', nrows=0).columns))
print('---GDP---')
print(list(pd.read_csv('data/0412/分省GDP_多年期_面板数据.csv', nrows=0).columns))

