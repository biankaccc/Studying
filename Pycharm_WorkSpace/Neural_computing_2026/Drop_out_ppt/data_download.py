# data_download.py
import os
import pandas as pd
import numpy as np
import torch
import urllib.request
import zipfile

# 配置路径
DATA_ROOT = "Data/bike-sharing"
CSV_PATH = os.path.join(DATA_ROOT, "hour.csv")
SAVE_PATH = "bike_data.pt"

def download_bike_data():
    if not os.path.exists(DATA_ROOT):
        os.makedirs(DATA_ROOT)
    if os.path.exists(CSV_PATH):
        print("数据集已存在，跳过下载")
        return
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00275/Bike-Sharing-Dataset.zip"
    zip_path = os.path.join(DATA_ROOT, "bike.zip")
    print("正在下载共享单车数据集...")
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(DATA_ROOT)
    os.remove(zip_path)
    print("下载并解压完成")

def preprocess_data():
    data = pd.read_csv(CSV_PATH)
    # 独热编码
    ohe_features = ['season', 'weathersit', 'mnth', 'hr', 'weekday']
    for feature in ohe_features:
        dummies = pd.get_dummies(data[feature], prefix=feature, drop_first=False)
        data = pd.concat([data, dummies], axis=1)

    drop_features = ['instant', 'dteday', 'season', 'weathersit', 'weekday', 'atemp',
                     'mnth', 'workingday', 'hr', 'casual', 'registered']
    data = data.drop(drop_features, axis=1)

    # 标准化
    norm_features = ['cnt', 'temp', 'hum', 'windspeed']
    scaled_features = {}
    for feature in norm_features:
        mean, std = data[feature].mean(), data[feature].std()
        scaled_features[feature] = [mean, std]
        data.loc[:, feature] = (data[feature] - mean) / std

    # 切分
    test_data = data[-31*24:]
    data = data[:-31*24]

    target_fields = ['cnt']
    features, targets = data.drop(target_fields, axis=1), data[target_fields]
    test_features, test_targets = test_data.drop(target_fields, axis=1), test_data[target_fields]

    X_train, y_train = features[:-30*24], targets[:-30*24]
    X_val, y_val = features[-30*24:], targets[-30*24:]

    # 强制转为数值类型，解决object数组报错
    X_train_np = X_train.astype(np.float64).values
    y_train_np = y_train['cnt'].astype(np.float64).values
    X_val_np = X_val.astype(np.float64).values
    y_val_np = y_val['cnt'].astype(np.float64).values

    X_train_tensor = torch.tensor(X_train_np, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train_np, dtype=torch.float32).unsqueeze(1)
    X_val_tensor = torch.tensor(X_val_np, dtype=torch.float32)
    y_val_tensor = torch.tensor(y_val_np, dtype=torch.float32).unsqueeze(1)

    torch.save({
        "X_train": X_train_tensor,
        "y_train": y_train_tensor,
        "X_val": X_val_tensor,
        "y_val": y_val_tensor,
        "input_dim": X_train.shape[1],
        "scaled_features": scaled_features
    }, SAVE_PATH)
    print(f"预处理完成，数据保存至 {SAVE_PATH}")

if __name__ == "__main__":
    download_bike_data()
    preprocess_data()
