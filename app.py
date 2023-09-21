import pandas as pd
import numpy as np
import panel as pn
pn.extension('tabulator')
pn.extension('plotly')

import seaborn as sns
import matplotlib.pyplot as plt
import hvplot.pandas
import holoviews as hv
import plotly.express as px
import plotly.graph_objects as go
import os

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from unidecode import unidecode

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
df_original = pd.read_csv("datos_limpios.csv", dtype=str)

# Crea una copia del DataFrame original
df = df_original.copy()

# Make DataFrame Pipeline Interactive
idf = df.interactive()

columnas_a_convertir = ['codigo_dane', 'cantidad', 'year','dia', 'mes']

df[columnas_a_convertir] = df[columnas_a_convertir].apply(lambda x: pd.to_numeric(x, errors='coerce'))

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Define Panel widgets
year_slider = pn.widgets.IntRangeSlider(name='Rango de años', width=250, start=2010, end=2023, value=(2010, 2023), value_throttled=(2010,2023))

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Radio buttons para seleccionar entre 'departamento' y 'municipio'
radio_buttons = pn.widgets.RadioButtonGroup(
    name='Seleccionar datos',
    options=['departamento', 'municipio'],
    button_type='success'
)

# Crear botones de selección de tipo de datos
bt2 = pn.widgets.RadioButtonGroup(
    name='Seleccionar datos',
    button_type='success',
    options=['delito', 'tipo_de_arma'],
)

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Función para crear la gráfica interactiva
@pn.depends(year=year_slider.param.value_throttled, data_type=radio_buttons) 
def create_bar_chart(year, data_type):
    # Filtra el DataFrame por el rango de años seleccionado
    filtered_df = df[(df['year'] >= year[0]) & (df['year'] <= year[1])]
    
    # Calcula la frecuencia de departamentos o municipios según la selección
    if data_type == 'departamento':
        data_column = 'departamento'
        plot_title = 'Frecuencia de Departamentos (Top 32)'
    else:
        data_column = 'municipio'
        plot_title = 'Frecuencia de Municipios (Top 32)'
    
    frecuencia_data = filtered_df[data_column].value_counts().reset_index()
    frecuencia_data = frecuencia_data.rename(columns={'index': data_column, data_column: 'Frecuencia'})
    
    # Selecciona los 32 principales
    top_32 = frecuencia_data.nlargest(32, 'Frecuencia')
    
    # Crea el gráfico de barras
    bar_chart = top_32.hvplot(
        kind='bar',
        x=data_column, 
        y='Frecuencia', 
        xlabel=data_column, 
        ylabel='Frecuencia', rot=90,
        title=plot_title
    )
    
    return bar_chart

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Función para crear la tabla paginada
@pn.depends(data_type=radio_buttons.param.value, year=year_slider.param.value)
def create_table(data_type, year):
    # Filtrar el DataFrame por el rango de años seleccionado
    filtered_df = df[(df['year'] >= year[0]) & (df['year'] <= year[1])]

    # Agrupar los datos por departamento o municipio según la selección
    if data_type == 'departamento':
        data_column = 'departamento'
    else:
        data_column = 'municipio'

    grouped_data = filtered_df.groupby(['year', data_column]).size().reset_index(name='Frecuencia')

    # Ordenar los datos por frecuencia de mayor a menor
    grouped_data = grouped_data.sort_values(by='Frecuencia', ascending=False)

    # Crear una tabla interactiva paginada, no editable
    table = pn.widgets.Tabulator(grouped_data, pagination='remote', page_size=10)
    
    # Configurar las columnas y hacer que la tabla no sea editable
    table.param.columns = [data_column, 'Frecuencia']
    table.param.editable = False

    return table

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Función para crear la tabla paginada
@pn.depends(data_type=bt2.param.value, year=year_slider.param.value)
def create_table2(data_type, year):
    # Filtrar el DataFrame por el rango de años seleccionado
    filtered_df = df[(df['year'] >= year[0]) & (df['year'] <= year[1])]

    # Agrupar los datos por delitos o tipo_de_arma según la selección
    if data_type == 'delito':
        data_column = 'delito'
    else:
        data_column = 'tipo_de_arma'

    grouped_data = filtered_df.groupby(['year', data_column]).size().reset_index(name='Frecuencia')

    # Ordenar los datos por frecuencia de mayor a menor
    grouped_data = grouped_data.sort_values(by='Frecuencia', ascending=False)

    # Crear una tabla interactiva paginada
    table2 = pn.widgets.Tabulator(grouped_data, pagination='remote', page_size=10)
    
    # Configurar las columnas y hacer que la tabla no sea editable
    table2.columns = [data_column, 'Frecuencia']
    table2.editable = False

    return table2

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Obtener la frecuencia de cada valor único en la columna 'delito'
frecuencia_delitos = df['delito'].value_counts()

