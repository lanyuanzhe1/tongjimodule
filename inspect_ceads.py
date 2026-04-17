
import pandas as pd
excel_file = pd.ExcelFile('data/碳核算数据库/data_ceads_used/表观碳排放清单_1997-2022.xlsx')
print(excel_file.sheet_names)
df = pd.read_excel('data/碳核算数据库/data_ceads_used/表观碳排放清单_1997-2022.xlsx', sheet_name='2011')
print(list(df.columns))
print(df.head(2))

