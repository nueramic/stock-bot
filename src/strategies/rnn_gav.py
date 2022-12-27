import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
from tqdm import tqdm


class StockDataset(Dataset):

    def __init__(self, x, window_size=7 * 4):
        self.x = x
        self.window_size = window_size
        self.data = pd.concat([x.shift(i) for i in range(window_size + 5)], axis=1)
        u_mask = self.data.ticker.apply(lambda x: len(x.unique()), axis=1)
        self.data = self.data[u_mask == 1].close

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        _x = torch.tensor(self.data.iloc[idx, :-5]).unsqueeze(-1).float()
        _y = torch.tensor(self.data.iloc[idx, -5:]).float()

        return _x, _y


class RNNGAV(torch.nn.Module):
    def __init__(self, input_size: int = 7 * 4, hidden_size: int = 32, output_size: int = 5):
        super(RNNGAV, self).__init__()
        self.input_size = input_size
        self.lstm = torch.nn.LSTM(1, hidden_size, batch_first=True, bidirectional=True)
        self.linear = torch.nn.Linear(hidden_size * 2, output_size)
        self.tanh = torch.nn.Tanh()
        self.norm = torch.nn.BatchNorm1d(input_size)

    def forward(self, prices: torch.Tensor):
        try:
            prices = self.norm(prices)
        except:
            print(prices.shape)
        lstm_out, _ = self.lstm(prices)
        out = self.linear(lstm_out[:, -1, :])
        out = self.tanh(out)
        return out

    def predict(self, _x: torch.Tensor):
        """
        :param _x: - исходные сырые цены
        :return: - предсказание на следующие 5 дней
        """
        assert len(_x) > self.input_size
        pct = _x.pct_change().dropna().values
        pct = torch.tensor(pct[-self.input_size:]).reshape(1, self.input_size, 1).float()
        pred = self.forward(pct).flatten()
        pred_x = [_x.iloc[-1]]
        for i in range(5):
            pred_x.append(pred_x[-1] * (1 + pred[i].item()))
        return pred_x[1:]


if __name__ == '__main__':
    x = pd.read_pickle('x.pkl')
    x = x.reset_index(drop=True)


    def normalize(df):
        df.close = df.close.pct_change()
        return df


    x = x.groupby('ticker', group_keys=False).apply(normalize)
    x = x.dropna()

    model = RNNGAV()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = torch.nn.PairwiseDistance(p=1)

    dataset = StockDataset(x)
    train_loader = torch.utils.data.DataLoader(dataset, batch_size=4096, shuffle=True)

    for epoch in range(4):
        running_loss, i = 0.0, 1

        for i, (x, y) in enumerate(tqdm(train_loader, leave=False), 1):
            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out.flatten(), y.flatten())
            running_loss += loss.item()
            loss.backward()
            optimizer.step()

        print(f'Epoch: {epoch:3d}, loss: {running_loss / i:.4f}')

    torch.save(model, 'rnn_gav.pth')
    data = pd.read_pickle('x.pkl')
    pred = model.predict(data.iloc[:30].close)
    true = data.iloc[30:35].close.values
    print(pred)
    print(true)
    print(np.corrcoef(pred, true)[0, 1])