# Crear un nuevo DataFrame a partir de la serie de frecuencias
df_delitos = pd.DataFrame({'delito': frecuencia_delitos.index, 'Frecuencia': frecuencia_delitos.values})

# Ordenar el DataFrame por frecuencia de mayor a menor
df_delitos = df_delitos.sort_values(by='Frecuencia', ascending=False)

# Función para crear el gráfico de pastel con porcentajes
def create_pie_chart_with_percentages(df):
    fig = px.pie(df, names='delito', values='Frecuencia')
   
    # Ajustar el tamaño del gráfico de pastel
    fig.update_layout(width=650, height=560)
    
    # Colocar la leyenda debajo del gráfico
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
    
    # Ajustar el margen derecho del gráfico para pegarlo a la izquierda
    fig.update_layout(margin=dict(r=300))

    return fig

# Crear un panel de Markdown con la explicación de la interacción
interaction_explanation = """
**Interacción con el Gráfico:**

El cuadro de leyenda te permite mostrar u ocultar ciertos artículos haciendo clic en ellos. 
Prueba hacer clic en los nombres de los artículos en la leyenda para ver cómo afecta al gráfico.
"""

# Crear el gráfico de pastel inicial con porcentajes
initial_pie_chart = create_pie_chart_with_percentages(df_delitos)

delito_explanation = pn.Column(
    pn.pane.Markdown("""
        - Artículo 205. Acceso carnal violento
        - Artículo 206. Acto sexual violento
        - Artículo 207. Acceso carnal o acto sexual en persona puesta en incapacidad de resistir
        - Artículo 208. Acceso carnal abusivo con menor de 14 años
        - Artículo 209. Actos sexuales con menor de 14 años
        - Artículo 210a. Acoso sexual
        - Artículo 210. Acceso carnal o acto sexual abusivo con incapaz de resistir
        - Artículo 211. Acceso carnal abusivo con menor de 14 años
        - Artículo 211. Actos sexuales con menor de 14 años
        - Artículo 211. Acceso carnal o acto sexual en persona puesta en incapacidad de resistir
        - Artículo 211. Acceso carnal violento
        - Artículo 211. Acto sexual violento 
        - Artículo 213. Inducción a la prostitución
        - Artículo 213a. Proxenetismo con menor de edad
        - Artículo 214. Constreñimiento a la prostitución
        - Artículo 216. Constreñimiento a la prostitución
        - Artículo 216. Inducción a la prostitución
        - Artículo 217. Estímulo a la prostitución de menores
        - Artículo 217a. Demanda de explotación sexual comercial de persona menor de 18 años de edad
        - Artículo 218. Pornografía con menores
        - Artículo 219a. Utilización o facilitación de medios de comunicación para ofrecer servicios sexuales de menores 
        - Artículo 219b. Omisión de denuncia
                    
        """),
    margin=(-10, 0, 0, 0)  # Margen superior, derecho, inferior e izquierdo
)

explanation_card = pn.Card(
    delito_explanation,
    title='Explicación Artículos',
    width=350,  # Ancho fijo en píxeles
    margin=(-10, 0, 0, -280),
    collapsible=True,  # Permite plegar/desplegar la carta
    collapsed=True,    # Inicialmente plegada
)

# Crear un panel con la explicación de interacción, el gráfico de pastel y la explicación de los delitos en forma de Card
interaction_panel = pn.Column(interaction_explanation, pn.Row(initial_pie_chart, explanation_card))

# Visualizar el panel
interaction_panel

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Título centrado
title = pn.pane.Markdown('# Abusos sexuales en Colombia', align='center')

