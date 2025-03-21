import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO
import base64
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Conv2D, Flatten, MaxPooling2D, Reshape, LSTM, SimpleRNN, Embedding
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.preprocessing.sequence import pad_sequences
from PIL import Image
import io
import json
from urllib.request import urlopen
# Add this import
from tensorflow.keras.preprocessing.text import Tokenizer
import matplotlib.pyplot as plt
from collections import Counter
from sklearn.neighbors import KNeighborsClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Configuración de la página
st.set_page_config(page_title='ANALIZADOR DE MERCADO PARA MERCADO LIBRE', layout='wide')

# Aumentar el tamaño máximo del archivo cargado a 1000MB (en bytes)
MAX_FILE_SIZE = 1000 * 1024 * 1024  # 1000MB. Streamlit cloud tiene un limite de 200mb

# Function to load image from URL
def load_image_from_url(url):
    try:
        image = Image.open(urlopen(url))
        return image
    except Exception as e:
        st.error(f"Error loading image from {url}: {e}")
        return None

# Function to display image with title
def display_image_with_title(image_url, title):
    image = load_image_from_url(image_url)
    if image:
        st.image(image, caption=title, use_column_width=True)

def main():
    # Titulo
    st.title('ANALIZADOR DE MERCADO PARA MERCADO LIBRE')
    # Barra lateral
    menu = ['Página Principal', 'Mercado', 'Estrategia Actual', 'Competencia', 'Estrategia Futura', 'Redes Neuronales']
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


    def redes_neuronales(df):
        st.header("Análisis de Mercado con Machine Learning")

        # --- Model Selection ---
        st.header("Selección del Modelo")
        model_type = st.selectbox("Seleccione el tipo de modelo:", ["MLP", "KMeans"])

        # --- Common Data Preparation ---
        # Check for necessary columns
        required_cols = ['Visitas', 'Estado de Salud', 'Cantidad Disponible', 'Categoría', 'Título', 'Precio']
        for col in required_cols:
            if col not in df.columns:
                st.warning(f"La columna '{col}' no está presente en los datos.")
                return

        # Impute missing values with the mean
        feature_cols = ['Visitas', 'Estado de Salud', 'Cantidad Disponible']
        for col in feature_cols:
            df[col] = df[col].fillna(df[col].mean())

        # Scale the features
        X = df[feature_cols].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # --- MLP Model ---
        if model_type == "MLP":
            st.subheader("Red Neuronal Multicapa (MLP)")

            # Encode the 'Categoría' column
            label_encoder = LabelEncoder()
            df['category_encoded'] = label_encoder.fit_transform(df['Categoría'])
            num_classes = len(label_encoder.classes_)
            y = to_categorical(df['category_encoded'], num_classes=num_classes)

            # Split the data
            X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

            # Define the MLP model
            mlp_model = Sequential([
                Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
                Dense(64, activation='relu'),
                Dense(num_classes, activation='softmax')
            ])
            mlp_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

            # Train the MLP model
            epochs = st.slider("Número de épocas (MLP)", 1, 20, 5, key="mlp_epochs")
            batch_size = st.slider("Tamaño del lote (MLP)", 16, 128, 32, key="mlp_batch_size")
            mlp_model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(X_test, y_test))

            # Evaluate the MLP model
            loss, accuracy = mlp_model.evaluate(X_test, y_test, verbose=0)
            st.write(f"Pérdida: {loss:.4f}")
            st.write(f"Precisión: {accuracy:.4f}")

            # Make predictions
            y_prob = mlp_model.predict(X_test)
            y_pred = np.argmax(y_prob, axis=1)
            predicted_categories = label_encoder.inverse_transform(y_pred)
            real_categories = label_encoder.inverse_transform(np.argmax(y_test, axis=1))

            # Create results DataFrame
            results_df = pd.DataFrame({
                'Categoría Real': real_categories,
                'Categoría Predicha': predicted_categories,
                'Confianza': np.max(y_prob, axis=1)
            })
            st.write("#### Resultados de la Predicción")
            st.dataframe(results_df.head())

            # Scatter plot
            fig = px.scatter(results_df, x="Categoría Real", y="Categoría Predicha",
                            color="Confianza", title="Predicciones del Modelo MLP con Confianza",
                            labels={"Categoría Real": "Categoría Real",
                                    "Categoría Predicha": "Categoría Predicha",
                                    "Confianza": "Confianza"})
            st.plotly_chart(fig)



        # --- KMeans Model ---
        elif model_type == "KMeans":
            st.subheader("Clustering con K-Means")

            # Determine optimal number of clusters
            inertia = []
            silhouette_coefficients = []
            K = range(2, 11)

            for k in K:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                kmeans.fit(X_scaled)
                inertia.append(kmeans.inertia_)
                score = silhouette_score(X_scaled, kmeans.labels_)
                silhouette_coefficients.append(score)

            # Plot inertia (Elbow Method)
            st.write("#### Elbow Method for optimal K")
            fig, ax = plt.subplots()
            ax.plot(K, inertia, marker='o')
            ax.set_xlabel('Number of clusters (K)')
            ax.set_ylabel('Inertia')
            ax.set_title('Elbow Method for optimal K')
            st.pyplot(fig)

            # Plot silhouette scores
            st.write("#### Silhouette Scores for optimal K")
            fig, ax = plt.subplots()
            ax.plot(K, silhouette_coefficients, marker='o')
            ax.set_xlabel('Number of clusters (K)')
            ax.set_ylabel('Silhouette Score')
            ax.set_title('Silhouette Score for optimal K')
            st.pyplot(fig)

            # K-Means Clustering
            n_clusters = st.slider("Number of clusters (K)", 2, 10, 3)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X_scaled)
            df['Cluster'] = clusters

            # Analyze Clusters
            st.write("### Analyze Clusters")
            cluster_summary = df.groupby('Cluster')[feature_cols].mean()
            st.dataframe(cluster_summary)

            # Display Titles in each cluster
            st.write("### Títulos por Cluster")
            for i in range(n_clusters):
                st.write(f"#### Cluster {i}:")
                cluster_titles = df[df['Cluster'] == i]['Título'].unique()
                st.write(cluster_titles) # Show titles

            # Create Scatter Plots with Cluster Coloring
            st.write("### Gráficos de Dispersión por Cluster")

            # Visitas vs. Precio
            fig_visitas_precio = px.scatter(df, x='Precio', y='Visitas', color='Cluster',
                                            title='Visitas vs. Precio por Cluster',
                                            labels={'Precio': 'Precio', 'Visitas': 'Visitas', 'Cluster': 'Cluster'})
            st.plotly_chart(fig_visitas_precio)

            # Visitas vs. Cantidad Disponible
            fig_visitas_cantidad = px.scatter(df, x='Cantidad Disponible', y='Visitas', color='Cluster',
                                                title='Visitas vs. Cantidad Disponible por Cluster',
                                                labels={'Cantidad Disponible': 'Cantidad Disponible', 'Visitas': 'Visitas', 'Cluster': 'Cluster'})
            st.plotly_chart(fig_visitas_cantidad)

            # Visitas vs. Estado de Salud
            fig_visitas_salud = px.scatter(df, x='Estado de Salud', y='Visitas', color='Cluster',
                                            title='Visitas vs. Estado de Salud por Cluster',
                                            labels={'Estado de Salud': 'Estado de Salud', 'Visitas': 'Visitas', 'Cluster': 'Cluster'})
            st.plotly_chart(fig_visitas_salud)

            # --- STRATEGY ---
            st.write("### STRATEGY")
            for i in range(n_clusters):
                st.write(f"##### Cluster {i}:")
                cluster_description = f"Productos con "
                for col in feature_cols:
                    mean_value = cluster_summary.loc[i, col]
                    cluster_description += f"{col}={mean_value:.2f}, "
                st.write(cluster_description)
                st.write("###### Estrategia: [Definir una estrategia específica para este cluster]")


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

        # --- Descargar DataFrame de Resultados a CSV ---
        csv_resultados = df_resultados.to_csv(index=False)
        b64_resultados = base64.b64encode(csv_resultados.encode()).decode()
        href_resultados = f'<a href="data:file/csv;base64,{b64_resultados}" download="resultados.csv">Descargar DataFrame de Resultados como CSV</a>'
        st.markdown(href_resultados, unsafe_allow_html=True)

        # --- DataFrame Combinado (Nueva Sección) ---
        st.subheader("DataFrame Combinado")

        def crear_dataframe_combinado(df):
            """Crea un DataFrame combinado con información relevante."""
            if df is None or 'Categoría' not in df.columns or 'Título' not in df.columns or 'OEM' not in df.columns or 'Visitas' not in df.columns or 'Cantidad Disponible' not in df.columns or 'Estado de Salud' not in df.columns or 'Vendedores' not in df.columns or 'permalink' not in df.columns or 'ID' not in df.columns:
                st.warning("Error: Faltan columnas necesarias en el DataFrame.  Asegúrate de tener 'Categoría', 'Título', 'OEM', 'Visitas', 'Cantidad Disponible', 'Estado de Salud', 'Vendedores', 'permalink' y 'ID'.")
                return None

            # Calcular la cantidad de publicaciones por categoría
            publicaciones_por_categoria = df.groupby('Categoría').size().reset_index(name='Cantidad Publicaciones')
            df_combinado = pd.merge(df, publicaciones_por_categoria, on='Categoría', how='left')

            # Agrupar por 'OEM' y calcular la suma de visitas
            oem_visitas = df.groupby('OEM')['Visitas'].sum().reset_index(name='Visitas por OEM')
            df_combinado = pd.merge(df_combinado, oem_visitas, on='OEM', how='left')

            # Calcular eficiencia del vendedor (promedio, ya que no hay selección de vendedor)
            total_visitas = df['Visitas'].sum()
            total_titulos = df['Título'].nunique()
            eficiencia_vendedor = total_visitas / total_titulos if total_titulos > 0 else 0
            df_combinado['Eficiencia Vendedor'] = eficiencia_vendedor  # Agregar al DataFrame

            # Eliminar duplicados para que cada fila represente una combinación única
            df_resumen = df_combinado[['Categoría', 'Título', 'OEM', 'Visitas', 'Cantidad Disponible', 'Estado de Salud', 'Cantidad Publicaciones', 'Visitas por OEM', 'Eficiencia Vendedor', 'permalink', 'ID']].drop_duplicates()

            # Calcular la eficiencia
            visitas_totales = df.groupby('OEM')['Visitas'].sum() # Visitas totales por OEM de todos los vendedores
            eficiencia_oem = (df_combinado['Visitas por OEM'] / visitas_totales[df_combinado['OEM']].values).fillna(0)  # Eficiencia para cada fila

            df_resumen['Eficiencia OEM'] = eficiencia_oem # Agrega la eficiencia calculada

            # Calcular Health promedio por categoria
            health_medio_por_categoria = df.groupby('Categoría')['Estado de Salud'].mean().reset_index(name = "Health Medio Categoria")
            df_resumen = pd.merge(df_resumen, health_medio_por_categoria, on='Categoría', how='left')
            df_resumen = df_resumen.fillna(0)

            return df_resumen

        df_combinado = crear_dataframe_combinado(df_filtrado)

        if df_combinado is not None:
            st.dataframe(df_combinado)
            # Opción de descarga (csv)
            csv = df_combinado.to_csv(index=False)
            st.download_button(
                label="Descargar datos como CSV",
                data=csv,
                file_name='data_combinada.csv',
                mime='text/csv',
            )

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
            # Opción de descarga (csv)
            csv = df_combinado.to_csv(index=False)
            st.download_button(
                label="Descargar datos como CSV",
                data=csv,
                file_name='data_combinada.csv',
                mime='text/csv',
            )

            return df_combinado  # Retornar ambos DataFrames


  
    def competencia(df, fecha_inicio, fecha_fin):
            st.header("Análisis de la Competencia")

            # Filtro de Fecha
            df_filtrado = df[(df['Fecha'] >= fecha_inicio) & (df['Fecha'] <= fecha_fin)]

            lista_vendedores = df['Vendedores'].unique()
            vendedor_seleccionado = st.selectbox('Seleccione un Vendedor (para comparar con la competencia)', lista_vendedores)


            # Selección del OEM
            lista_oem = df_filtrado['OEM'].unique()
            oem_seleccionado = st.selectbox('Seleccione un OEM', lista_oem)

            # Filtrar por OEM seleccionado
            df_oem = df_filtrado[df_filtrado['OEM'] == oem_seleccionado]

            # Funciones de Variación
            def variacion_precios_oem(df_oem, oem_seleccionado):
                """Muestra la variación de precios del OEM seleccionado entre todos los ."""
                if df_oem is None or 'Vendedores' not in df_oem.columns or 'Precio' not in df_oem.columns or 'OEM' not in df_oem.columns:
                    st.warning("Error: Faltan columnas necesarias en el DataFrame ('Vendedores', 'Precio', 'OEM').")
                    return

                # Calcular el precio promedio por
                df_competidores = df_oem.groupby('Vendedores')['Precio'].mean().reset_index()

                if df_competidores.empty:
                    st.warning(f"No hay  que vendan el OEM '{oem_seleccionado}'.")
                    return

                # Convertir la columna Precio a float antes de aplicar el formato
                df_competidores['Precio'] = df_competidores['Precio'].astype(float)

                max_vendedores = len(df_competidores)

                if max_vendedores == 1:
                    st.warning("Solo hay un  disponible, mostrando el precio sin comparación.")
                    df_competidores['Precio'] = df_competidores['Precio'].apply(lambda x: '${:.2f}'.format(x))
                    st.write(df_competidores)
                    return  # Terminar la función si solo hay un

                # Slider para el Top N
                head = st.slider(
                    f'Top  por Variación de Precio ({oem_seleccionado})',
                    1, max_vendedores, min(10, max_vendedores), key='precio'
                )

                # Ordenar por precio y seleccionar el Top N
                df_competidores = df_competidores.sort_values(by='Precio', ascending=False).head(head)

                # Aplicar formato a Precio después de la selección
                df_competidores['Precio'] = df_competidores['Precio'].apply(lambda x: '${:.2f}'.format(x))

                # Crear gráfico de barras
                fig = px.bar(df_competidores, x='Vendedores', y='Precio',
                            title=f'Top {head}  por Precio Promedio ({oem_seleccionado})',
                            labels={'Vendedores': 'Vendedor', 'Precio': 'Precio Promedio ($)'},
                            color='Precio', color_continuous_scale=px.colors.sequential.Plasma)
                fig.update_layout(xaxis_title='Vendedor', yaxis_title='Precio Promedio ($)',
                                xaxis={'categoryorder': 'total descending'})
                st.plotly_chart(fig)

            def variacion_cantidad_disponible_oem(df_oem, oem_seleccionado):
                """Muestra la variación de cantidad disponible del OEM seleccionado entre todos los ."""
                if df_oem is None or 'Vendedores' not in df_oem.columns or 'Cantidad Disponible' not in df_oem.columns or 'OEM' not in df_oem.columns:
                    st.warning("Error: Faltan columnas necesarias en el DataFrame ('Vendedores', 'Cantidad Disponible', 'OEM').")
                    return

                # Calcular la cantidad disponible promedio por
                df_competidores = df_oem.groupby('Vendedores')['Cantidad Disponible'].mean().reset_index()

                if df_competidores.empty:
                    st.warning(f"No hay  que vendan el OEM '{oem_seleccionado}'.")
                    return

                # Slider para el Top N
                head = st.slider(f'Top  por Variación de Cantidad Disponible ({oem_seleccionado})', 1,
                                len(df_competidores), min(10, len(df_competidores)), key='cantidad')

                # Ordenar por cantidad disponible y seleccionar el Top N
                df_competidores = df_competidores.sort_values(by='Cantidad Disponible', ascending=False).head(head)

                # Crear gráfico de barras
                fig = px.bar(df_competidores, x='Vendedores', y='Cantidad Disponible',
                            title=f'Top {head}  por Cantidad Disponible Promedio ({oem_seleccionado})',
                            labels={'Vendedores': 'Vendedor', 'Cantidad Disponible': 'Cantidad Disponible Promedio'},
                            color='Cantidad Disponible', color_continuous_scale=px.colors.sequential.Plasma)
                fig.update_layout(xaxis_title='Vendedor', yaxis_title='Cantidad Disponible Promedio',
                                xaxis={'categoryorder': 'total descending'})
                st.plotly_chart(fig)

            def variacion_health_oem(df_oem, oem_seleccionado):
                """Muestra la variación de health del OEM seleccionado entre todos los ."""
                if df_oem is None or 'Vendedores' not in df_oem.columns or 'Estado de Salud' not in df_oem.columns or 'OEM' not in df_oem.columns:
                    st.warning("Error: Faltan columnas necesarias en el DataFrame ('Vendedores', 'Estado de Salud', 'OEM').")
                    return

                # Calcular el health promedio por
                df_competidores = df_oem.groupby('Vendedores')['Estado de Salud'].mean().reset_index()

                if df_competidores.empty:
                    st.warning(f"No hay  que vendan el OEM '{oem_seleccionado}'.")
                    return

                # Slider para el Top N
                head = st.slider(f'Top  por Variación de Health ({oem_seleccionado})', 1, len(df_competidores),
                                min(10, len(df_competidores)), key='health')

                # Ordenar por health y seleccionar el Top N
                df_competidores = df_competidores.sort_values(by='Estado de Salud', ascending=False).head(head)

                # Crear gráfico de barras
                fig = px.bar(df_competidores, x='Vendedores', y='Estado de Salud',
                            title=f'Top {head}  por Health Promedio ({oem_seleccionado})',
                            labels={'Vendedores': 'Vendedor', 'Estado de Salud': 'Health Promedio'},
                            color='Estado de Salud', color_continuous_scale=px.colors.sequential.Plasma)
                fig.update_layout(xaxis_title='Vendedor', yaxis_title='Health Promedio',
                                xaxis={'categoryorder': 'total descending'})
                st.plotly_chart(fig)

            def comparacion_visitas_oem(df, oem_seleccionado):
                """Compara las visitas por OEM entre todos los ."""
                if df is None or 'Vendedores' not in df.columns or 'Visitas' not in df.columns or 'OEM' not in df.columns:
                    st.warning("Error: Faltan columnas necesarias en el DataFrame ('Vendedores', 'Visitas', 'OEM').")
                    return

                # Visitas de todos los  para el OEM seleccionado
                df_competidores = df[df['OEM'] == oem_seleccionado].groupby('Vendedores')['Visitas'].sum().reset_index()

                if df_competidores.empty:
                    st.warning(f"No hay  que vendan el OEM '{oem_seleccionado}'.")
                    return

                # Slider para el Top N
                head = st.slider(f'Top  por Visitas ({oem_seleccionado})', 1, len(df_competidores),
                                min(10, len(df_competidores)), key='visitas')

                # Ordenar por visitas y seleccionar el Top N
                df_competidores = df_competidores.sort_values(by='Visitas', ascending=False).head(head)

                # Crear gráfico de barras
                fig = px.bar(df_competidores, x='Vendedores', y='Visitas',
                            title=f'Top {head}  por Visitas ({oem_seleccionado})',
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
                """Crea un DataFrame con información de todos los  para el OEM seleccionado."""
                # Reemplazar 'item_id' por 'ID' y 'URL' por 'permalink'
                if df is None or 'Vendedores' not in df.columns or 'Título' not in df.columns or 'ID' not in df.columns or 'permalink' not in df.columns or 'Precio' not in df.columns or 'Cantidad Disponible' not in df.columns or 'Estado de Salud' not in df.columns or 'OEM' not in df.columns or 'Visitas' not in df.columns or 'warranty' not in df.columns or 'tags' not in df.columns or 'shipping' not in df.columns or 'Fecha de Última Actualización' not in df.columns:
                    st.warning(
                        "Error: Faltan columnas necesarias en el DataFrame. Asegúrate de tener 'Vendedores', 'Título', 'ID', 'permalink', 'Precio', 'Cantidad Disponible', 'Estado de Salud', 'OEM', 'Visitas', 'warranty', 'tags', 'shipping' y 'Fecha de Última Actualización'.")
                    return None

                # Filtrar por el OEM seleccionado
                df_competidores = df[df['OEM'] == oem_seleccionado]

                if df_competidores.empty:
                    st.warning(f"No hay  que vendan el OEM '{oem_seleccionado}'.")
                    return None

                # Agrupar por  y calcular promedios
                df_resumen = df_competidores.groupby('Vendedores').agg(
                    {'Precio': 'mean',
                    'Cantidad Disponible': 'mean',
                    'Estado de Salud': 'mean',
                    'Visitas': 'sum',  # Agregar las visitas
                    'Título': 'first',  # Obtener el primer título (puedes ajustarlo si es necesario)
                    'ID': 'first',  # Obtener el primer ID
                    'permalink': 'first',  # Obtener el primer permalink
                    'Fecha de Última Actualización': 'first'
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

                # Análisis Adicional (Gráficos)
            st.subheader("Análisis Detallado de Características")

            # 1) Gráfico de Título vs. Fecha de Última Actualización
            st.subheader("Fecha de Última Actualización")

            # Verificar si la columna 'Fecha de Última Actualización' existe
            if 'Fecha de Última Actualización' in df_oem.columns:
                # Convertir la columna a tipo datetime si no lo es
                if not pd.api.types.is_datetime64_any_dtype(df_oem['Fecha de Última Actualización']):
                    df_oem['Fecha de Última Actualización'] = pd.to_datetime(df_oem['Fecha de Última Actualización'])

                # Extraer la fecha
                df_oem['Fecha de Última Actualización'] = df_oem['Fecha de Última Actualización'].dt.date

                # Contar la frecuencia de cada fecha
                fecha_counts = df_oem['Fecha de Última Actualización'].value_counts().reset_index()
                fecha_counts.columns = ['Fecha', 'Cantidad']

                # Crear el gráfico de torta
                fig_fecha_actualizacion = px.pie(fecha_counts, values='Cantidad', names='Fecha',
                                                title='Distribución de Fechas de Última Actualización',
                                                labels={'Fecha': 'Fecha de Última Actualización', 'Cantidad': 'Cantidad'},
                                                color_discrete_sequence=px.colors.sequential.Plasma)
                st.plotly_chart(fig_fecha_actualizacion)
            else:
                st.warning("La columna 'Fecha de Última Actualización' no existe en el DataFrame.")

            # 2) Gráfico de Warranty por Título
            st.subheader("Garantía por Título")
            warranty_counts = df_oem.groupby('Título')['warranty'].value_counts().unstack().fillna(0)
            fig_warranty = px.bar(warranty_counts, x=warranty_counts.index, y=warranty_counts.columns,
                                title='Distribución de Garantía por Título',
                                labels={'value': 'Cantidad', 'Título': 'Título del Producto'},
                                color_continuous_scale=px.colors.sequential.Plasma)
            st.plotly_chart(fig_warranty)

            # 3) Gráfico de Tags (catalog_listing y/o catalog_forewarning) por Título
            st.subheader("Catálogo por Título")

            def esta_en_catalogo(tags_list):
                if isinstance(tags_list, str):
                    tags_list = eval(tags_list)  # Convert string representation to list
                
                for tag in tags_list:
                    if 'catalog_listing_eligible' in tag or 'catalog_forewarning' in tag or 'catalog_boost' in tag:
                        return 'Sí'
                return 'No'

            df_oem['en_catalogo'] = df_oem['tags'].apply(esta_en_catalogo)

            # Contar cuántos títulos están en el catálogo y cuántos no
            catalogo_counts = df_oem['en_catalogo'].value_counts().reset_index()
            catalogo_counts.columns = ['En Catálogo', 'Cantidad']

            # Crear un gráfico de torta
            fig_catalogo = px.pie(catalogo_counts, values='Cantidad', names='En Catálogo',
                                    title='Distribución de Productos en Catálogo',
                                    color_discrete_sequence=px.colors.sequential.Plasma)
            st.plotly_chart(fig_catalogo)


            # 4) Gráfico detallado de Cuota Simple
            st.subheader("Tipos de Cuota Simple")

            def extract_cuota_simple_type(tags_list):
                if isinstance(tags_list, str):
                    tags_list = eval(tags_list)  # Convert string representation to list
                
                for tag in tags_list:
                    if 'cuota-simple-paid-by-buyer' in tag:
                        return 'cuota-simple-paid-by-buyer'
                    elif 'cuota-simple-3' in tag:
                        return 'cuota-simple-3'
                    elif 'cuota-simple-6' in tag:
                        return 'cuota-simple-6'
                    elif 'cuota-simple-9' in tag:
                        return 'cuota-simple-9'
                    elif 'cuota-simple-12' in tag:
                        return 'cuota-simple-12'
                    elif 'cuota-simple-18' in tag:
                        return 'cuota-simple-18'
                return 'Ninguna'  # Si no se encuentra ninguna cuota simple

            df_oem['tipo_cuota_simple'] = df_oem['tags'].apply(extract_cuota_simple_type)

            # Contar la frecuencia de cada tipo de cuota simple
            tipo_cuota_simple_counts = df_oem['tipo_cuota_simple'].value_counts().reset_index()
            tipo_cuota_simple_counts.columns = ['Tipo de Cuota Simple', 'Cantidad']

            # Crear un gráfico de torta
            fig_tipos_cuota_simple = px.pie(tipo_cuota_simple_counts, values='Cantidad', names='Tipo de Cuota Simple',
                                                title='Distribución de Tipos de Cuota Simple',
                                                color_discrete_sequence=px.colors.sequential.Plasma)
            st.plotly_chart(fig_tipos_cuota_simple)

            # 6) Gráfico de Free Shipping por Título
            st.subheader("Free Shipping por Título")

            def extract_free_shipping(shipping_info):
                if isinstance(shipping_info, str):
                    shipping_info = eval(shipping_info)
                return shipping_info.get('free_shipping', False)

            df_oem['free_shipping'] = df_oem['shipping'].apply(extract_free_shipping)
            free_shipping_counts = df_oem.groupby('Título')['free_shipping'].value_counts().unstack().fillna(0)
            fig_free_shipping = px.bar(free_shipping_counts, x=free_shipping_counts.index,
                                        y=free_shipping_counts.columns,
                                        title='Distribución de Free Shipping por Título',
                                        labels={'value': 'Cantidad', 'Título': 'Título del Producto'},
                                        color_continuous_scale=px.colors.sequential.Plasma)
            st.plotly_chart(fig_free_shipping)
        
    def estrategia_futura(df, fecha_inicio, fecha_fin):
        st.header("Estrategia Futura")

        # 1) Upload Nuevo Competidor Data
        carga_archivo_competidores = st.file_uploader("Cargue el archivo de competidores por favor (Excel)",
                                                    type=['xlsx'])

        if carga_archivo_competidores is not None:
            try:
                df_competidores_nuevos = pd.read_excel(carga_archivo_competidores)
                df_competidores_nuevos['OEM'] = df_competidores_nuevos['OEM'].astype(str)
                st.write("Datos de nuevos competidores cargados:")
                st.dataframe(df_competidores_nuevos.head())

                # Diagnostic prints:
                st.write("Original DataFrame ID dtype:", df['ID'].dtype)
                st.write("Competitor DataFrame ID dtype:", df_competidores_nuevos['ID'].dtype)

                # **Key Conversion and Handling of Data Types**: Prioritize numeric handling
                try:
                    df['ID'] = pd.to_numeric(df['ID'], errors='raise')  # Raise the error instead of coerse it
                    df_competidores_nuevos['ID'] = pd.to_numeric(df_competidores_nuevos['ID'],
                                                                errors='raise')
                except ValueError as e:  # Handle cases where some IDs cannot be converted to numbers
                    st.warning(f"Warning: Some IDs could not be converted to numbers: {e}. Trying string conversion.")
                    df['ID'] = df['ID'].astype(str)
                    df_competidores_nuevos['ID'] = df_competidores_nuevos['ID'].astype(str)

                # Merge with Existing Data using concat:
                try:
                    df = pd.concat([df, df_competidores_nuevos], ignore_index=True)
                except Exception as e:
                    st.error(f"Error during concat: {e}")
                    return  # Avoid the following code
                st.write("DataFrame after CONCAT")
                st.dataframe(df.head())


            except Exception as e:
                st.error(f"Error al cargar el archivo de competidores: {e}")
                return  # Exit if there's an error

        # 2) Selección del Vendedor
        lista_vendedores = df['Vendedores'].unique()
        vendedor_seleccionado = st.selectbox('Seleccione un Vendedor (para comparar con la competencia)',
                                            lista_vendedores)

        # 3) Filtro de Fecha (already applied to initial dataframe)
        df_filtrado = df[(df['Fecha'] >= fecha_inicio) & (df['Fecha'] <= fecha_fin)]

        # 4) Selección del OEM
        lista_oem = df_filtrado['OEM'].unique()
        oem_seleccionado = st.selectbox('Seleccione un OEM', lista_oem)

        # Filter for the selected OEM
        df_oem = df_filtrado[df_filtrado['OEM'] == oem_seleccionado]
        # Add a guard to check if df_oem is defined and not empty before running the analysis
        if not df_oem.empty:
            def variacion_precios_oem(df_oem, oem_seleccionado):
                """Shows the price variation ($) of the selected OEM."""
                if df_oem is None or 'Vendedores' not in df_oem.columns or 'Precio' not in df_oem.columns or 'OEM' not in df_oem.columns:
                    st.warning("Faltan columns ('Vendedores', 'Precio', 'OEM').")
                    return

                df_competidores = df_oem.groupby('Vendedores')['Precio'].mean().reset_index()
                if df_competidores.empty:
                    st.warning(f"No hay vendedores del OEM '{oem_seleccionado}'.")
                    return

                df_competidores['Precio'] = df_competidores['Precio'].apply(lambda x: '${:.2f}'.format(x))
                head = st.slider(f'Vendedores por Precio Promedio ({oem_seleccionado})', 1, len(df_competidores),
                                min(10, len(df_competidores)), key='precios_fut')
                df_competidores = df_competidores.sort_values(by='Precio', ascending=False).head(head)
                fig = px.bar(df_competidores, x='Vendedores', y='Precio',
                            title=f'Top {head} Vendedores por Precio Promedio ({oem_seleccionado})',
                            labels={'Vendedores': 'Vendedor', 'Precio': 'Precio Promedio ($)'},
                            color='Precio', color_continuous_scale=px.colors.sequential.Plasma)
                fig.update_layout(xaxis_title='Vendedor', yaxis_title='Precio Promedio ($)',
                                xaxis={'categoryorder': 'total descending'})
                st.plotly_chart(fig)

            def variacion_cantidad_disponible_oem(df_oem, oem_seleccionado):
                """Shows the quantity variation of the selected OEM."""
                if df_oem is None or 'Vendedores' not in df_oem.columns or 'Cantidad Disponible' not in df_oem.columns or 'OEM' not in df_oem.columns:
                    st.warning("Error: Missing ('Vendedores', 'Cantidad Disponible', 'OEM').")
                return
            
            df_competidores = df_oem.groupby('Vendedores')['Cantidad Disponible'].mean().reset_index()
            if df_competidores.empty:
                st.warning(f"No hay vendedores que vendan OEM '{oem_seleccionado}'.")
                return

            head = st.slider(f'Competidores por Variación de Cantidad Disponible ({oem_seleccionado})', 1,
                            len(df_competidores), min(10, len(df_competidores)), key='can_fut')
            df_competidores = df_competidores.sort_values(by='Cantidad Disponible', ascending=False).head(head)
            fig = px.bar(df_competidores, x='Vendedores', y='Cantidad Disponible',
                        title=f'Top {head} Competidores por Cantidad Disponible Promedio ({oem_seleccionado})',
                        labels={'Vendedores': 'Vendedor', 'Cantidad Disponible': 'Cantidad Disponible Promedio'},
                        color='Cantidad Disponible', color_continuous_scale=px.colors.sequential.Plasma)
            fig.update_layout(xaxis_title='Vendedor', yaxis_title='Cantidad Disponible Promedio',
                            xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)

            def variacion_health_oem(df_oem, oem_seleccionado):
                """Shows the Health variation of the selected OEM."""
                if df_oem is None or 'Vendedores' not in df_oem.columns or 'Estado de Salud' not in df_oem.columns or 'OEM' not in df_oem.columns:
                    st.warning("Error: Missing columns ('Vendedores', 'Estado de Salud', 'OEM').")
                    return

                df_competidores = df_oem.groupby('Vendedores')['Estado de Salud'].mean().reset_index()
                if df_competidores.empty:
                    st.warning(f"No hay competidores para el OEM '{oem_seleccionado}'.")
                    return

                head = st.slider(f'Competidores por Variación de Health ({oem_seleccionado})', 1, len(df_competidores),
                                min(10, len(df_competidores)), key='salud_fut')
                df_competidores = df_competidores.sort_values(by='Estado de Salud', ascending=False).head(head)
                fig = px.bar(df_competidores, x='Vendedores', y='Estado de Salud',
                            title=f'Top {head} Competidores por Health Promedio ({oem_seleccionado})',
                            labels={'Vendedores': 'Vendedor', 'Estado de Salud': 'Health Promedio'},
                            color='Estado de Salud', color_continuous_scale=px.colors.sequential.Plasma)
                fig.update_layout(xaxis_title='Vendedor', yaxis_title='Health Promedio',
                                xaxis={'categoryorder': 'total descending'})
                st.plotly_chart(fig)

            def comparacion_visitas_oem(df, oem_seleccionado):
                """Comparing the visits of the selected OEM."""
                if df is None or 'Vendedores' not in df.columns or 'Visitas' not in df.columns or 'OEM' not in df.columns:
                    st.warning("Error: Missing columns ('Vendedores', 'Visitas', 'OEM').")
                    return

                df_competidores = df[df['OEM'] == oem_seleccionado].groupby('Vendedores')['Visitas'].sum().reset_index()
                if df_competidores.empty:
                    st.warning(f"No hay vendedores para el OEM '{oem_seleccionado}'.")
                    return

                head = st.slider(f'Competidores por Visitas ({oem_seleccionado})', 1, len(df_competidores),
                                min(10, len(df_competidores)), key='visitas_fut')
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
            comparacion_visitas_oem(df_filtrado, oem_seleccionado)

            # 7) DataFrame Combinado
            st.subheader("DataFrame de Competencia (Incluyendo Nuevos Competidores)")

            def crear_dataframe_competencia(df, oem_seleccionado):
                """Creates a DataFrame with information of all  for the OEM selected."""
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
                    'Visitas': 'sum',
                    'Título': 'first',
                    'ID': 'first',
                    'permalink': 'first'
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

            st.subheader("Análisis Detallado de Características")

            # 1) Gráfico de Título vs. Fecha de Última Actualización
            st.subheader("Fecha de Última Actualización")

            # Verificar si la columna 'Fecha de Última Actualización' existe
            if 'Fecha de Última Actualización' in df_oem.columns:
                # Convertir la columna a tipo datetime si no lo es
                if not pd.api.types.is_datetime64_any_dtype(df_oem['Fecha de Última Actualización']):
                    df_oem['Fecha de Última Actualización'] = pd.to_datetime(df_oem['Fecha de Última Actualización'])

                # Extraer la fecha
                df_oem['Fecha de Última Actualización'] = df_oem['Fecha de Última Actualización'].dt.date

                # Contar la frecuencia de cada fecha
                fecha_counts = df_oem['Fecha de Última Actualización'].value_counts().reset_index()
                fecha_counts.columns = ['Fecha', 'Cantidad']

                # Crear el gráfico de torta
                fig_fecha_actualizacion = px.pie(fecha_counts, values='Cantidad', names='Fecha',
                                                title='Distribución de Fechas de Última Actualización',
                                                labels={'Fecha': 'Fecha de Última Actualización', 'Cantidad': 'Cantidad'},
                                                color_discrete_sequence=px.colors.sequential.Plasma)
                st.plotly_chart(fig_fecha_actualizacion)
            else:
                st.warning("La columna 'Fecha de Última Actualización' no existe en el DataFrame.")

        # 2) Gráfico de Warranty por Título
            st.subheader("Garantía por Título")
            # Initialize fig_warranty to None in case the following code is skipped.
            fig_warranty = None
            if 'warranty' in df_oem.columns and 'Título' in df_oem.columns:
                warranty_counts = df_oem.groupby('Título')['warranty'].value_counts().unstack().fillna(0)
                fig_warranty = px.bar(warranty_counts, x=warranty_counts.index, y=warranty_counts.columns,
                                title='Distribución de Garantía por Título',
                                labels={'value': 'Cantidad', 'Título': 'Título del Producto'},
                                color_continuous_scale=px.colors.sequential.Plasma)
            else:
                st.warning("Las columnas 'warranty' o 'Título' no existen en el DataFrame.")

            if fig_warranty is not None: # add this if statement
                st.plotly_chart(fig_warranty)


        # 3) Gráfico de Tags (catalog_listing y/o catalog_forewarning) por Título
            st.subheader("Catálogo por Título")

            def esta_en_catalogo(tags_list):
                if isinstance(tags_list, str):
                    tags_list = eval(tags_list)  # Convert string representation to list
                
                for tag in tags_list:
                    if 'catalog_listing_eligible' in tag or 'catalog_forewarning' in tag or 'catalog_boost' in tag:
                        return 'Sí'
                return 'No'
            
            if 'tags' in df_oem.columns:
                df_oem['en_catalogo'] = df_oem['tags'].apply(esta_en_catalogo)

                # Contar cuántos títulos están en el catálogo y cuántos no
                catalogo_counts = df_oem['en_catalogo'].value_counts().reset_index()
                catalogo_counts.columns = ['En Catálogo', 'Cantidad']

                # Crear un gráfico de torta
                fig_catalogo = px.pie(catalogo_counts, values='Cantidad', names='En Catálogo',
                                        title='Distribución de Productos en Catálogo',
                                        color_discrete_sequence=px.colors.sequential.Plasma)
                st.plotly_chart(fig_catalogo)
            else:
                st.warning("La columna 'tags' no existe en el DataFrame.")
        
        # 5) Gráfico detallado de Cuota Simple
            st.subheader("Tipos de Cuota Simple")

            def extract_cuota_simple_type(tags_list):
                if isinstance(tags_list, str):
                    tags_list = eval(tags_list)  # Convert string representation to list
                
                cuota_types = []  # Lista para almacenar los tipos de cuota simple encontrados
                for tag in tags_list:
                    if 'cuota-simple-paid-by-buyer' in tag:
                        cuota_types.append('cuota-simple-paid-by-buyer')
                    elif 'cuota-simple-3' in tag:
                        cuota_types.append('cuota-simple-3')
                    elif 'cuota-simple-6' in tag:
                        cuota_types.append('cuota-simple-6')
                    elif 'cuota-simple-9' in tag:
                        cuota_types.append('cuota-simple-9')
                    elif 'cuota-simple-12' in tag:
                        cuota_types.append('cuota-simple-12')
                
                if cuota_types:
                    return ', '.join(cuota_types)  # Retorna una cadena con los tipos encontrados
                else:
                    return 'Ninguna'  # Si no se encuentra ninguna cuota simple
            
            if 'tags' in df_oem.columns:
                df_oem['tipo_cuota_simple'] = df_oem['tags'].apply(extract_cuota_simple_type)

                # Contar la frecuencia de cada tipo de cuota simple
                tipo_cuota_simple_counts = df_oem['tipo_cuota_simple'].value_counts().reset_index()
                tipo_cuota_simple_counts.columns = ['Tipo de Cuota Simple', 'Cantidad']

                # Crear un gráfico de torta
                fig_tipos_cuota_simple = px.pie(tipo_cuota_simple_counts, values='Cantidad', names='Tipo de Cuota Simple',
                                                    title='Distribución de Tipos de Cuota Simple',
                                                    color_discrete_sequence=px.colors.sequential.Plasma)
                st.plotly_chart(fig_tipos_cuota_simple)
            else:
                st.warning("La columna 'tags' no existe en el DataFrame.")

        # 6) Gráfico de Free Shipping por Título
            st.subheader("Free Shipping por Título")

            def extract_free_shipping(shipping_info):
                if isinstance(shipping_info, str):
                    shipping_info = eval(shipping_info)
                return shipping_info.get('free_shipping', False)
            
            if 'shipping' in df_oem.columns and 'Título' in df_oem.columns:
                df_oem['free_shipping'] = df_oem['shipping'].apply(extract_free_shipping)
                free_shipping_counts = df_oem.groupby('Título')['free_shipping'].value_counts().unstack().fillna(0)
                fig_free_shipping = px.bar(free_shipping_counts, x=free_shipping_counts.index,
                                            y=free_shipping_counts.columns,
                                            title='Distribución de Free Shipping por Título',
                                            labels={'value': 'Cantidad', 'Título': 'Título del Producto'},
                                            color_continuous_scale=px.colors.sequential.Plasma)
                st.plotly_chart(fig_free_shipping)
            else:
                st.warning("Las columnas 'shipping' o 'Título' no existen en el DataFrame.")
        else:
            st.warning("Por favor, cargue un archivo de competidores para realizar el análisis.")












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
    df_filtrado = pd.DataFrame()  # DataFrame vacio como valor por defecto

    if seleccion == 'Página Principal':
        pass  # La página principal ya se ha mostrado, no hay nada más que hacer aquí.
    elif seleccion == 'Mercado':
        if data is not None and fecha_inicio is not None and fecha_fin is not None:  # Verificar si los datos se cargaron correctamente y las fechas están definidas
            df_filtrado, df_descarga = mercado(data, fecha_inicio, fecha_fin)
        else:
            st.warning("Por favor, cargue los datos en la página principal y asegúrese de que la columna 'Fecha' esté presente.")
    elif seleccion == 'Estrategia Actual':
        if data is not None and fecha_inicio is not None and fecha_fin is not None:  # Verifico que data y las fechas existan
            df_filtrado = data[(data['Fecha'] >= fecha_inicio) & (data['Fecha'] <= fecha_fin)]  # Aplico filtro de fechas
            if not df_filtrado.empty:  # Solo llama a estrategia_actual si df_filtrado no está vacío
                df_estrat = estrategia_actual(df_filtrado.copy())  # Pasamos df_filtrado como argumento
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
    elif seleccion == 'Redes Neuronales':
        if data is not None:
            redes_neuronales(data.copy()) # Pass a copy to avoid modifying the original dataframe
        else:
            st.warning("Por favor, cargue los datos en la página principal.")

if __name__ == '__main__':
    main()
