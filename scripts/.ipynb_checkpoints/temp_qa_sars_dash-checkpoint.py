import dash
from dash import dcc, html, Input, Output
import pandas as pd
from pathlib import Path
from datetime import datetime
from importlib.machinery import SourceFileLoader
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# Загружаем модули
m0 = SourceFileLoader("m", "/export/home/agletdinov/work/git_projects/gitlab/collapse-pango-lineages/modules.py").load_module()
m = SourceFileLoader("m", "/export/home/agletdinov/work/git_projects/temporary_qualifier-sars_cov_2/scripts/self_modules.py").load_module()

# Путь к данным
ROOT = Path().cwd().parent
DATA = ROOT / "data"

to_file = DATA / "ежедневный_расширенный_отчёт_2024-10-05 16-00-01.tsv.gz"
to_save = DATA.joinpath(to_file.stem + "_filt.tsv.gz")
if to_save.exists():
    print(f"Skipped")
    df_filt = pd.read_csv(to_save, sep='\t',quoting=3,
                         usecols=["id последовательности", "Дата забора", "Pangolin", "Pangolin_collapse", "дни_с_2020"],
                         dtype={"id последовательности": str,
                                "Pangolin": str,
                                "Pangolin_collapse": str,
                                "дни_с_2020": int},
                         parse_dates=['Дата забора'])
else:
    df = pd.read_csv(to_file, sep='\t',quoting=3,
                     usecols=["id последовательности", "Дата забора", "Pangolin"],
                     dtype={"id последовательности": str,
                            "Pangolin": str},
                     parse_dates=['Дата забора'])
    df_filt = df_preprocessing(df, start_date)
    print(df_filt.shape)
    df_filt.to_csv(to_save,
                   sep="\t",
                   index=False,
                   compression='gzip')

# Функция для конвертации графиков в формат base64 для отображения на дашборде
def fig_to_base64(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format='png')
    buffer.seek(0)
    img_bytes = buffer.getvalue()
    buffer.close()
    encoded = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/png;base64,{encoded}"

# Создание приложения Dash
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("SARS-CoV-2 Статистика по линиям"),
    html.Label('Введите название линии:'),
    dcc.Input(id='lineage-input', value='XBB', type='text'),
    html.Br(),
    html.Label('Введите дату (ГГГГ-ММ-ДД):'),
    dcc.Input(id='date-input', value='2022-12-15', type='text'),
    html.Br(),
    html.Button('Построить графики', id='submit-val', n_clicks=0),
    html.Div(id='output-kde-plot'),
    html.Div(id='output-morbidity-plot'),
    html.Div(id='output-prediction-plot')
])

@app.callback(
    [Output('output-kde-plot', 'children'),
     Output('output-morbidity-plot', 'children'),
     Output('output-prediction-plot', 'children')],
    [Input('submit-val', 'n_clicks')],
    [dash.dependencies.State('lineage-input', 'value'),
     dash.dependencies.State('date-input', 'value')]
)
def update_graph(n_clicks, lineage_input, date):
    if n_clicks > 0:
        start_date = datetime(2020, 1, 1)

        # Обрабатываем название линии перед использованием
        strain = m0.create_collapsed_strain(lineage_input)

        # Используем pipeline для создания графиков
        strain_df = m0.create_strain_df(strain=strain, date=date, df=df_filt)
        kde = m.create_kde(strain_df=strain_df)
        threshold = m.create_threshold(kde=kde, strain_df=strain_df)
        day_number = m.find_day_number(date=date, start_date=start_date)

        # Построение графика KDE
        fig1, ax1 = plt.subplots()
        m.draw_kde(kde=kde, strain=strain, day_number=day_number, strain_df=strain_df)
        kde_plot = html.Img(src=fig_to_base64(fig1))

        # Построение графика заболеваемости
        fig2, ax2 = plt.subplots()
        m.draw_morbidity(strain_df=strain_df, strain=strain, date=date)
        morbidity_plot = html.Img(src=fig_to_base64(fig2))

        # Построение графика предсказания
        fig3, ax3 = plt.subplots()
        m.draw_predictions(kde=kde, strain=strain, strain_df=strain_df, threshold=threshold, day_number=day_number)
        prediction_plot = html.Img(src=fig_to_base64(fig3))

        return kde_plot, morbidity_plot, prediction_plot
    return None, None, None

if __name__ == '__main__':
    app.run_server(debug=True, port=9998)