# Logo centrado con tamaño fijo
logo = pn.panel('bandera.png', width=200, height=200, align='center')

# Texto centrado
text2 = pn.pane.Markdown('Dataset: http://bit.ly/4604c8H', align='center')

# Texto centrado
text1 = pn.pane.Markdown("""
                        En este conjunto de datos la ciudadanía puede encontrar información sobre delitos sexuales desde el 
                        01 de enero del año 2010 al 31 de mayo del año 2023. Los datos están de acuerdo a la nueva metodología 
                        de validación de denuncias con la Fiscalía General de la Nación, la cual puede ser encontrada en el link
                        """, styles={'text-align': 'justify'})

# Botones centrados
radio_button_panel = pn.Row(radio_buttons, align='center')
radio_button_panel2 = pn.Row(bt2, align='center')

# Slider centrado
year_slider_panel = pn.Row(year_slider, align='center')

# Header box (sin alineación específica)
header_box = pn.Column(title, logo, text1, text2, radio_button_panel, radio_button_panel2, year_slider_panel, align='center', width=300)

# Crear un panel con la gráfica de barras
bar_chart_panel = pn.Card(pn.Column(create_bar_chart, width=800, height=310), title='Frecuencia', width=800)

# Crear un panel con la tabla
table_panel = pn.Card(pn.Column(create_table, width=400, height=373), title='Municipio / Departamento', width=400)

table_panel2 = pn.Card(pn.Column(create_table2, width=400, height=373), title='Armas / Delito', width=400)

# Crear un panel con la grafica de pastel
interaction_panel = pn.Card(pn.Column(interaction_explanation, pn.Row(initial_pie_chart, explanation_card)), title='Artículos', width=770, height=766)

# Alinear verticalmente el encabezado y la tarjeta que contiene el gráfico y las tablas
header_and_chart_table = pn.Card(pn.Row(header_box, pn.Column(pn.Row(bar_chart_panel), pn.Row(table_panel, table_panel2)), interaction_panel), 
                                 title='Dashboard')

# Crear un dashboard que coloca el encabezado a la izquierda y el panel de gráfico y tabla a la derecha
dashboard = pn.Row(header_and_chart_table, sizing_mode="fixed")

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Crear elementos del header y el footer
header = pn.Row(
    pn.pane.Markdown('# Proyecto Final Gestión de Proyectos', align='center'), 
    width=800,
    margin=(0, 0, 0, 0),
    css_classes=['header']
)

# Texto debajo del título
header_text = pn.pane.Markdown("""
                            En el contexto global actual, donde los derechos humanos y la igualdad de género son temas centrales de discusión y acción,
                            se enmarca el proyecto que tiene como objetivo analizar una base de datos sobre violaciones en Colombia. Esta iniciativa surge 
                            en respuesta a la creciente preocupación por los casos de violencia sexual en el país, una problemática que afecta a individuos 
                            de todas las edades, géneros y trasfondos socioeconómicos. Las violaciones no solo tienen un impacto devastador en las víctimas 
                            y sus familias, sino que también generan efectos negativos en la sociedad en su conjunto, erosionando la confianza en las instituciones 
                            y perpetuando patrones de discriminación y desigualdad. En este contexto, el análisis descriptivo de la base de datos busca arrojar 
                            luz sobre las tendencias, patrones geográficos y características demográficas de los incidentes de violación, proporcionando una base 
                            sólida para comunicar la toma de decisiones informadas por parte de las autoridades y los actores involucrados en la prevención y mitigación 
                            de la violencia sexual en Colombia.
                            """, margin=(-20, 20, 0, 20), styles={'text-align': 'justify'})

# Crear un panel para el header
header_panel = pn.Column(
    header,
    header_text,
    sizing_mode="stretch_width"
)

# Crear un panel para el footer
footer = pn.Row(
    pn.pane.Markdown('© 2023 Tu Nombre', align='center'), 
    width=800,
    css_classes=['footer']
)

# Crear un panel para tu dashboard
dashboard_panel = pn.Column(
    header_panel,
    dashboard,
    footer,
    sizing_mode="stretch_width"
)

# Visualizar el panel del dashboard
dashboard_panel.servable()