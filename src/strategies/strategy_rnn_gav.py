import torch
import pandas as pd
from rnn_gav import RNNGAV
import plotly

model = torch.load('rnn_gav.pth')
data = pd.read_pickle('x.pkl')

print(model.predict(data.head(50).close))
