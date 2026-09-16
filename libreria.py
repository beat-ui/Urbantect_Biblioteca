import streamlit as st
import json
import os
import re
from streamlit_js_eval import streamlit_js_eval

# ==================== CONFIGURACIÓN DE PÁGINA ====================
st.set_page_config(
    page_title="Libreria Urbantect",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== FUNCIONES DE ARCHIVO ====================
def obtener_ruta_app():
    return os.path.dirname(os.path.abspath(__file__))

def cargar_datos():
    json_path = os.path.join(obtener_ruta_app(), "inventario_libros.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error al cargar: {e}")
            return []
    return []

def guardar_datos(libros):
    json_path = os.path.join(obtener_ruta_app(), "inventario_libros.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(libros, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# ==================== ORDENAMIENTO LCC ====================
def ordenar_lcc(lcc):
    if not lcc:
        return ("", 0, "", 0, 0)
    lcc = lcc.strip().upper()
    patron = r'^([A-Z]+)\s+(\d+)\s+([A-Z0-9]+)(?:\s+(\d{4}))?$'
    match = re.match(patron, lcc)
    if match:
        letras = match.group(1)
        numero_clasif = int(match.group(2))
        letras_num = match.group(3)
        anio = int(match.group(4)) if match.group(4) else 0
        match_final = re.match(r'^([A-Z]+)(\d+)$', letras_num)
        if match_final:
            letras_final = match_final.group(1)
            num_final = int(match_final.group(2))
        else:
            letras_final = letras_num
            num_final = 0
        return (letras, numero_clasif, letras_final, num_final, anio)
    return (lcc, 0, "", 0, 0)

def encontrar_posicion_por_lcc(nuevo_libro, libros):
    nueva_clave = ordenar_lcc(nuevo_libro.get("LCC", ""))
    for i, libro_existente in enumerate(libros):
        clave_existente = ordenar_lcc(libro_existente.get("LCC", ""))
        if nueva_clave < clave_existente:
            return i
    return len(libros)

# ==================== ESTADO DE LA SESIÓN ====================
if "libros" not in st.session_state:
    st.session_state.libros = cargar_datos()

if "modo" not in st.session_state:
    st.session_state.modo = "Consutar"

if "libro_en_edicion" not in st.session_state:
    st.session_state.libro_en_edicion = None

if "mensaje_exito" not in st.session_state:
    st.session_state.mensaje_exito = None

if "libro_seleccionado_id" not in st.session_state:
    st.session_state.libro_seleccionado_id = None

# ==================== ENCABEZADO ====================
st.title("INVENTARIO DE LA BIBLIOTECA")

col_a, col_b = st.columns([3, 1])
with col_a:
    st.caption(f"Total de libros en inventario: **{len(st.session_state.libros)}**")
with col_b:
    modo_actual = st.session_state.modo
    color = "🔵" if modo_actual == "Consultar" else "🟢"
    st.markdown(f"### {color} MODO {modo_actual.upper()}")

if st.session_state.mensaje_exito:
    st.success(st.session_state.mensaje_exito)
    st.session_state.mensaje_exito = None

# ==================== BARRA LATERAL ====================
with st.sidebar:
    st.header("Panel de Control")

    nuevo_modo = st.radio(
        "Modo de operación:",
        ("Consultar", "Modificar"),
        index=0 if st.session_state.modo == "Consultar" else 1
    )

    if nuevo_modo != st.session_state.modo:
        st.session_state.modo = nuevo_modo
        st.session_state.libro_en_edicion = None
        st.rerun()

    st.divider()

    if st.session_state.modo == "Modificar":
        st.subheader("Registrar Nuevo Libro")

        with st.form("form_registro", clear_on_submit=True):
            titulo = st.text_input("Título *")
            autor = st.text_input("Autor *")
            lcc = st.text_input("LCC *")
            isbn = st.text_input("ISBN")
            materia = st.text_input("Materia")
            anio = st.text_input("Año")
            editorial = st.text_input("Editorial")
            ubicacion = st.text_input("Ubicación")

            submitted = st.form_submit_button("Registrar Libro")

            if submitted:
                if not titulo or not autor or not lcc:
                    st.error("Título, Autor y LCC son obligatorios.")
                else:
                    nuevo_libro = {
                        "Titulo": titulo,
                        "Autor": autor,
                        "ISBN": isbn,
                        "Materia": materia,
                        "Año": anio,
                        "Editorial": editorial,
                        "LCC": lcc,
                        "Ubicacion": ubicacion,
                        "id": len(st.session_state.libros) + 1
                    }
                    pos = encontrar_posicion_por_lcc(nuevo_libro, st.session_state.libros)
                    st.session_state.libros.insert(pos, nuevo_libro)

                    for i, l in enumerate(st.session_state.libros, 1):
                        l["id"] = i

                    if guardar_datos(st.session_state.libros):
                        st.session_state.mensaje_exito = f"Libro '{titulo}' registrado correctamente."
                        st.rerun()

# ==================== BÚSQUEDA ====================
st.subheader("Búsqueda de Libros")

col1, col2, col3 = st.columns([1, 3, 1])
with col1:
    criterio = st.selectbox(
        "Buscar por:",
        ["Titulo", "Autor", "ISBN", "Materia", "Editorial", "Año", "LCC", "Ubicacion"]
    )
with col2:
    termino = st.text_input("Término de búsqueda", placeholder="Escribe aquí...")
with col3:
    st.write("")
    st.write("")
    if st.button("Mostrar Todos", use_container_width=True):
        termino = ""

termino_global = st.text_input("Búsqueda global (en todos los campos)", placeholder="Escribe aquí...")

# ==================== FILTRADO ====================
libros_filtrados = st.session_state.libros

if termino:
    libros_filtrados = [
        libro for libro in libros_filtrados
        if termino.lower() in str(libro.get(criterio, "")).lower()
    ]

if termino_global:
    resultados = []
    for libro in libros_filtrados:
        for k, v in libro.items():
            if k != "id" and termino_global.lower() in str(v).lower():
                resultados.append(libro)
                break
    libros_filtrados = resultados

# ==================== TABLA ====================
st.subheader(f"Libros Registrados ({len(libros_filtrados)} encontrados)")
st.caption("Haz clic en una fila de la tabla para seleccionar un libro.")

if libros_filtrados:
    datos_tabla = []
    for i, libro in enumerate(libros_filtrados, 1):
        datos_tabla.append({
            "No.": i,
            "LCC": libro.get("LCC", ""),
            "Titulo": libro.get("Titulo", ""),
            "Autor": libro.get("Autor", ""),
            "ISBN": libro.get("ISBN", ""),
            "Materia": libro.get("Materia", ""),
            "Año": libro.get("Año", ""),
            "Editorial": libro.get("Editorial", ""),
            "Ubicacion": libro.get("Ubicacion", ""),
        })

    altura_pantalla = streamlit_js_eval(js_expressions='window.innerHeight', key='altura_ventana')

    if altura_pantalla:
        altura_dataframe = int(altura_pantalla) - 450
        if altura_dataframe < 300:
            altura_dataframe = 300
    else:
        altura_dataframe = 600

    # Tabla con selección por clic
    evento = st.dataframe(
        datos_tabla,
        use_container_width=True,
        hide_index=True,
        height=altura_dataframe,
        on_select="rerun",
        selection_mode="single-row",
        key="tabla_libros",
        column_config={
            "No.": st.column_config.NumberColumn("No.", width="small"),
            "LCC": st.column_config.TextColumn("LCC", width="small"),
            "Titulo": st.column_config.TextColumn("Título", width="large"),
            "Autor": st.column_config.TextColumn("Autor", width="medium"),
            "ISBN": st.column_config.TextColumn("ISBN", width="small"),
            "Materia": st.column_config.TextColumn("Materia", width="medium"),
            "Año": st.column_config.TextColumn("Año", width="small"),
            "Editorial": st.column_config.TextColumn("Editorial", width="medium"),
            "Ubicacion": st.column_config.TextColumn("Ubicación", width="small"),
        }
    )

    # Detectar si el usuario hizo clic en alguna fila
    filas_seleccionadas = evento.selection.rows
    if filas_seleccionadas:
        idx_fila = filas_seleccionadas[0]
        libro_sel = libros_filtrados[idx_fila]
        st.session_state.libro_seleccionado_id = libro_sel.get("id")
        st.success(f"Libro seleccionado: **{libro_sel.get('Titulo', '')}**")
else:
    st.warning("No se encontraron libros.")

# ==================== ACCIONES SOBRE LIBRO SELECCIONADO ====================
libro_sel = None
if st.session_state.libro_seleccionado_id is not None:
    for l in st.session_state.libros:
        if l.get("id") == st.session_state.libro_seleccionado_id:
            libro_sel = l
            break

if libro_sel:
    st.divider()
    st.subheader("Acciones sobre el libro seleccionado")
    st.info(f"Seleccionado: **{libro_sel.get('Titulo', '')}** — {libro_sel.get('Autor', '')}")

    if st.session_state.modo == "Consultar":
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Editar este libro", use_container_width=True):
                st.session_state.libro_en_edicion = libro_sel
                st.session_state.modo = "Modificar"
                st.rerun()

    elif st.session_state.modo == "Modificar":
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Editar", use_container_width=True):
                st.session_state.libro_en_edicion = libro_sel
                st.rerun()
        with col2:
            if st.button("Eliminar", use_container_width=True):
                id_libro = libro_sel.get("id")
                st.session_state.libros = [
                    l for l in st.session_state.libros if l.get("id") != id_libro
                ]
                for i, l in enumerate(st.session_state.libros, 1):
                    l["id"] = i
                if guardar_datos(st.session_state.libros):
                    st.session_state.mensaje_exito = f"Libro '{libro_sel.get('Titulo', '')}' eliminado."
                    st.session_state.libro_en_edicion = None
                    st.session_state.libro_seleccionado_id = None
                    st.rerun()

        st.markdown("##### Ordenamiento manual")
        st.caption("Mueve este libro dentro de la lista. Solo funciona cuando ves TODOS los libros (sin filtros).")

        hay_filtros = bool(termino) or bool(termino_global)

        col_u, col_d, col_t, col_b = st.columns(4)

        with col_u:
            if st.button("Subir", use_container_width=True, disabled=hay_filtros):
                idx_real = st.session_state.libros.index(libro_sel)
                if idx_real > 0:
                    st.session_state.libros.pop(idx_real)
                    st.session_state.libros.insert(idx_real - 1, libro_sel)
                    for i, l in enumerate(st.session_state.libros, 1):
                        l["id"] = i
                    if guardar_datos(st.session_state.libros):
                        st.rerun()
                else:
                    st.warning("Ya está en la primera posición.")

        with col_d:
            if st.button("Bajar", use_container_width=True, disabled=hay_filtros):
                idx_real = st.session_state.libros.index(libro_sel)
                if idx_real < len(st.session_state.libros) - 1:
                    st.session_state.libros.pop(idx_real)
                    st.session_state.libros.insert(idx_real + 1, libro_sel)
                    for i, l in enumerate(st.session_state.libros, 1):
                        l["id"] = i
                    if guardar_datos(st.session_state.libros):
                        st.rerun()
                else:
                    st.warning("Ya está en la última posición.")

        with col_t:
            if st.button("Al principio", use_container_width=True, disabled=hay_filtros):
                idx_real = st.session_state.libros.index(libro_sel)
                if idx_real > 0:
                    st.session_state.libros.pop(idx_real)
                    st.session_state.libros.insert(0, libro_sel)
                    for i, l in enumerate(st.session_state.libros, 1):
                        l["id"] = i
                    if guardar_datos(st.session_state.libros):
                        st.rerun()
                else:
                    st.warning("Ya está en la primera posición.")

        with col_b:
            if st.button("Al final", use_container_width=True, disabled=hay_filtros):
                idx_real = st.session_state.libros.index(libro_sel)
                if idx_real < len(st.session_state.libros) - 1:
                    st.session_state.libros.pop(idx_real)
                    st.session_state.libros.append(libro_sel)
                    for i, l in enumerate(st.session_state.libros, 1):
                        l["id"] = i
                    if guardar_datos(st.session_state.libros):
                        st.rerun()
                else:
                    st.warning("Ya está en la última posición.")

        if hay_filtros:
            st.info("Para usar el ordenamiento manual, primero quita los filtros de búsqueda (deja los campos vacíos y presiona 'Mostrar Todos').")

# ==================== FORMULARIO DE EDICIÓN ====================
if st.session_state.libro_en_edicion:
    st.divider()
    st.subheader("Editando libro")

    libro = st.session_state.libro_en_edicion

    with st.form("form_edicion"):
        titulo = st.text_input("Título *", value=libro.get("Titulo", ""))
        autor = st.text_input("Autor *", value=libro.get("Autor", ""))
        lcc = st.text_input("LCC *", value=libro.get("LCC", ""))
        isbn = st.text_input("ISBN", value=libro.get("ISBN", ""))
        materia = st.text_input("Materia", value=libro.get("Materia", ""))
        anio = st.text_input("Año", value=libro.get("Año", ""))
        editorial = st.text_input("Editorial", value=libro.get("Editorial", ""))
        ubicacion = st.text_input("Ubicación", value=libro.get("Ubicacion", ""))

        col_save, col_cancel = st.columns(2)
        with col_save:
            guardar = st.form_submit_button("Guardar cambios", use_container_width=True)
        with col_cancel:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)

        if guardar:
            if not titulo or not autor or not lcc:
                st.error("Título, Autor y LCC son obligatorios.")
            else:
                libro_actualizado = {
                    "Titulo": titulo,
                    "Autor": autor,
                    "ISBN": isbn,
                    "Materia": materia,
                    "Año": anio,
                    "Editorial": editorial,
                    "LCC": lcc,
                    "Ubicacion": ubicacion,
                    "id": libro.get("id")
                }

                # === AQUÍ ESTÁ EL CAMBIO CLAVE ===
                # Solo reordenar si el LCC cambió. Si no, mantiene la posición.
                lcc_cambio = libro_actualizado["LCC"] != libro.get("LCC", "")

                idx = st.session_state.libros.index(libro)
                st.session_state.libros.pop(idx)

                if lcc_cambio:
                    nueva_pos = encontrar_posicion_por_lcc(libro_actualizado, st.session_state.libros)
                    st.session_state.libros.insert(nueva_pos, libro_actualizado)
                else:
                    st.session_state.libros.insert(idx, libro_actualizado)

                for i, l in enumerate(st.session_state.libros, 1):
                    l["id"] = i

                if guardar_datos(st.session_state.libros):
                    st.session_state.mensaje_exito = f"Libro '{titulo}' actualizado correctamente."
                    st.session_state.libro_en_edicion = None
                    st.rerun()

        if cancelar:
            st.session_state.libro_en_edicion = None
            st.rerun()

# ==================== EXPORTAR ====================
st.divider()
if st.button("Exportar/Guardar JSON"):
    if guardar_datos(st.session_state.libros):
        st.session_state.mensaje_exito = f"Datos guardados. Total: {len(st.session_state.libros)} libros."
        st.rerun()