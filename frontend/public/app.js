const API = "/api";
const cuerpo = document.getElementById("cuerpo-pedidos");
const vacio = document.getElementById("vacio");
const mensaje = document.getElementById("mensaje");
const dialogo = document.getElementById("dialogo");
const form = document.getElementById("form-pedido");

function mostrarMensaje(texto, tipo) {
  mensaje.textContent = texto;
  mensaje.className = tipo;
  mensaje.hidden = false;
}

function fila(p) {
  const tr = document.createElement("tr");
  tr.setAttribute("data-testid", `pedido-${p.id}`);
  const celdas = [p.id, p.usuario, p.costo.toFixed(2), null, p.detalle ?? "", p.creado_en];
  celdas.forEach((valor, i) => {
    const td = document.createElement("td");
    if (i === 3) {
      const badge = document.createElement("span");
      badge.className = `estado ${p.estado_pago.toLowerCase()}`;
      badge.setAttribute("data-testid", "estado-pago");
      badge.textContent = p.estado_pago;
      td.appendChild(badge);
    } else {
      td.textContent = valor;
    }
    tr.appendChild(td);
  });
  return tr;
}

async function cargarPedidos() {
  const r = await fetch(`${API}/pedidos`);
  const pedidos = await r.json();
  cuerpo.replaceChildren(...pedidos.map(fila));
  vacio.hidden = pedidos.length > 0;
}

document.getElementById("btn-crear").addEventListener("click", () => {
  form.reset();
  dialogo.showModal();
});
document.getElementById("btn-cancelar").addEventListener("click", () => dialogo.close());

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const datos = new FormData(form);
  const cuerpoSolicitud = {
    usuario: datos.get("usuario"),
    costo: Number(datos.get("costo")),
    tarjeta: datos.get("tarjeta"),
  };
  dialogo.close();
  try {
    const r = await fetch(`${API}/pedidos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cuerpoSolicitud),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const p = await r.json();
    const textos = {
      APROBADO: `Pedido #${p.id} creado: pago APROBADO`,
      RECHAZADO: `Pedido #${p.id} creado: pago RECHAZADO (${p.detalle})`,
      ERROR: `Pedido #${p.id} creado: ERROR al procesar el pago (${p.detalle})`,
    };
    mostrarMensaje(textos[p.estado_pago], p.estado_pago.toLowerCase());
  } catch (err) {
    mostrarMensaje(`No se pudo crear el pedido: ${err.message}`, "error");
  }
  await cargarPedidos();
});

cargarPedidos();
