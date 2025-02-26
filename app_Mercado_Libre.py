import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import base64

# Configuración de la página
st.set_page_config(page_title='ANALIZADOR DE MERCADO PARA MERCADO LIBRE', layout='wide')

# Aumentar el tamaño máximo del archivo cargado a 1000MB (en bytes)
MAX_FILE_SIZE = 1000 * 1024 * 1024  # 1000MB. Streamlit cloud tiene un limite de 200mb

def main():
    # Titulo
    st.title('ANALIZADOR DE MERCADO PARA MERCADO LIBRE')
    # Barra lateral
    menu = ['Página Principal', 'Mercado', 'Estrategia Actual', 'Competencia', 'Estrategia Futura']
    seleccion = st.sidebar.selectbox('Menu de Navegación', menu)

    def pagina_principal():
        carga_archivo = st.file_uploader("Cargue el archivo por favor", type=['xlsx'])

        if carga_archivo is not None:
            try:
                # Check file size before reading
                if carga_archivo.size > MAX_FILE_SIZE:
                    st.error(f"El archivo es demasiado grande. El tamaño máximo permitido es {MAX_FILE_SIZE / (1024 * 1024)} MB")
                    return None  # Or raise an exception, depending on your error handling

                df = pd.read_excel(carga_archivo)

                df = df.rename(columns={'Available Quantity': 'Cantidad Disponible',
                                         'health': 'Estado de Salud',
                                         'Seller2': 'Vendedores',
                                         'Price': 'Precio',
                                         'date_created': 'Fecha de Inicio',
                                         'last_updated': 'Fecha de Última Actualización',
                                         'visits': 'Visitas',
                                         'description': 'Categoría',
                                         'Title': 'Título',
                                         'Fecha': 'Fecha' # Renombrar la columna 'Fecha'
                                         })
                # Convertir las columnas de fecha al tipo datetime si no lo son
                #Primero intento convertir las columnas 'Fecha de Inicio' y 'Fecha de Última Actualización'
                #Solo las convierto si existen en el DataFrame
                if 'Fecha de Inicio' in df.columns:
                    df['Fecha de Inicio'] = pd.to_datetime(df['Fecha de Inicio'], errors='coerce')
                if 'Fecha de Última Actualización' in df.columns:
                    df['Fecha de Última Actualización'] = pd.to_datetime(df['Fecha de Última Actualización'], errors='coerce')

                if 'Fecha' in df.columns:
                    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')  # Convertir la columna 'Fecha'

                st.write('Datos Cargados')
                st.dataframe(df.head())
                return df  # Retornar el DataFrame cargado
            except Exception as e:
                st.error(f"Error al cargar el archivo: {e}")
                return None
        else:
            st.info("Por favor, cargue un archivo Excel.")
            return None









 


 

    def mercado(df, fecha_inicio, fecha_fin):  # Recibe el DataFrame y las fechas como argumento
            st.header("Análisis de Mercado")
            st.subheader("Gráfica de visitas por vendedores")

            # Filtro de fecha aplicado a todo el analisis de mercado
            df_filtrado = df[(df['Fecha'] >= fecha_inicio) & (df['Fecha'] <= fecha_fin)]

            if df_filtrado.empty:
                st.warning("No hay datos en el rango de fechas seleccionado.")
                return None, None  # Retornar None para ambos DataFrames

            # --- Diccionario para almacenar resultados ---
            resultados = {}

            # --- Análisis y Visualizaciones (Funciones internas) ---
            def vendedores_visitas(df_filtrado):
                nonlocal resultados  # Permite modificar la variable 'resultados'
                if df_filtrado is None or 'Vendedores' not in df_filtrado.columns or 'Visitas' not in df_filtrado.columns:
                    st.warning("El DataFrame no tiene las columnas necesarias ('Vendedores', 'Visitas'). Asegúrese de cargar los datos correctamente.")
                    return

                # Agrupar por vendedor y sumar las visitas
                df_sum = df_filtrado.groupby('Vendedores')['Visitas'].sum()

                # Slider para el top de vendedores
                head = st.slider("Top de vendedores", 1, 50, 20)
                st.write(head)

                # Ordenar de forma descendente y seleccionar los principales
                df_sum = df_sum.sort_values(ascending=False).head(head)

                # Almacenar resultados
                resultados['Top Vendedores'] = df_sum.index.tolist() # Guarda los nombres de los vendedores
                resultados['Visitas Top Vendedores'] = df_sum.values.tolist() # Guarda las visitas

                # Crear la barra de colores con Plotly Express
                fig = px.bar(df_sum,
                            x=df_sum.index,
                            y='Visitas',
                            title=f'Top {head} Vendedores por Número de Visitas (entre {fecha_inicio.strftime("%Y-%m-%d")} y {fecha_fin.strftime("%Y-%m-%d")})',
                            color=df_sum.values,  # Usar los valores de visitas para el color
                            color_continuous_scale=px.colors.sequential.Plasma)  # Elegir una paleta de colores.  Plasma es una buena opción.

                # Personalizar el diseño (opcional)
                fig.update_layout(
                    xaxis_title="Vendedor",
                    yaxis_title="Número de Visitas",
                    xaxis={'categoryorder': 'total descending'}  # Ordenar las barras por valor descendente
                )

                # Mostrar la figura
                st.plotly_chart(fig)

            def vendedores_vistas(df_filtrado):
                nonlocal resultados
                if df_filtrado is None or 'Categoría' not in df_filtrado.columns or 'Visitas' not in df_filtrado.columns:
                    st.warning("El DataFrame no tiene las columnas necesarias ('Categoría', 'Visitas').  Asegúrese de cargar los datos correctamente.")
                    return

                # Agrupar por categoría y sumar las visitas
                df_sum = df_filtrado.groupby('Categoría')['Visitas'].sum()

                head = st.slider("Top de Categorías", 1, 50, 20)
                st.write(head)

                # Ordenar de forma descendente y seleccionar los principales
                df_sum = df_sum.sort_values(ascending=False).head(head)

                # Almacenar resultados
                resultados['Top Categorías'] = df_sum.index.tolist()
                resultados['Visitas Top Categorías'] = df_sum.values.tolist()

                # Crear la barra de colores con Plotly Express
                fig = px.bar(df_sum,
                            x=df_sum.index,
                            y='Visitas',
                            title=f'Top {head} Categorías por Número de Visitas (entre {fecha_inicio.strftime("%Y-%m-%d")} y {fecha_fin.strftime("%Y-%m-%d")})',
                            color=df_sum.values,  # Usar los valores de visitas para el color
                            color_continuous_scale=px.colors.sequential.Plasma)  # Elegir una paleta de colores.  Plasma es una buena opción.

                # Personalizar el diseño (opcional)
                fig.update_layout(
                    xaxis_title="Categoría",
                    yaxis_title="Número de Visitas",
                    xaxis={'categoryorder': 'total descending'}  # Ordenar las barras por valor descendente
                )

                # Mostrar la figura
                st.plotly_chart(fig)

            def estado_salud_categorias(df_filtrado):
                nonlocal resultados
                if df_filtrado is None or 'Categoría' not in df_filtrado.columns or 'Estado de Salud' not in df_filtrado.columns:
                    st.warning("El DataFrame no tiene las columnas necesarias ('Categoría', 'Estado de Salud'). Asegúrese de cargar los datos correctamente.")
                    return

                # Agrupar por categoría y calcular el estado de salud promedio
                df_mean = df_filtrado.groupby('Categoría')['Estado de Salud'].mean()

                # Slider para el top de categorias
                head = st.slider("Top de Categorías por Estado de Salud", 1, 50, 20)
                st.write(head)

                # Ordenar de forma descendente y seleccionar los principales
                df_mean = df_mean.sort_values(ascending=False).head(head)

                # Almacenar resultados
                resultados['Top Categorías (Salud)'] = df_mean.index.tolist()
                resultados['Salud Promedio Top Categorías'] = df_mean.values.tolist()

                # Crear la barra de colores con Plotly Express
                fig = px.bar(df_mean,
                            x=df_mean.index,
                            y=df_mean.values,
                            title=f'Top {head} Categorías por Estado de Salud Promedio (entre {fecha_inicio.strftime("%Y-%m-%d")} y {fecha_fin.strftime("%Y-%m-%d")})',
                            color=df_mean.values,  # Usar los valores de visitas para el color
                            color_continuous_scale=px.colors.sequential.Plasma)  # Elegir una paleta de colores.  Plasma es una buena opción.

                # Personalizar el diseño (opcional)
                fig.update_layout(
                    xaxis_title="Categorías",
                    yaxis_title="Estado de Salud Promedio",
                    xaxis={'categoryorder': 'total descending'}  # Ordenar las barras por valor descendente
                )

                # Mostrar la figura en Streamlit
                st.plotly_chart(fig)

            def analizar_disponibilidad_categorias(df_filtrado):
                nonlocal resultados
                if df_filtrado is None or 'Categoría' not in df_filtrado.columns or 'Cantidad Disponible' not in df_filtrado.columns:
                    st.warning("El DataFrame no tiene las columnas necesarias ('Categoría', 'Cantidad Disponible'). Asegúrese de cargar los datos correctamente.")
                    return

                # Calcular el promedio de cantidad disponible por categoría
                df_promedio = df_filtrado.groupby('Categoría')['Cantidad Disponible'].mean().reset_index()
                df_promedio = df_promedio.rename(columns={'Cantidad Disponible': 'Promedio Disponible'})

                # Slider para el top de categorias
                head = st.slider("Top de Categorías por Cantidad Disponible", 1, 50, 20)
                st.write(head)

                # Ordenar y seleccionar el top
                df_promedio = df_promedio.sort_values(by='Promedio Disponible', ascending=False).head(head)

                # Almacenar resultados
                resultados['Top Categorías (Disponibilidad)'] = df_promedio['Categoría'].tolist()
                resultados['Disponibilidad Promedio Top Categorías'] = df_promedio['Promedio Disponible'].tolist()

                # Crear el gráfico de barras
                fig = px.bar(df_promedio,
                            x='Categoría',
                            y='Promedio Disponible',
                            title=f'Top {head} Promedio de Cantidades Disponibles por Categoría (entre {fecha_inicio.strftime("%Y-%m-%d")} y {fecha_fin.strftime("%Y-%m-%d")})',
                            color='Promedio Disponible',
                            color_continuous_scale=px.colors.sequential.Viridis)

                # Personalizar el diseño
                fig.update_layout(
                    xaxis_title="Categoría",
                    yaxis_title="Cantidad Disponible Promedio",
                    xaxis={'categoryorder': 'total descending'}
                )

                # Mostrar el gráfico en Streamlit
                st.plotly_chart(fig)

            def oem_efficiency(df_filtrado):
                nonlocal resultados
                if df_filtrado is None or 'OEM' not in df_filtrado.columns or 'Visitas' not in df_filtrado.columns:
                    st.warning("El DataFrame no tiene las columnas necesarias ('description', 'Visitas'). Asegúrese de cargar los datos correctamente.")
                    return

                oem_column = df_filtrado['OEM']  # Utiliza 'description' para OEM
                visits_column = df_filtrado['Visitas']

                # Create a DataFrame for easier processing
                df_oem = pd.DataFrame({'OEM': oem_column, 'Visitas': visits_column})

                # Group by OEM and sum the visits
                oem_visits = df_oem.groupby('OEM')['Visitas'].sum()

                # Calculate the *number* of times each OEM appears in the data.  This is the change!
                oem_counts = df_oem['OEM'].value_counts()  #Count each OEM

                # Calculate the efficiency for each OEM: visits / count
                oem_efficiency = oem_visits / oem_counts

                # Slider for the top of OEMs
                top_n = st.slider("Top N OEMs", 1, 50, 20)
                st.write(top_n)

                # Sort by efficiency and get the top N
                top_oem_efficiency = oem_efficiency.sort_values(ascending=False).head(top_n)

                # Almacenar resultados
                resultados['Top OEMs (Eficiencia)'] = top_oem_efficiency.index.tolist()
                resultados['Eficiencia Top OEMs'] = top_oem_efficiency.values.tolist()

                # Create the bar chart with Plotly Express
                fig = px.bar(
                    x=top_oem_efficiency.index,
                    y=top_oem_efficiency.values,
                    title=f'Top {top_n} Eficiencia de cada OEM (entre {fecha_inicio.strftime("%Y-%m-%d")} y {fecha_fin.strftime("%Y-%m-%d")})',
                    labels={'x': 'OEM', 'y': 'Eficiencia (Visitas / Count of OEM)'},
                    color=top_oem_efficiency.values,
                    color_continuous_scale=px.colors.sequential.Viridis
                )

                fig.update_layout(
                    xaxis_title="OEM",
                    yaxis_title="Eficiencia",
                    xaxis={'categoryorder': 'total descending'}
                )

                st.plotly_chart(fig)

            def categoria_efficiency(df_filtrado):
                nonlocal resultados
                if df_filtrado is None or 'Categoría' not in df_filtrado.columns or 'Visitas' not in df_filtrado.columns:
                    st.warning("El DataFrame no tiene las columnas necesarias ('Categoría', 'Visitas'). Asegúrese de cargar los datos correctamente.")
                    return

                categoría_column = df_filtrado['Categoría']
                visits_column = df_filtrado['Visitas']

                # Create a DataFrame for easier processing
                df_cat = pd.DataFrame({'Categoría': categoría_column, 'Visitas': visits_column})

                # Group by category and sum the visits
                cat_visits = df_cat.groupby('Categoría')['Visitas'].sum()

                # Calculate the *number* of times each category appears in the data
                cat_counts = df_cat['Categoría'].value_counts()

                # Calculate the efficiency for each category: visits / count
                cat_efficiency = cat_visits / cat_counts

                # Slider for the top of Categories
                top_n = st.slider("Top N Categorías", 1, 50, 20)
                st.write(top_n)

                # Sort by efficiency and get the top N
                top_cat_efficiency = cat_efficiency.sort_values(ascending=False).head(top_n)

                # Almacenar resultados
                resultados['Top Categorías (Eficiencia)'] = top_cat_efficiency.index.tolist()
                resultados['Eficiencia Top Categorías'] = top_cat_efficiency.values.tolist()

                # Create the bar chart with Plotly Express
                fig = px.bar(
                    x=top_cat_efficiency.index,
                    y=top_cat_efficiency.values,
                    title=f'Top {top_n} Eficiencia de cada Categoría (entre {fecha_inicio.strftime("%Y-%m-%d")} y {fecha_fin.strftime("%Y-%m-%d")})',
                    labels={'x': 'Categoría', 'y': 'Eficiencia (Visitas / Count of Categoría)'},
                    color=top_cat_efficiency.values,
                    color_continuous_scale=px.colors.sequential.Viridis
                )

                fig.update_layout(
                    xaxis_title="Categoría",
                    yaxis_title="Eficiencia",
                    xaxis={'categoryorder': 'total descending'}
                )

                st.plotly_chart(fig)

            # Llamar a las funciones de visualización
            vendedores_visitas(df_filtrado)
            vendedores_vistas(df_filtrado)
            estado_salud_categorias(df_filtrado)
            analizar_disponibilidad_categorias(df_filtrado)
            oem_efficiency(df_filtrado)
            categoria_efficiency(df_filtrado)

            # --- Crear DataFrame de Resultados ---
            df_resultados = pd.DataFrame.from_dict(resultados, orient='index').transpose()
            st.subheader("DataFrame de Resultados")
            st.dataframe(df_resultados)

            # --- Descargar DataFrame de Resultados a Excel ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_resultados.to_excel(writer, index=False, sheet_name='Resultados')
            excel_data = output.getvalue()
            b64 = base64.b64encode(excel_data).decode('utf-8')
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="resultados.xlsx">Descargar DataFrame de Resultados como Excel</a>'
            st.markdown(href, unsafe_allow_html=True)

            # --- DataFrame Combinado (Nueva Sección) ---
            st.subheader("DataFrame Combinado")

            # Selector de vendedor
            vendedores_unicos = df_filtrado['Vendedores'].unique()
            vendedores = st.selectbox("Selecciona un vendedor", vendedores_unicos)

            def crear_dataframe_combinado(df, vendedores):
                """Crea un DataFrame combinado con información relevante."""
                if df is None or 'Categoría' not in df.columns or 'Título' not in df.columns or 'OEM' not in df.columns or 'Visitas' not in df.columns or 'Cantidad Disponible' not in df.columns or 'Estado de Salud' not in df.columns or 'Vendedores' not in df.columns or 'permalink' not in df.columns or 'ID' not in df.columns:
                    st.warning("Error: Faltan columnas necesarias en el DataFrame.  Asegúrate de tener 'Categoría', 'Título', 'OEM', 'Visitas', 'Cantidad Disponible', 'Estado de Salud', 'Vendedores', 'permalink' y 'ID'.")
                    return None

                df_vendedor = df[df['Vendedores'] == vendedores].copy() # Importante usar .copy() para evitar SettingWithCopyWarning

                # Calcular la cantidad de publicaciones por categoría
                publicaciones_por_categoria = df_vendedor.groupby('Categoría').size().reset_index(name='Cantidad Publicaciones')
                df_vendedor = pd.merge(df_vendedor, publicaciones_por_categoria, on='Categoría', how='left')

                # Agrupar por 'OEM' y calcular la suma de visitas
                oem_visitas = df_vendedor.groupby('OEM')['Visitas'].sum().reset_index(name='Visitas por OEM')
                df_vendedor = pd.merge(df_vendedor, oem_visitas, on='OEM', how='left')

                # Calcular eficiencia del vendedor
                total_visitas = df_vendedor['Visitas'].sum()
                total_titulos = df_vendedor['Título'].nunique()
                eficiencia_vendedor = total_visitas / total_titulos if total_titulos > 0 else 0
                df_vendedor['Eficiencia Vendedor'] = eficiencia_vendedor  # Agregar al DataFrame

                # Eliminar duplicados para que cada fila represente una combinación única
                df_resumen = df_vendedor[['Categoría', 'Título', 'OEM', 'Visitas', 'Cantidad Disponible', 'Estado de Salud', 'Cantidad Publicaciones', 'Visitas por OEM', 'Eficiencia Vendedor', 'permalink', 'ID']].drop_duplicates()

                # Calcular la eficiencia
                visitas_totales = df.groupby('OEM')['Visitas'].sum() # Visitas totales por OEM de todos los vendedores
                eficiencia_oem = (df_vendedor['Visitas por OEM'] / visitas_totales[df_vendedor['OEM']].values).fillna(0)  # Eficiencia para cada fila

                df_resumen['Eficiencia OEM'] = eficiencia_oem # Agrega la eficiencia calculada

                # Calcular Health promedio por categoria
                health_medio_por_categoria = df_vendedor.groupby('Categoría')['Estado de Salud'].mean().reset_index(name = "Health Medio Categoria")
                df_resumen = pd.merge(df_resumen, health_medio_por_categoria, on='Categoría', how='left')
                df_resumen = df_resumen.fillna(0)

                return df_resumen

            df_combinado = crear_dataframe_combinado(df_filtrado, vendedores)

            if df_combinado is not None:
                st.dataframe(df_combinado)
                # Opción de descarga (excel)
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_combinado.to_excel(writer, index=False, sheet_name='DataCombinada')
                excel_data = output.getvalue()
                b64 = base64.b64encode(excel_data).decode('utf-8')
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="data_combinada.xlsx">Descargar DataFrame Combinado como Excel</a>'
                st.markdown(href, unsafe_allow_html=True)

            return df_resultados, df_combinado  # Retornar ambos DataFrames





    def estrategia_actual(df_filtrado):  # Recibe el DataFrame filtrado como argumento
        st.header("Estrategia Actual")

        # Verifica si df_filtrado está vacío antes de continuar
        if df_filtrado is None or df_filtrado.empty:
            st.warning("No hay datos en el rango de fechas seleccionado.")
            return

        lista_vendedores = df_filtrado['Vendedores'].unique()
        vendedores = st.selectbox('Seleccione un Vendedor', lista_vendedores)

        # --- Visitas por Título ---
        st.subheader(f"Grafica de Visitas por Título para {vendedores}")

        def visitas_titulos_vendedores(df_filtrado, vendedores):
            """Muestra la gráfica de visitas por título para un vendedor específico."""
            if df_filtrado is None or 'Título' not in df_filtrado.columns or 'Visitas' not in df_filtrado.columns or 'Vendedores' not in df_filtrado.columns:
                st.warning("Error: Las columnas 'Título', 'Visitas' y 'Vendedores' deben estar presentes en el DataFrame.")
                return

            df_vendedor = df_filtrado[df_filtrado['Vendedores'] == vendedores]
            df_sum = df_vendedor.groupby('Título')['Visitas'].sum().reset_index()
            head = st.slider('Top Títulos por Visitas', 1, 50, 20, key="titulos_visitas")  # key para evitar conflicto de sliders
            df_sum = df_sum.sort_values(by='Visitas', ascending=False).head(head)

            fig = px.bar(df_sum, x='Título', y='Visitas',
                        title=f'Top {head} Títulos por Visitas para {vendedores}',
                        labels={'Título': 'Título', 'Visitas': 'Visitas'},
                        color='Visitas', color_continuous_scale=px.colors.sequential.Plasma)
            fig.update_layout(xaxis_title='Título', yaxis_title='Visitas', xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)

        visitas_titulos_vendedores(df_filtrado, vendedores)

        # --- Visitas por OEM ---
        st.subheader(f"Gráfica de Visitas por OEM para {vendedores}")

        def visitas_oem_vendedores(df_filtrado, vendedores):
            """Muestra la gráfica de visitas por OEM para un vendedor específico."""
            if df_filtrado is None or 'OEM' not in df_filtrado.columns or 'Visitas' not in df_filtrado.columns or 'Vendedores' not in df_filtrado.columns:
                st.warning("Error: Las columnas 'OEM', 'Visitas' y 'Vendedores' deben estar presentes en el DataFrame.")
                return

            df_vendedor = df_filtrado[df_filtrado['Vendedores'] == vendedores]
            df_sum = df_vendedor.groupby('OEM')['Visitas'].sum().reset_index()
            head = st.slider('Top OEMs por Visitas', 1, 50, 20, key="oem_visitas")  # key para evitar conflicto de sliders
            df_sum = df_sum.sort_values(by='Visitas', ascending=False).head(head)

            fig = px.bar(df_sum, x='OEM', y='Visitas',
                        title=f'Top {head} OEMs por Visitas para {vendedores}',
                        labels={'OEM': 'OEM', 'Visitas': 'Visitas'},
                        color='Visitas', color_continuous_scale=px.colors.sequential.Plasma)
            fig.update_layout(xaxis_title='OEM', yaxis_title='Visitas', xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)

        visitas_oem_vendedores(df_filtrado, vendedores)

        # --- Cantidad de Publicaciones por Categoría ---
        st.subheader(f"Gráfica de Cantidad de Publicaciones por Categoría para {vendedores}")

        def publicaciones_por_categoria(df_filtrado, vendedores):
            """Muestra la cantidad de publicaciones por categoría para un vendedor."""
            if df_filtrado is None or 'Categoría' not in df_filtrado.columns or 'Vendedores' not in df_filtrado.columns:
                st.warning("Error: Las columnas 'Categoría' y 'Vendedores' deben estar presentes en el DataFrame.")
                return

            df_vendedor = df_filtrado[df_filtrado['Vendedores'] == vendedores]
            df_count = df_vendedor.groupby('Categoría').size().reset_index(name='Cantidad') # Usamos size() para contar
            head = st.slider('Top Categorías por Publicaciones', 1, 50, 20, key="cat_publicaciones")  # key para evitar conflicto de sliders
            df_count = df_count.sort_values(by='Cantidad', ascending=False).head(head)

            fig = px.bar(df_count, x='Categoría', y='Cantidad',
                        title=f'Top {head} Categorías por Cantidad de Publicaciones para {vendedores}',
                        labels={'Categoría': 'Categoría', 'Cantidad': 'Cantidad de Publicaciones'},
                        color='Cantidad', color_continuous_scale=px.colors.sequential.Plasma)
            fig.update_layout(xaxis_title='Categoría', yaxis_title='Cantidad de Publicaciones', xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)

        publicaciones_por_categoria(df_filtrado, vendedores)

        # --- Cantidades Disponibles por Título ---
        st.subheader(f"Gráfica de Cantidades Disponibles por Título para {vendedores}")

        def cantidades_disponibles_por_titulo(df_filtrado, vendedores):
            """Muestra la cantidad disponible por título para un vendedor."""
            if df_filtrado is None or 'Título' not in df_filtrado.columns or 'Cantidad Disponible' not in df_filtrado.columns or 'Vendedores' not in df_filtrado.columns:
                st.warning("Error: Las columnas 'Título', 'Cantidad Disponible' y 'Vendedores' deben estar presentes en el DataFrame.")
                return

            df_vendedor = df_filtrado[df_filtrado['Vendedores'] == vendedores]
            df_sum = df_vendedor.groupby('Título')['Cantidad Disponible'].sum().reset_index()
            head = st.slider('Top Títulos por Cantidad Disponible', 1, 50, 20, key="titulo_cantidad")  # key para evitar conflicto de sliders
            df_sum = df_sum.sort_values(by='Cantidad Disponible', ascending=False).head(head)

            fig = px.bar(df_sum, x='Título', y='Cantidad Disponible',
                        title=f'Top {head} Títulos por Cantidad Disponible para {vendedores}',
                        labels={'Título': 'Título', 'Cantidad Disponible': 'Cantidad Disponible'},
                        color='Cantidad Disponible', color_continuous_scale=px.colors.sequential.Plasma)
            fig.update_layout(xaxis_title='Título', yaxis_title='Cantidad Disponible', xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)

        cantidades_disponibles_por_titulo(df_filtrado, vendedores)

        # --- Eficiencia en el Mercado (OEM) ---
        st.subheader(f"Eficiencia en el Mercado (OEM) para {vendedores}")

        def eficiencia_mercado_oem(df, vendedores):
            """Calcula y muestra la eficiencia en el mercado (OEM) para un vendedor."""
            if df is None or 'OEM' not in df.columns or 'Visitas' not in df.columns or 'Vendedores' not in df.columns:
                st.warning("Error: Las columnas 'OEM', 'Visitas' y 'Vendedores' deben estar presentes en el DataFrame.")
                return

            # Total de visitas de los OEM del vendedor
            df_vendedor = df[df['Vendedores'] == vendedores]
            visitas_vendedor = df_vendedor.groupby('OEM')['Visitas'].sum()

            # Total de visitas de esos mismos OEM de todos los vendedores
            visitas_totales = df.groupby('OEM')['Visitas'].sum()

            # Calcular la eficiencia
            eficiencia = (visitas_vendedor / visitas_totales).fillna(0)  # Manejar divisiones por cero

            # Crear DataFrame para la gráfica
            df_eficiencia = eficiencia.reset_index(name='Eficiencia')
            df_eficiencia = df_eficiencia.sort_values(by='Eficiencia', ascending=False)
            head = st.slider('Top OEMs por Eficiencia', 1, 50, 20, key="oem_eficiencia")  # key para evitar conflicto de sliders
            df_eficiencia = df_eficiencia.head(head)

            # Crear la gráfica
            fig = px.bar(df_eficiencia, x='OEM', y='Eficiencia',
                        title=f'Top {head} Eficiencia en el Mercado (OEM) para {vendedores}',
                        labels={'OEM': 'OEM', 'Eficiencia': 'Eficiencia'},
                        color='Eficiencia', color_continuous_scale=px.colors.sequential.Plasma)
            fig.update_layout(xaxis_title='OEM', yaxis_title='Eficiencia', xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)

        eficiencia_mercado_oem(df_filtrado, vendedores)

        # --- Health Medio por Categoría ---
        st.subheader(f"Health Medio por Categoría para {vendedores}")

        def health_medio_por_categoria(df_filtrado, vendedores):
            """Calcula y muestra el health medio por categoría para un vendedor."""
            if df_filtrado is None or 'Categoría' not in df_filtrado.columns or 'Estado de Salud' not in df_filtrado.columns or 'Vendedores' not in df_filtrado.columns:
                st.warning("Error: Las columnas 'Categoría', 'Estado de Salud' y 'Vendedores' deben estar presentes en el DataFrame.")
                return

            df_vendedor = df_filtrado[df_filtrado['Vendedores'] == vendedores]
            health_medio = df_vendedor.groupby('Categoría')['Estado de Salud'].mean().reset_index()
            health_medio = health_medio.sort_values(by='Estado de Salud', ascending=False)

            head = st.slider('Top Categorías por Health Medio', 1, 50, 20, key="health_medio")  # key para evitar conflicto de sliders
            health_medio = health_medio.head(head)

            fig = px.bar(health_medio, x='Categoría', y='Estado de Salud',
                        title=f'Top {head} Health Medio por Categoría para {vendedores}',
                        labels={'Categoría': 'Categoría', 'Estado de Salud': 'Health Medio'},
                        color='Estado de Salud', color_continuous_scale=px.colors.sequential.Plasma)

            fig.update_layout(xaxis_title='Categoría', yaxis_title='Health Medio', xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)

        health_medio_por_categoria(df_filtrado, vendedores)

        # --- Eficiencia del Vendedor ---
        st.subheader(f"Eficiencia del Vendedor ({vendedores})")

        def eficiencia_del_vendedor(df_filtrado, vendedores):
            """Calcula y muestra la eficiencia del vendedor (Total Visitas / Total Títulos)."""
            if df_filtrado is None or 'Título' not in df_filtrado.columns or 'Visitas' not in df_filtrado.columns or 'Vendedores' not in df_filtrado.columns:
                st.warning("Error: Las columnas 'Título', 'Visitas' y 'Vendedores' deben estar presentes en el DataFrame.")
                return

            df_vendedor = df_filtrado[df_filtrado['Vendedores'] == vendedores]
            total_visitas = df_vendedor['Visitas'].sum()
            total_titulos = df_vendedor['Título'].nunique()  # Usa nunique() para contar títulos únicos

            if total_titulos == 0:
                st.warning("El vendedor no tiene títulos.")
                return

            eficiencia = total_visitas / total_titulos

            st.metric(label=f"Eficiencia del Vendedor ({vendedores})", value=f"{eficiencia:.2f}") #Muestra el valor con dos decimales

            # No se necesita gráfico para un solo valor, pero podrías mostrarlo en un indicador
            # st.write(f"Eficiencia del Vendedor (Total Visitas / Total Títulos): {eficiencia:.2f}")

        eficiencia_del_vendedor(df_filtrado, vendedores)

        # --- DataFrame con Información Combinada ---
        st.subheader("DataFrame con Información Combinada")

        def crear_dataframe_combinado(df, vendedores):
            """Crea un DataFrame combinado con información relevante."""
            if df is None or 'Categoría' not in df.columns or 'Título' not in df.columns or 'OEM' not in df.columns or 'Visitas' not in df.columns or 'Cantidad Disponible' not in df.columns or 'Estado de Salud' not in df.columns or 'Vendedores' not in df.columns or 'permalink' not in df.columns or 'ID' not in df.columns:
                st.warning("Error: Faltan columnas necesarias en el DataFrame.  Asegúrate de tener 'Categoría', 'Título', 'OEM', 'Visitas', 'Cantidad Disponible', 'Estado de Salud', 'Vendedores', 'permalink' y 'ID'.")
                return None

            df_vendedor = df[df['Vendedores'] == vendedores].copy() # Importante usar .copy() para evitar SettingWithCopyWarning

            # Calcular la cantidad de publicaciones por categoría
            publicaciones_por_categoria = df_vendedor.groupby('Categoría').size().reset_index(name='Cantidad Publicaciones')
            df_vendedor = pd.merge(df_vendedor, publicaciones_por_categoria, on='Categoría', how='left')

            # Agrupar por 'OEM' y calcular la suma de visitas
            oem_visitas = df_vendedor.groupby('OEM')['Visitas'].sum().reset_index(name='Visitas por OEM')
            df_vendedor = pd.merge(df_vendedor, oem_visitas, on='OEM', how='left')

            # Calcular eficiencia del vendedor
            total_visitas = df_vendedor['Visitas'].sum()
            total_titulos = df_vendedor['Título'].nunique()
            eficiencia_vendedor = total_visitas / total_titulos if total_titulos > 0 else 0
            df_vendedor['Eficiencia Vendedor'] = eficiencia_vendedor  # Agregar al DataFrame

            # Eliminar duplicados para que cada fila represente una combinación única
            df_resumen = df_vendedor[['Categoría', 'Título', 'OEM', 'Visitas', 'Cantidad Disponible', 'Estado de Salud', 'Cantidad Publicaciones', 'Visitas por OEM', 'Eficiencia Vendedor', 'permalink', 'ID']].drop_duplicates()

            # Calcular la eficiencia
            visitas_totales = df.groupby('OEM')['Visitas'].sum() # Visitas totales por OEM de todos los vendedores
            eficiencia_oem = (df_vendedor['Visitas por OEM'] / visitas_totales[df_vendedor['OEM']].values).fillna(0)  # Eficiencia para cada fila

            df_resumen['Eficiencia OEM'] = eficiencia_oem # Agrega la eficiencia calculada

            # Calcular Health promedio por categoria
            health_medio_por_categoria = df_vendedor.groupby('Categoría')['Estado de Salud'].mean().reset_index(name = "Health Medio Categoria")
            df_resumen = pd.merge(df_resumen, health_medio_por_categoria, on='Categoría', how='left')
            df_resumen = df_resumen.fillna(0)

            return df_resumen

        df_combinado = crear_dataframe_combinado(df_filtrado, vendedores)

        if df_combinado is not None:
            st.dataframe(df_combinado)
            # Opción de descarga (excel)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_combinado.to_excel(writer, index=False, sheet_name='DataCombinada')
            excel_data = output.getvalue()
            b64 = base64.b64encode(excel_data).decode('utf-8')
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="data_combinada.xlsx">Descargar DataFrame Combinado como Excel</a>'
            st.markdown(href, unsafe_allow_html=True)


        
        
        
        
        
        
            
    def competencia(df, fecha_inicio, fecha_fin):
        st.header("Análisis de la Competencia")

        # 1) Selección del Vendedor
        lista_vendedores = df['Vendedores'].unique()
        vendedor_seleccionado = st.selectbox('Seleccione un Vendedor (para comparar con la competencia)', lista_vendedores)

        # 2) Filtro de Fecha (ya aplicado - df recibido ya debe estar filtrado)
        df_filtrado = df[(df['Fecha'] >= fecha_inicio) & (df['Fecha'] <= fecha_fin)]

        # 3) Selección del OEM
        lista_oem = df_filtrado['OEM'].unique()
        oem_seleccionado = st.selectbox('Seleccione un OEM', lista_oem)

        # Filtrar por OEM seleccionado
        df_oem = df_filtrado[df_filtrado['OEM'] == oem_seleccionado]

        # Funciones de Variación (4, 5, 6)
        def variacion_precios_oem(df_oem, oem_seleccionado):
            """Muestra la variación de precios (en $) del OEM seleccionado entre todos los vendedores, incluido el seleccionado."""
            if df_oem is None or 'Vendedores' not in df_oem.columns or 'Precio' not in df_oem.columns or 'OEM' not in df_oem.columns:
                st.warning("Error: Faltan columnas necesarias en el DataFrame ('Vendedores', 'Precio', 'OEM').")
                return

            # Calcular el precio promedio por vendedor (incluyendo al vendedor seleccionado)
            df_competidores = df_oem.groupby('Vendedores')['Precio'].mean().reset_index()

            if df_competidores.empty:
                st.warning(f"No hay vendedores que vendan el OEM '{oem_seleccionado}'.")
                return

            # Formatear el precio como moneda ($)
            df_competidores['Precio'] = df_competidores['Precio'].apply(lambda x: '${:.2f}'.format(x))

            # Slider para el Top N
            head = st.slider(f'Top Vendedores por Variación de Precio ({oem_seleccionado})', 1, len(df_competidores), min(10, len(df_competidores)), key = 'precio')

            # Ordenar por precio y seleccionar el Top N
            df_competidores = df_competidores.sort_values(by='Precio', ascending=False).head(head)

            # Crear gráfico de barras
            fig = px.bar(df_competidores, x='Vendedores', y='Precio',
                        title=f'Top {head} Vendedores por Precio Promedio ({oem_seleccionado})',
                        labels={'Vendedores': 'Vendedor', 'Precio': 'Precio Promedio ($)'},
                        color='Precio', color_continuous_scale=px.colors.sequential.Plasma)
            fig.update_layout(xaxis_title='Vendedor', yaxis_title='Precio Promedio ($)', xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)

        def variacion_cantidad_disponible_oem(df_oem, oem_seleccionado):
            """Muestra la variación de cantidad disponible del OEM seleccionado entre todos los vendedores, incluido el seleccionado."""
            if df_oem is None or 'Vendedores' not in df_oem.columns or 'Cantidad Disponible' not in df_oem.columns or 'OEM' not in df_oem.columns:
                st.warning("Error: Faltan columnas necesarias en el DataFrame ('Vendedores', 'Cantidad Disponible', 'OEM').")
                return

            # Calcular la cantidad disponible promedio por vendedor (incluyendo al vendedor seleccionado)
            df_competidores = df_oem.groupby('Vendedores')['Cantidad Disponible'].mean().reset_index()

            if df_competidores.empty:
                st.warning(f"No hay vendedores que vendan el OEM '{oem_seleccionado}'.")
                return

            # Slider para el Top N
            head = st.slider(f'Top Vendedores por Variación de Cantidad Disponible ({oem_seleccionado})', 1, len(df_competidores), min(10, len(df_competidores)), key = 'cantidad')

            # Ordenar por cantidad disponible y seleccionar el Top N
            df_competidores = df_competidores.sort_values(by='Cantidad Disponible', ascending=False).head(head)

            # Crear gráfico de barras
            fig = px.bar(df_competidores, x='Vendedores', y='Cantidad Disponible',
                        title=f'Top {head} Vendedores por Cantidad Disponible Promedio ({oem_seleccionado})',
                        labels={'Vendedores': 'Vendedor', 'Cantidad Disponible': 'Cantidad Disponible Promedio'},
                        color='Cantidad Disponible', color_continuous_scale=px.colors.sequential.Plasma)
            fig.update_layout(xaxis_title='Vendedor', yaxis_title='Cantidad Disponible Promedio', xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)

        def variacion_health_oem(df_oem, oem_seleccionado):
            """Muestra la variación de health del OEM seleccionado entre todos los vendedores, incluido el seleccionado."""
            if df_oem is None or 'Vendedores' not in df_oem.columns or 'Estado de Salud' not in df_oem.columns or 'OEM' not in df_oem.columns:
                st.warning("Error: Faltan columnas necesarias en el DataFrame ('Vendedores', 'Estado de Salud', 'OEM').")
                return

            # Calcular el health promedio por vendedor (incluyendo al vendedor seleccionado)
            df_competidores = df_oem.groupby('Vendedores')['Estado de Salud'].mean().reset_index()

            if df_competidores.empty:
                st.warning(f"No hay vendedores que vendan el OEM '{oem_seleccionado}'.")
                return

            # Slider para el Top N
            head = st.slider(f'Top Vendedores por Variación de Health ({oem_seleccionado})', 1, len(df_competidores), min(10, len(df_competidores)), key = 'health')

            # Ordenar por health y seleccionar el Top N
            df_competidores = df_competidores.sort_values(by='Estado de Salud', ascending=False).head(head)

            # Crear gráfico de barras
            fig = px.bar(df_competidores, x='Vendedores', y='Estado de Salud',
                        title=f'Top {head} Vendedores por Health Promedio ({oem_seleccionado})',
                        labels={'Vendedores': 'Vendedor', 'Estado de Salud': 'Health Promedio'},
                        color='Estado de Salud', color_continuous_scale=px.colors.sequential.Plasma)
            fig.update_layout(xaxis_title='Vendedor', yaxis_title='Health Promedio', xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)

        def comparacion_visitas_oem(df, oem_seleccionado):
            """Compara las visitas por OEM entre todos los vendedores, incluido el seleccionado."""
            if df is None or 'Vendedores' not in df.columns or 'Visitas' not in df.columns or 'OEM' not in df.columns:
                st.warning("Error: Faltan columnas necesarias en el DataFrame ('Vendedores', 'Visitas', 'OEM').")
                return

            # Visitas de todos los vendedores para el OEM seleccionado
            df_competidores = df[df['OEM'] == oem_seleccionado].groupby('Vendedores')['Visitas'].sum().reset_index()

            if df_competidores.empty:
                st.warning(f"No hay vendedores que vendan el OEM '{oem_seleccionado}'.")
                return

            # Slider para el Top N
            head = st.slider(f'Top Vendedores por Visitas ({oem_seleccionado})', 1, len(df_competidores), min(10, len(df_competidores)), key = 'visitas')

            # Ordenar por visitas y seleccionar el Top N
            df_competidores = df_competidores.sort_values(by='Visitas', ascending=False).head(head)

            # Crear gráfico de barras
            fig = px.bar(df_competidores, x='Vendedores', y='Visitas',
                        title=f'Top {head} Vendedores por Visitas ({oem_seleccionado})',
                        labels={'Vendedores': 'Vendedor', 'Visitas': 'Visitas'},
                        color='Visitas', color_continuous_scale=px.colors.sequential.Plasma)
            fig.update_layout(xaxis_title='Vendedor', yaxis_title='Visitas', xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)

        # Llamar a las funciones de variación
        variacion_precios_oem(df_oem, oem_seleccionado)
        variacion_cantidad_disponible_oem(df_oem, oem_seleccionado)
        variacion_health_oem(df_oem, oem_seleccionado)

        # Llamar a la función de comparación de visitas
        st.subheader("Comparación de Visitas por OEM")
        comparacion_visitas_oem(df_filtrado, oem_seleccionado)

        # 7) DataFrame Combinado
        st.subheader("DataFrame de Competencia")

        def crear_dataframe_competencia(df, oem_seleccionado):
            """Crea un DataFrame con información de todos los vendedores (incluido el seleccionado) para el OEM seleccionado."""
            # Reemplazar 'item_id' por 'ID' y 'URL' por 'permalink'
            if df is None or 'Vendedores' not in df.columns or 'Título' not in df.columns or 'ID' not in df.columns or 'permalink' not in df.columns or 'Precio' not in df.columns or 'Cantidad Disponible' not in df.columns or 'Estado de Salud' not in df.columns or 'OEM' not in df.columns or 'Visitas' not in df.columns:
                st.warning("Error: Faltan columnas necesarias en el DataFrame.  Asegúrate de tener 'Vendedores', 'Título', 'ID', 'permalink', 'Precio', 'Cantidad Disponible', 'Estado de Salud', 'OEM' y 'Visitas'.")
                return None

            # Filtrar por el OEM seleccionado
            df_competidores = df[df['OEM'] == oem_seleccionado]

            if df_competidores.empty:
                st.warning(f"No hay vendedores que vendan el OEM '{oem_seleccionado}'.")
                return None

            # Agrupar por vendedor y calcular promedios
            df_resumen = df_competidores.groupby('Vendedores').agg(
                {'Precio': 'mean',
                'Cantidad Disponible': 'mean',
                'Estado de Salud': 'mean',
                'Visitas':'sum', #Agregar las visitas
                'Título': 'first',  # Obtener el primer título (puedes ajustarlo si es necesario)
                'ID': 'first',  # Obtener el primer ID
                'permalink': 'first'        # Obtener el primer permalink
                }).reset_index()

            # Formatear el precio como moneda ($)
            df_resumen['Precio'] = df_resumen['Precio'].apply(lambda x: '${:.2f}'.format(x))

            df_resumen.rename(columns={'Precio': 'Precio Promedio',
                                    'Cantidad Disponible': 'Cantidad Disponible Promedio',
                                    'Estado de Salud': 'Health Promedio',
                                    'Visitas': 'Visitas Totales'}, inplace=True)

            return df_resumen

        df_competencia = crear_dataframe_competencia(df_oem, oem_seleccionado)

        if df_competencia is not None:
            st.dataframe(df_competencia)

            # Descarga CSV
            csv = df_competencia.to_csv(index=False)
            st.download_button(
                label="Descargar datos de la competencia como CSV",
                data=csv,
                file_name=f'competencia_{oem_seleccionado}.csv',
                mime='text/csv',
            )

 
        
        
        
        
        
        
        
        
        

    def estrategia_futura(df, fecha_inicio, fecha_fin):
        st.header("Estrategia Futura")

        # 1) Upload Nuevo Competidor Data
        carga_archivo_competidores = st.file_uploader("Cargue el archivo de competidores por favor (Excel)", type=['xlsx'])

        if carga_archivo_competidores is not None:
            try:
                df_competidores_nuevos = pd.read_excel(carga_archivo_competidores)
                st.write("Datos de nuevos competidores cargados:")
                st.dataframe(df_competidores_nuevos.head())

                # Diagnostic prints:
                st.write("Original DataFrame ID dtype:", df['ID'].dtype)
                st.write("Competitor DataFrame ID dtype:", df_competidores_nuevos['ID'].dtype)

                # **Key Conversion and Handling of Data Types**: Prioritize numeric handling
                try:
                    df['ID'] = pd.to_numeric(df['ID'], errors='raise') #Raise the error instead of coerse it
                    df_competidores_nuevos['ID'] = pd.to_numeric(df_competidores_nuevos['ID'], errors='raise')
                    df_competidores_nuevos['OEM']=df_competidores_nuevos['OEM'].astype(int)
                except ValueError as e: # Handle cases where some IDs cannot be converted to numbers
                    st.warning(f"Warning: Some IDs could not be converted to numbers: {e}.  Trying string conversion.")
                    df['ID'] = df['ID'].astype(str)
                    df_competidores_nuevos['ID'] = df_competidores_nuevos['ID'].astype(str)

                # Merge with Existing Data using concat:
                try:
                    df = pd.concat([df, df_competidores_nuevos], ignore_index=True)
                except Exception as e:
                    st.error(f"Error during concat: {e}")
                    return #Avoid the following code
                st.write("DataFrame after CONCAT")
                st.dataframe(df.head())


            except Exception as e:
                st.error(f"Error al cargar el archivo de competidores: {e}")
                return  # Exit if there's an error

        # 2) Selección del Vendedor
        lista_vendedores = df['Vendedores'].unique()
        vendedor_seleccionado = st.selectbox('Seleccione un Vendedor (para comparar con la competencia)', lista_vendedores)

        # 3) Filtro de Fecha (already applied to initial dataframe)
        df_filtrado = df[(df['Fecha'] >= fecha_inicio) & (df['Fecha'] <= fecha_fin)]

        # 4) Selección del OEM
        lista_oem = df_filtrado['OEM'].unique()
        oem_seleccionado = st.selectbox('Seleccione un OEM', lista_oem)

        # Filter for the selected OEM
        df_oem = df_filtrado[df_filtrado['OEM'] == oem_seleccionado]

        #  Functions from Competencia - ALL INTEGRATED into estrategia_futura:

        def variacion_precios_oem(df_oem, oem_seleccionado):
            """Shows the price variation ($) of the selected OEM. all vendors included."""
            if df_oem is None or 'Vendedores' not in df_oem.columns or 'Precio' not in df_oem.columns or 'OEM' not in df_oem.columns:
                st.warning("Faltan columns ('Vendedores', 'Precio', 'OEM').")
                return

            df_competidores = df_oem.groupby('Vendedores')['Precio'].mean().reset_index()
            if df_competidores.empty:
                st.warning(f"No hay vendedores del OEM '{oem_seleccionado}'.")
                return

            df_competidores['Precio'] = df_competidores['Precio'].apply(lambda x: '${:.2f}'.format(x))
            head = st.slider(f'Vendedores por Precio Promedio ({oem_seleccionado})', 1, len(df_competidores), min(10, len(df_competidores)), key = 'precios_fut')
            df_competidores = df_competidores.sort_values(by='Precio', ascending=False).head(head)
            fig = px.bar(df_competidores, x='Vendedores', y='Precio',
                        title=f'Top {head} Vendedores por Precio Promedio ({oem_seleccionado})',
                        labels={'Vendedores': 'Vendedor', 'Precio': 'Precio Promedio ($)'},
                        color='Precio', color_continuous_scale=px.colors.sequential.Plasma)
            fig.update_layout(xaxis_title='Vendedor', yaxis_title='Precio Promedio ($)', xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)

        def variacion_cantidad_disponible_oem(df_oem, oem_seleccionado):
            """Variation of quantity of the selected OEM, All vendors included."""
            if df_oem is None or 'Vendedores' not in df_oem.columns or 'Cantidad Disponible' not in df_oem.columns or 'OEM' not in df_oem.columns:
                st.warning("Error: Missing ('Vendedores', 'Cantidad Disponible', 'OEM').")
                return

            df_competidores = df_oem.groupby('Vendedores')['Cantidad Disponible'].mean().reset_index()
            if df_competidores.empty:
                st.warning(f"No hay vendedores que vendan OEM '{oem_seleccionado}'.")
                return

            head = st.slider(f'Competidores por Variación de Cantidad Disponible ({oem_seleccionado})', 1, len(df_competidores), min(10, len(df_competidores)),key ='can_fut' )
            df_competidores = df_competidores.sort_values(by='Cantidad Disponible', ascending=False).head(head)
            fig = px.bar(df_competidores, x='Vendedores', y='Cantidad Disponible',
                        title=f'Top {head} Competidores por Cantidad Disponible Promedio ({oem_seleccionado})',
                        labels={'Vendedores': 'Vendedor', 'Cantidad Disponible': 'Cantidad Disponible Promedio'},
                        color='Cantidad Disponible', color_continuous_scale=px.colors.sequential.Plasma)
            fig.update_layout(xaxis_title='Vendedor', yaxis_title='Cantidad Disponible Promedio', xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)

        def variacion_health_oem(df_oem, oem_seleccionado):
            """Health Variation of the selected OEM, All vendors included."""
            if df_oem is None or 'Vendedores' not in df_oem.columns or 'Estado de Salud' not in df_oem.columns or 'OEM' not in df_oem.columns:
                st.warning("Error: Missing columns ('Vendedores', 'Estado de Salud', 'OEM').")
                return

            df_competidores = df_oem.groupby('Vendedores')['Estado de Salud'].mean().reset_index()
            if df_competidores.empty:
                st.warning(f"No hay competidores para el OEM '{oem_seleccionado}'.")
                return

            head = st.slider(f'Competidores por Variación de Health ({oem_seleccionado})', 1, len(df_competidores), min(10, len(df_competidores)), key = 'salud_fut')
            df_competidores = df_competidores.sort_values(by='Estado de Salud', ascending=False).head(head)
            fig = px.bar(df_competidores, x='Vendedores', y='Estado de Salud',
                        title=f'Top {head} Competidores por Health Promedio ({oem_seleccionado})',
                        labels={'Vendedores': 'Vendedor', 'Estado de Salud': 'Health Promedio'},
                        color='Estado de Salud', color_continuous_scale=px.colors.sequential.Plasma)
            fig.update_layout(xaxis_title='Vendedor', yaxis_title='Health Promedio', xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)

        def comparacion_visitas_oem(df, oem_seleccionado):
            """Compariing the visit of the selecte OEM between ALL Vendors."""
            if df is None or 'Vendedores' not in df.columns or 'Visitas' not in df.columns or 'OEM' not in df.columns:
                st.warning("Error: Missing columns ('Vendedores', 'Visitas', 'OEM').")
                return

            df_competidores = df[df['OEM'] == oem_seleccionado].groupby('Vendedores')['Visitas'].sum().reset_index()
            if df_competidores.empty:
                st.warning(f"No hay vendedores para el OEM '{oem_seleccionado}'.")
                return

            head = st.slider(f'Competidores por Visitas ({oem_seleccionado})', 1, len(df_competidores), min(10, len(df_competidores)),key = 'visitas_fut')
            df_competidores = df_competidores.sort_values(by='Visitas', ascending=False).head(head)
            fig = px.bar(df_competidores, x='Vendedores', y='Visitas',
                        title=f'Top {head} Competidores por Visitas ({oem_seleccionado})',
                        labels={'Vendedores': 'Vendedor', 'Visitas': 'Visitas'},
                        color='Visitas', color_continuous_scale=px.colors.sequential.Plasma)
            fig.update_layout(xaxis_title='Vendedor', yaxis_title='Visitas', xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)


        # Call ALL the Analysis functions:

        st.subheader("Análisis de la Competencia por Precio")
        variacion_precios_oem(df_oem, oem_seleccionado)

        st.subheader("Análisis de la Competencia por Cantidad Disponible")
        variacion_cantidad_disponible_oem(df_oem, oem_seleccionado)

        st.subheader("Análisis de la Competencia por Estado de Salud")
        variacion_health_oem(df_oem, oem_seleccionado)

        st.subheader("Análisis de la Competencia por Visitas")
        comparacion_visitas_oem(df_filtrado, oem_seleccionado) # Use df_filtrado

        # 7) DataFrame Combinado
        st.subheader("DataFrame de Competencia (Incluyendo Nuevos Competidores)")

        def crear_dataframe_competencia(df, oem_seleccionado):
            """Creates a DataFrame with information of all vendors for the OEM selected."""
            if df is None or 'Vendedores' not in df.columns or 'Título' not in df.columns or 'ID' not in df.columns or 'permalink' not in df.columns or 'Precio' not in df.columns or 'Cantidad Disponible' not in df.columns or 'Estado de Salud' not in df.columns or 'OEM' not in df.columns or 'Visitas' not in df.columns:
                st.warning("Error: Missing columns. Chequea los datos y avisa a los admin.")
                return None

            df_competidores = df[df['OEM'] == oem_seleccionado]

            if df_competidores.empty:
                st.warning(f"No hay vendedores para el OEM '{oem_seleccionado}'.")
                return None

            # Force the type before aggregation:
            df_competidores['ID'] = df_competidores['ID'].astype(str)

            df_resumen = df_competidores.groupby('Vendedores').agg(
                {'Precio': 'mean',
                'Cantidad Disponible': 'mean',
                'Estado de Salud': 'mean',
                'Visitas':'sum', #Agregamos las visitas
                'Título': 'first',
                'ID': 'first', #Agregamos las Id
                'permalink': 'first' # Agregamos permaLink
                }).reset_index()
            df_resumen['ID'] = df_resumen['ID'].astype(str)


            # Formatear el precio como moneda ($)
            df_resumen['Precio'] = df_resumen['Precio'].apply(lambda x: '${:.2f}'.format(x))

            df_resumen.rename(columns={'Precio': 'Precio Promedio',
                                    'Cantidad Disponible': 'Cantidad Disponible Promedio',
                                    'Estado de Salud': 'Health Promedio',
                                    'Visitas': 'Visitas Totales'}, inplace=True)

            return df_resumen

        df_competencia = crear_dataframe_competencia(df_oem, oem_seleccionado)

        if df_competencia is not None:
            st.dataframe(df_competencia)

            # CSV Download:
            csv = df_competencia.to_csv(index=False)
            st.download_button(
                label="Descargar datos de la competencia (incluyendo nuevos) como CSV",
                data=csv,
                file_name=f'competencia_futura_{oem_seleccionado}.csv',
                mime='text/csv',
            )

    # Lógica principal basada en la selección del menú
    data = pagina_principal()  # Cargar los datos y guardarlos en la variable data

    # Filtro de fecha global
    if data is not None and 'Fecha' in data.columns:
        fecha_minima = data['Fecha'].min()
        fecha_maxima = data['Fecha'].max()
        fecha_inicio = st.date_input("Fecha de inicio", value=fecha_minima)
        fecha_fin = st.date_input("Fecha de fin", value=fecha_maxima)

        fecha_inicio = pd.to_datetime(fecha_inicio)
        fecha_fin = pd.to_datetime(fecha_fin)
    else:
        fecha_inicio = None
        fecha_fin = None
        if data is None:
            st.warning("Por favor, cargue los datos en la página principal.")
        else:
            st.warning("La columna 'Fecha' no se encuentra en los datos cargados.")

    # Definir df_filtrado fuera de los bloques if/elif
    df_filtrado = pd.DataFrame() # DataFrame vacio como valor por defecto

    if seleccion == 'Página Principal':
        pass  # La página principal ya se ha mostrado, no hay nada más que hacer aquí.
    elif seleccion == 'Mercado':
        if data is not None and fecha_inicio is not None and fecha_fin is not None:  # Verificar si los datos se cargaron correctamente y las fechas están definidas
            df_filtrado, df_descarga = mercado(data, fecha_inicio, fecha_fin)
        else:
             st.warning("Por favor, cargue los datos en la página principal y asegúrese de que la columna 'Fecha' esté presente.")
    elif seleccion == 'Estrategia Actual':
        if data is not None and fecha_inicio is not None and fecha_fin is not None: # Verifico que data y las fechas existan
            df_filtrado = data[(data['Fecha'] >= fecha_inicio) & (data['Fecha'] <= fecha_fin)] # Aplico filtro de fechas
            if not df_filtrado.empty:  # Solo llama a estrategia_actual si df_filtrado no está vacío
                estrategia_actual(df_filtrado)  # Pasamos df_filtrado como argumento
            else:
                st.warning("No hay datos en el rango de fechas seleccionado.")
        else:
            st.warning("Por favor, cargue los datos en la página principal y asegúrese de que la columna 'Fecha' esté presente.")
    elif seleccion == 'Competencia':
        if data is not None and fecha_inicio is not None and fecha_fin is not None:
            competencia(data, fecha_inicio, fecha_fin)  # Pasar df, fecha_inicio y fecha_fin
        else:
            st.warning("Por favor, cargue los datos en la página principal y seleccione un rango de fechas.")
    elif seleccion == 'Estrategia Futura':
        if data is not None and fecha_inicio is not None and fecha_fin is not None:
            estrategia_futura(data, fecha_inicio, fecha_fin)
        else:
            st.warning("Por favor, cargue los datos en la página principal y seleccione un rango de fechas.")

if __name__ == '__main__':
    main()
