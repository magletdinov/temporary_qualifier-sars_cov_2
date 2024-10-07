from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import gaussian_kde
from datetime import datetime
import plotly.graph_objects as go

def df_preprocessing(df, start_date):
    df = df[df["Дата забора"] > start_date]
    df.dropna(subset=["Pangolin"], inplace=True)
    df["Pangolin_collapse"] = df["Pangolin"].apply(lambda x: m.create_collapsed_strain(x.split(" ")[0]))
    
    start_date = datetime(2020, 1, 1)

    # Преобразование даты в количество дней от 1 января 2020 года
    df['дни_с_2020'] = (df['Дата забора'] - start_date).dt.days
    df.dropna(subset=["дни_с_2020"], inplace=True)
    return df

def find_day_number(date, start_date):
    new_date = pd.to_datetime(date)
    day_number = (new_date - start_date).days
    return day_number

def create_strain_df(strain, date, df):
    new_date = pd.to_datetime(date)
    strain_df = df[df["Pangolin_collapse"] == strain]
    #print(df.head())
    if new_date > strain_df["Дата забора"].max():
        strain_df = strain_df[(strain_df["Дата забора"] <= (new_date - pd.tseries.offsets.Day()))]# берём без учета дня загрузки текущего сиквенса
    if len(strain_df) <= 1:
        print("Данных для анализа недостаточно")
        return None
    strain_df.sort_values(by="Дата забора", inplace=True)
    return strain_df

def create_kde(strain_df):
    # Получение значений для KDE
    values = strain_df['дни_с_2020'].values

    # Построение KDE
    kde = gaussian_kde(values, bw_method=0.8)
    return kde

def create_threshold(kde, strain_df):
    # Генерация числовых значений для оси X (например, все дни c 2020)
    x = np.arange(start=0, stop=365*5)

    # Оценка плотности для каждого дня в году
    density = kde(x)
    q = lambda df: 75 if len(df) > 250 else 90
    threshold = np.percentile(density, q(strain_df))
    return threshold

def correct_or_error_collection_date(day_number, threshold, kde):
    probability = kde(day_number)
    return probability > threshold

def draw_kde(kde, strain, day_number, strain_df):
    # Генерация числовых значений для оси X (например, все дни с 2020)
    x = np.arange(start=0, stop=365*5)
    # Оценка плотности для каждого дня в году
    density = kde(x)
    
    # Определение границ оси X
    xmin, xmax = strain_df["дни_с_2020"].min(), strain_df["дни_с_2020"].max()

    # Создание графика
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=density, mode='lines', name='Плотность KDE'))
    fig.add_vline(x=day_number, line_color='red', line_dash='dash', name='День события')
    fig.update_layout(
        title=f'Ядерная оценка плотности для {strain}',
        xaxis_title='Номер дня пандемии (начиная с 01.01.2020)',
        yaxis_title='Плотность',
        xaxis=dict(range=[xmin, xmax])
    )
    return fig  # Возвращаем фигуру вместо ее отображения

def draw_morbidity(strain_df, strain, date):
    # Определение границ оси X
    xmin_date, xmax_date = strain_df["Дата забора"].min(), strain_df["Дата забора"].max()
    strain_df_agg = strain_df.groupby(by="Дата забора").agg({"Pangolin_collapse": "count"}).reset_index()

    # Создание графика
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=strain_df_agg["Дата забора"], 
                             y=strain_df_agg["Pangolin_collapse"], 
                             mode='lines+markers', 
                             name='Число образцов'))
    
    fig.update_layout(
        title=f'Динамика заболеваемости {strain}',
        xaxis_title='Дата забора',
        yaxis_title='Число образцов',
        xaxis=dict(range=[xmin_date, xmax_date])
    )
    return fig  # Возвращаем фигуру вместо ее отображения

def draw_predictions(kde, strain, strain_df, threshold, day_number):
    xmin, xmax = strain_df["дни_с_2020"].min(), strain_df["дни_с_2020"].max()
    res = []
    
    for i in np.arange(xmin, xmax):
        probability = kde(i)
        res.append((probability > threshold)[0])
    
    # Создание графика
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.arange(xmin, xmax), 
                             y=res, 
                             mode='lines', 
                             name='Предсказания'))
    
    fig.update_layout(
        title=f'Предсказание достоверности для {strain}',
        xaxis_title='Номер дня пандемии (начиная с 01.01.2020)',
        yaxis_title='True - 1, False - 0',
        xaxis=dict(range=[xmin, xmax])
    )
    return fig  # Возвращаем фигуру вместо ее отображени
    
def create_statistics_pipe(strain, date, df, start_date):
    strain_df = create_strain_df(strain=strain, date=date, df=df)
    kde = create_kde(strain_df=strain_df)
    threshold = create_threshold(kde=kde, strain_df=strain_df)
    day_number = find_day_number(date=date, start_date=start_date)
    
    draw_kde(kde=kde, strain=strain, day_number=day_number, strain_df=strain_df)
    draw_morbidity(strain_df=strain_df, strain=strain, date=date)
    draw_predictions(kde=kde, strain=strain, strain_df=strain_df, threshold=threshold, day_number=day_number)
    
    print(correct_or_error_collection_date(day_number=day_number, threshold=threshold, kde=kde))