# =========================================================
# 1. IMPORTACIONES
# =========================================================
# FastAPI crea la aplicacion web
# HTTPException permite mostrar errores
# HTMLResponse permite devolver una pagina HTML
# BaseModel valida los datos X, Y y Z
# random genera numeros aleatorios

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import random


# =========================================================
# 2. CONFIGURACION PRINCIPAL
# =========================================================

# Creamos la aplicacion
app = FastAPI()

# TAM indica el tamano del mosaico: 12 x 12
TAM = 12

# Creamos una matriz de 12 x 12 llena de ceros
matriz = [[0 for y in range(TAM)] for x in range(TAM)]

# Aqui se guardan estados anteriores para usar Undo
historial = []


# =========================================================
# 3. DATOS QUE RECIBE EL PROGRAMA
# =========================================================

# Esta clase define los datos que recibimos:
# X = fila
# Y = columna
# Z = altura o valor
class Datos(BaseModel):
    x: int
    y: int
    z: int


# =========================================================
# 4. FUNCIONES PRINCIPALES DE PYTHON
# =========================================================

# Obtiene la matriz, el valor maximo y el valor minimo
def informacion():
    valores = []

    # Recorremos cada fila y agregamos sus valores
    for fila in matriz:
        valores += fila

    return {
        "matriz": matriz,
        "maximo": max(valores),
        "minimo": min(valores)
    }


# Guarda una copia de la matriz actual
# Esto sirve para poder hacer Undo
def guardar():
    historial.append([fila.copy() for fila in matriz])


# =========================================================
# 5. RUTAS DE LA API
# =========================================================

# GET obtiene la matriz actual
@app.get("/api/matriz")
def ver_matriz():
    return informacion()


# POST genera valores aleatorios en todo el mosaico
@app.post("/api/mix")
def mix():
    guardar()

    for x in range(TAM):
        for y in range(TAM):
            matriz[x][y] = random.randint(-100, 100)

    return informacion()


# POST cambia el valor de una celda especifica
@app.post("/api/asignar")
def asignar(datos: Datos):

    # Validamos que X exista dentro del mosaico
    if datos.x < 1 or datos.x > TAM:
        raise HTTPException(400, "X no es valido")

    # Validamos que Y exista dentro del mosaico
    if datos.y < 1 or datos.y > TAM:
        raise HTTPException(400, "Y no es valido")

    # Z solo puede estar entre -100 y 100
    if datos.z < -100 or datos.z > 100:
        raise HTTPException(400, "Z debe estar entre -100 y 100")

    guardar()

    # Restamos 1 porque Python empieza a contar desde 0
    matriz[datos.x - 1][datos.y - 1] = datos.z

    return informacion()


# POST regresa al estado anterior
@app.post("/api/undo")
def undo():
    global matriz

    if len(historial) == 0:
        raise HTTPException(400, "No hay cambios")

    matriz = historial.pop()

    return informacion()


# POST vuelve a poner toda la matriz en cero
@app.post("/api/reiniciar")
def reiniciar():
    guardar()

    for x in range(TAM):
        for y in range(TAM):
            matriz[x][y] = 0

    return informacion()


# =========================================================
# 6. PAGINA PRINCIPAL
# =========================================================
# Esta ruta manda la pagina al navegador

