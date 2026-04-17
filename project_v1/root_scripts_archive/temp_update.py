
import pandas as pd
import numpy as np
input_file = r'e:\code\tongjimodule\project\data\intermediate\panel_master_with_index.csv'
df = pd.read_csv(input_file)
df['energy_digital_index_100'] = df['energy_digital_index'] * 100
df.to_csv(input_file, index=False)

