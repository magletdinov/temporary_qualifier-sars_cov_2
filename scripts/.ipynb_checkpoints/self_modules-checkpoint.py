from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import gaussian_kde
from datetime import datetime

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
    # Генерация числовых значений для оси X (например, все дни c 2020)
    x = np.arange(start=0, stop=365*5)
    # Оценка плотности для каждого дня в году
    density = kde(x)
    # Визуализация результатов
    xmin, xmax = strain_df["дни_с_2020"].min(), strain_df["дни_с_2020"].max()
    plt.plot(x, density, label='Плотность KDE')
    plt.xlim(xmin, xmax)
    plt.xlabel('Номер дня пандемии (начиная с 01.01.2020)')
    #plt.ylabel('Плотность')
    plt.title(f'Ядерная оценка плотности для {strain}')
    plt.legend()
    plt.axvline(x=day_number, color='r', linestyle='--')
    plt.show()
    
def draw_morbidity(strain_df, strain, date):
    # Оценка вероятности для новых событий
    # Определение границ оси X
    #print(strain_df.head())
    xmin_date, xmax_date = strain_df["Дата забора"].min(), strain_df["Дата забора"].max()
    #xmin, xmax = "2023-10-01", "2024-12-01"
    strain_df_agg = strain_df.groupby(by="Дата забора").agg({"Pangolin_collapse":"count"})
    
    print("sasasasasa", strain_df_agg.head())
    print(strain_df_agg.index) 
    strain_df_agg.plot(kind="line")
    #plt.xlim(xmin_date, xmax_date)
    #plt.ylabel('Число образцов')
    #plt.title(f'Динамика заболеваемости {strain}')
    #plt.legend()
    #plt.axvline(x=date, color='r', linestyle='--')
    plt.show()
    
def draw_predictions(kde, strain, strain_df, threshold, day_number):
    xmin, xmax = strain_df["дни_с_2020"].min(), strain_df["дни_с_2020"].max()
    res = []
    for i in np.arange(xmin, xmax):
        probability = kde(i)
        #print(f'Вероятность события {new_date_day}: {probability[0]}')
        #print((probability > threshold)[0])
        res.append((probability > threshold)[0])
    ax = sns.lineplot(x=[i for i in np.arange(xmin, xmax)], y=res)
    ax.set_title(f'Предсказание достоверности для {strain}')
    ax.set_xlabel('Номер дня пандемии (начиная с 01.01.2020)')
    ax.set_ylabel('True - 1, False - 0')
    #plt.axvline(x=day_number, color='r', linestyle='--')
    plt.show()
    
def create_statistics_pipe(strain, date, df, start_date):
    strain_df = create_strain_df(strain=strain, date=date, df=df)
    kde = create_kde(strain_df=strain_df)
    threshold = create_threshold(kde=kde, strain_df=strain_df)
    day_number = find_day_number(date=date, start_date=start_date)
    
    draw_kde(kde=kde, strain=strain, day_number=day_number, strain_df=strain_df)
    draw_morbidity(strain_df=strain_df, strain=strain, date=date)
    draw_predictions(kde=kde, strain=strain, strain_df=strain_df, threshold=threshold, day_number=day_number)
    
    print(correct_or_error_collection_date(day_number=day_number, threshold=threshold, kde=kde))