@app.get("/", response_class=HTMLResponse)
def pagina():

    return """
<!DOCTYPE html>

<html>

<head>

<title>Mosaico de Alturas</title>


<!-- =====================================================
     7. CSS
     Esta parte controla el aspecto visual de la pagina
===================================================== -->

<style>

body {
    font-family: Arial;
    text-align: center;
    background: #eeeeee;
}

main {
    width: 900px;
    margin: 25px auto;
    background: white;
    padding: 20px;
    border-radius: 12px;
}

input {
    width: 65px;
    padding: 7px;
    margin: 5px;
}

button {
    padding: 9px 14px;
    margin: 5px;
    cursor: pointer;
}

/* Aqui se forma el mosaico de 12 columnas */
#mosaico {
    display: grid;
    grid-template-columns: repeat(12, 50px);
    gap: 2px;
    justify-content: center;
    margin-top: 20px;
}

/* Estilo de cada cuadrito */
.celda {
    width: 50px;
    height: 50px;
    border: 1px solid #555;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    cursor: pointer;
}

/* Efecto cuando pasamos el mouse */
.celda:hover {
    transform: scale(1.08);
}

/* Borde de la celda seleccionada */
.seleccionada {
    outline: 4px solid black;
    z-index: 2;
}

#mensaje {
    margin: 12px;
    font-weight: bold;
}

/* Estilo de la leyenda de colores */
.leyenda span {
    display: inline-block;
    padding: 7px;
    margin: 3px;
    border: 1px solid #555;
}

</style>

</head>


<body>

<main>

<h1>Mosaico de Alturas</h1>


<!-- =====================================================
     8. HTML
     Controles que ve el usuario
===================================================== -->

X:
<input type="number" id="x">

Y:
<input type="number" id="y">

Z:
<input type="number" id="z">

<br>

<button onclick="aplicar()">Aplicar valor</button>
<button onclick="mix()">Mixear valores</button>
<button onclick="undo()">Undo</button>
<button onclick="reiniciar()">Reiniciar</button>


<p>
    Altura maxima:
    <b id="maximo">0</b>

    &nbsp;&nbsp;

    Altura minima:
    <b id="minimo">0</b>
</p>


<p>
    Celda seleccionada:
    <b id="seleccion">Ninguna</b>
</p>


<!-- Aqui se dibuja el mosaico -->
<div id="mosaico"></div>

<!-- Aqui aparecen mensajes -->
<div id="mensaje"></div>


<!-- Leyenda de colores -->
<div class="leyenda">

<h3>Leyenda</h3>

<span style="background:#08306b;color:white;">Muy bajo</span>
<span style="background:#6baed6;">Bajo</span>
<span style="background:#eeeeee;">0</span>
<span style="background:#fdae6b;">Alto</span>
<span style="background:#a63603;color:white;">Muy alto</span>

</div>

</main>


<!-- =====================================================
     9. JAVASCRIPT
     Esta parte hace interactiva la pagina
===================================================== -->

<script>

let seleccionX = null;
let seleccionY = null;


/* =====================================================
   9.1 COLORES
   Decide el color dependiendo del valor Z
===================================================== */

function color(valor) {

    if (valor <= -75) return "#08306b";
    if (valor <= -50) return "#2171b5";
    if (valor <= -25) return "#6baed6";
    if (valor < 0) return "#c6dbef";
    if (valor == 0) return "#eeeeee";
    if (valor <= 25) return "#fee6ce";
    if (valor <= 50) return "#fdae6b";
    if (valor <= 75) return "#f16913";

    return "#a63603";
}


/* =====================================================
   9.2 DIBUJAR EL MOSAICO
===================================================== */

function mostrar(datos) {

    const mosaico =
        document.getElementById("mosaico");

    // Limpiamos el mosaico antes de volver a dibujarlo
    mosaico.innerHTML = "";

    // Mostramos maximo y minimo
    document.getElementById("maximo").textContent =
        datos.maximo;

    document.getElementById("minimo").textContent =
        datos.minimo;


    // Recorremos todas las filas
    for (let x = 0; x < datos.matriz.length; x++) {

        // Recorremos todas las columnas
        for (let y = 0; y < datos.matriz[x].length; y++) {

            let valor =
                datos.matriz[x][y];

            // Creamos un cuadrito
            let celda =
                document.createElement("div");

            celda.className =
                "celda";


            // Si esta seleccionada, le ponemos borde
            if (seleccionX == x && seleccionY == y) {
                celda.classList.add("seleccionada");
            }


            // Mostramos el valor dentro del cuadro
            celda.textContent =
                valor;

            // Aplicamos el color correspondiente
            celda.style.backgroundColor =
                color(valor);


            // Ponemos letras blancas en colores oscuros
            if (valor <= -50 || valor > 50) {
                celda.style.color = "white";
            }


            /* Cuando hacemos clic en una celda:
               guarda X, Y y Z arriba
               y marca el cuadro seleccionado
            */

            celda.onclick = function() {

                seleccionX = x;
                seleccionY = y;

                document.getElementById("x").value =
                    x + 1;

                document.getElementById("y").value =
                    y + 1;

                document.getElementById("z").value =
                    valor;

                document.getElementById("seleccion").textContent =
                    "X: " + (x + 1) +
                    "  Y: " + (y + 1) +
                    "  Z: " + valor;

                mostrar(datos);

                document.getElementById("mensaje").textContent =
                    "Celda seleccionada";
            };


            // Agregamos la celda al mosaico
            mosaico.appendChild(celda);
        }
    }
}


/* =====================================================
   9.3 CARGAR LA MATRIZ
===================================================== */

async function cargar() {

    let respuesta =
        await fetch("/api/matriz");

    mostrar(await respuesta.json());
}


/* =====================================================
   9.4 BOTON MIX
===================================================== */

async function mix() {

    let respuesta =
        await fetch("/api/mix", {
            method: "POST"
        });

    let datos =
        await respuesta.json();

    mostrar(datos);

    document.getElementById("mensaje").textContent =
        "Valores mezclados";
}


/* =====================================================
   9.5 BOTON APLICAR VALOR
===================================================== */

async function aplicar() {

    let x =
        document.getElementById("x").value;

    let y =
        document.getElementById("y").value;

    let z =
        document.getElementById("z").value;


    // Validamos que los campos tengan datos
    if (!x || !y || !z) {

        document.getElementById("mensaje").textContent =
            "Llena X, Y y Z";

        return;
    }


    // Mandamos los datos a Python
    let respuesta =
        await fetch("/api/asignar", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                x: Number(x),
                y: Number(y),
                z: Number(z)
            })
        });


    let datos =
        await respuesta.json();


    // Si ocurre un error, lo mostramos
    if (!respuesta.ok) {

        document.getElementById("mensaje").textContent =
            datos.detail;

        return;
    }


    // Guardamos la celda seleccionada
    seleccionX = Number(x) - 1;
    seleccionY = Number(y) - 1;


    document.getElementById("seleccion").textContent =
        "X: " + x +
        "  Y: " + y +
        "  Z: " + z;


    mostrar(datos);


    document.getElementById("mensaje").textContent =
        "Valor aplicado";
}


/* =====================================================
   9.6 BOTON UNDO
===================================================== */

async function undo() {

    let respuesta =
        await fetch("/api/undo", {
            method: "POST"
        });


    let datos =
        await respuesta.json();


    if (!respuesta.ok) {

        document.getElementById("mensaje").textContent =
            datos.detail;

        return;
    }


    mostrar(datos);


    document.getElementById("mensaje").textContent =
        "Cambio deshecho";
}


/* =====================================================
   9.7 BOTON REINICIAR
===================================================== */

async function reiniciar() {

    let respuesta =
        await fetch("/api/reiniciar", {
            method: "POST"
        });


    let datos =
        await respuesta.json();


    // Quitamos la seleccion
    seleccionX = null;
    seleccionY = null;


    document.getElementById("seleccion").textContent =
        "Ninguna";


    // Limpiamos X, Y y Z
    document.getElementById("x").value = "";
    document.getElementById("y").value = "";
    document.getElementById("z").value = "";


    mostrar(datos);


    document.getElementById("mensaje").textContent =
        "Mosaico reiniciado";
}


/* =====================================================
   9.8 INICIAR LA PAGINA
===================================================== */

cargar();

</script>

</body>

</html>
"""