import pandas as pd
import numpy as np
import time

from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import MaxAbsScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline

def load_and_process(file_path):
    """
    读取 CSV，生成标签并做镜像扩充。
    返回 X, y
    """
    df = pd.read_csv(file_path)
    df['label'] = 1
    df_mirror = df.iloc[:, :-1] * -1
    df_mirror['label'] = 0
    df_all = pd.concat([df, df_mirror], ignore_index=True)
    X = df_all.iloc[:, :-1].values
    y = df_all['label'].values
    return X, y

def train_and_select_best(file_path,
                          test_size=0.1,
                          random_state=None):
    """
    在同一测试集上依次训练 XGB / MLP(pipeline) / RF，
    打印三者准确率，返回最佳模型（若是 MLP 就是整个 pipeline）及对应测试集。
    """
    if random_state is None:
        random_state = int(time.time())

    # 1. 读数据并拆分
    X, y = load_and_process(file_path)
    X_train_all, X_test, y_train_all, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    results = {}
    models  = {}

    # 2. XGBoost
    xgb = XGBClassifier(use_label_encoder=False,
                        eval_metric='logloss',
                        random_state=random_state)
    xgb.fit(X_train_all, y_train_all)
    y_pred = xgb.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"XGB 准确率: {acc:.4f}")
    results['XGB'] = acc
    models['XGB']  = xgb

    # 3. MLP + MaxAbsScaler Pipeline
    mlp_pipeline = Pipeline([
        ('scaler', MaxAbsScaler()),
        ('mlp', MLPClassifier(
            hidden_layer_sizes=(99, 66),
            activation='relu',
            solver='adam',
            alpha=1e-4,
            batch_size=32,
            learning_rate_init=1e-3,
            max_iter=300,
            early_stopping=True,
            validation_fraction=0.1,
            random_state=42
        ))
    ])
    mlp_pipeline.fit(X_train_all, y_train_all)
    y_pred = mlp_pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"MLP Pipeline 准确率: {acc:.4f}")
    results['MLP'] = acc
    models['MLP']  = mlp_pipeline

    # 4. 随机森林
    rf = RandomForestClassifier(n_estimators=100,
                                random_state=random_state)
    rf.fit(X_train_all, y_train_all)
    y_pred = rf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"RF   准确率: {acc:.4f}")
    results['RF'] = acc
    models['RF']  = rf

    # 5. 选最佳
    best_name = max(results, key=results.get)
    print(f"最佳模型: {best_name}，准确率: {results[best_name]:.4f}")

    # 返回（模型对象, X_test, y_test）
    return models[best_name], X_test, y_test

if __name__ == "__main__":
    best_model, X_test, y_test = train_and_select_best("results.csv")
    # 如果 best_model 是 MLP，那么它就是一个 pipeline，调用 predict 会自动先 scale 再预测
    y_pred = best_model.predict(X_test)
    print("最终准确率：", accuracy_score(y_test, y_pred))
