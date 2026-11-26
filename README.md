# Práctica optativa — comercio electrónico en MongoDB

Base de datos `ecommerce_nosql` en MongoDB Atlas. Modela una tienda con clientes, catálogo, inventario, pedidos, pagos y auditoría. Los documentos se relacionan por `ObjectId` (`cliente_id`, `producto_id`, `pedido_id`). Las consultas de este documento son las de **mongosh**. Los archivos `.py` cargan datos y prueban cifrado y subdocumentos desde Python.

La clave Fernet no está en el repositorio. `cifrado.py` la lee de `~/.ecommerce-fernet.key`. La conexión usa un archivo `.env` (tampoco se sube) con `MONGODB_URI` y `DB_NAME`.

## Colecciones

| Colección | Qué guarda |
| --- | --- |
| `clientes` | Nombre, apellidos, correo (hash SHA-256 y valor cifrado), teléfono cifrado, direcciones y si está activo |
| `productos` | SKU, nombre, categoría, precio decimal en MXN, proveedor y características |
| `pedidos` | Cliente, fecha, renglones de productos, importes y estado del pedido y del envío |
| `pagos` | Pedido, referencia, método, monto y estado del cobro |
| `inventario` | Existencias, unidades reservadas y stock mínimo por producto y almacén |
| `auditoria` | Usuario, acción (`INSERT`, `UPDATE`, `DELETE`), colección afectada y documento |

Estados de pedido: `Pendiente`, `Pagado`, `Enviado`, `Entregado`, `Cancelado`. Estados de pago: `Pendiente`, `Aprobado`, `Rechazado`. Métodos: `Tarjeta`, `Transferencia`, `Efectivo`. Moneda permitida: `MXN`.

---

## Archivos Python

Dependencias en `requirements.txt`: `pymongo` (driver), `python-dotenv` (lee `.env`), `Faker` (nombres y calles ficticias en español de México), `cryptography` (Fernet) y sus dependencias `cffi`, `pycparser` y `dnspython`.

### `cifrado.py`

Carga la clave simétrica desde `~/.ecommerce-fernet.key` y expone dos funciones:

- `cifrar(texto)` convierte el texto a bytes UTF-8, lo cifra con Fernet y devuelve el token en texto.
- `descifrar(texto_cifrado)` invierte esa operación.

Correo, teléfono y calle se guardan cifrados. El correo también se guarda como hash SHA-256 de 64 caracteres hexadecimales para poder buscar al cliente sin descifrar toda la colección.

### `main.py`

Prueba de un solo cliente. Se conecta a Atlas, hace `ping` y trabaja sobre la base indicada en `DB_NAME`.

1. Calcula el hash de `cliente@ejemplo.com`.
2. Busca un cliente con ese `correo_hash`.
3. Si no existe, inserta a Juan Perez Lopez con correo, teléfono `3312345678` y calle `Av. Vallarta` cifrados, ciudad Guadalajara, estado Jalisco, código postal `44160`, fecha UTC y `activo: true`.
4. Si la calle guardada sigue en texto plano (dato de una prueba anterior), la reemplaza por su versión cifrada.
5. Vuelve a leer el documento y imprime el correo, el teléfono y la calle ya descifrados, y también los tokens cifrados tal como quedaron en MongoDB.

### `seeding.py`

Poblado reproducible. Faker y `random` usan la semilla `2026`, así que los nombres y las cantidades salen iguales en cada ejecución. La fecha base de los documentos es el 1 de noviembre de 2026 (UTC). Cada función omite el documento si ya existe la clave de negocio (`correo_hash`, `sku`, `producto_id`, `seed_codigo` o `referencia`). Los precios y totales se guardan como `Decimal128` con dos decimales.

`crear_clientes` inserta hasta 20 clientes `cliente001@ejemplo.com` … `cliente020@ejemplo.com`. Nombre y apellidos salen de Faker. Correo, teléfono y calle van cifrados. Ciudad fija: Guadalajara, Jalisco. Todos quedan activos.

`crear_productos` inserta el catálogo de 25 productos, SKU `PROD-001` a `PROD-025`:

| SKU | Nombre | Categoría | Precio MXN |
| --- | --- | --- | --- |
| PROD-001 | Laptop Lenovo IdeaPad | Electronica | 12500 |
| PROD-002 | Mouse Logitech | Electronica | 450 |
| PROD-003 | Teclado Mecanico | Electronica | 1200 |
| PROD-004 | Monitor Samsung 24 | Electronica | 3200 |
| PROD-005 | Audifonos Bluetooth | Electronica | 850 |
| PROD-006 | Memoria USB 64GB | Electronica | 180 |
| PROD-007 | Disco SSD 1TB | Electronica | 1450 |
| PROD-008 | Webcam Full HD | Electronica | 680 |
| PROD-009 | Bocina Bluetooth | Electronica | 950 |
| PROD-010 | Cargador USB-C | Electronica | 350 |
| PROD-011 | Playera Deportiva | Ropa | 299 |
| PROD-012 | Sudadera | Ropa | 650 |
| PROD-013 | Pantalon Mezclilla | Ropa | 799 |
| PROD-014 | Tenis Deportivos | Ropa | 1350 |
| PROD-015 | Gorra | Accesorios | 250 |
| PROD-016 | Mochila Escolar | Accesorios | 780 |
| PROD-017 | Botella Termica | Accesorios | 390 |
| PROD-018 | Reloj Digital | Accesorios | 1100 |
| PROD-019 | Lampara de Escritorio | Hogar | 550 |
| PROD-020 | Silla de Oficina | Hogar | 2750 |
| PROD-021 | Organizador de Escritorio | Hogar | 320 |
| PROD-022 | Juego de Sabanas | Hogar | 890 |
| PROD-023 | Balon de Futbol | Deportes | 480 |
| PROD-024 | Mancuernas 5KG | Deportes | 720 |
| PROD-025 | Tapete de Yoga | Deportes | 450 |

El proveedor de esos productos es Distribuidora Comercial MX (`ventas@ejemplo.com`). `LAP-001` no sale de este catálogo: lo inserta la prueba de validación en mongosh y es el mismo modelo de laptop, con otra descripción y otro proveedor.

`crear_inventario` crea un registro en Almacén Principal por cada producto `LAP-001` y `PROD-001` … `PROD-025` que ya exista. Existencias aleatorias entre 15 y 100, reservadas entre 0 y 5, stock mínimo 10.

`crear_pedidos` crea 20 pedidos `SEED-PED-001` … `SEED-PED-020`. Cada uno toma el cliente de la misma posición y dos productos del catálogo (el de su índice y el de cinco posiciones más adelante). Cada renglón lleva de 1 a 3 unidades. Impuesto del 16 % sobre el subtotal y envío fijo de 150. Estado del pedido y del envío: `Pendiente`. Paquetería: DHL. La dirección de envío se copia del cliente.

`crear_pagos` crea un pago `SEED-PAGO-001` … `SEED-PAGO-020` por cada pedido semilla. El monto es el total del pedido. El método es Tarjeta, Transferencia o Efectivo. Estado: `Pendiente`. La fecha del pago es la fecha del pedido.

`crear_auditoria` crea 15 eventos `SEED-AUD-001` … `SEED-AUD-015`. No los generan triggers: el script los inserta a mano. Usuario `seed_script`, acción `INSERT`, colección `pedidos`, `datos_anteriores` nulo y `datos_nuevos` con estado `Pendiente`.

Al final imprime el `countDocuments` de las seis colecciones y la suma.

### `pruebas_subdocumetos.py`

Comprueba un pedido con arreglo de productos y subdocumento de envío.

1. Busca al cliente `cliente@ejemplo.com` por su hash y al producto `LAP-001`.
2. Si ese cliente ya tiene un pedido con el SKU `LAP-001`, reutiliza ese `_id`. Si no, inserta un pedido de 1 laptop a 12500, impuestos 0, envío 200 y total 12700, estado `Pendiente`, paquetería DHL y la dirección del cliente.
3. Lee el pedido guardado e imprime el id, el `cliente_id`, cuántos renglones hay, el nombre del primer producto, el estado del envío y el total.

Ese pedido de prueba (total 12700, sin código `SEED-PED`) es el que aparece primero en varias consultas de más abajo y no tiene pago asociado.

---

## Consultas mongosh

Todas empiezan con `use ecommerce_nosql`. Los archivos de creación, validación y verificación traen las consultas. Los de expresiones regulares y `$lookup` traen además la salida capturada el 26 de noviembre de 2026. Cada una de esas consultas pide como máximo 10 documentos: si la tabla tiene 10 filas, puede haber más en la colección.

### Creación de colecciones

Archivo: `01_creacion_colecciones.txt`. Seis `createCollection` con validador `$jsonSchema`, `validationLevel: "strict"` y `validationAction: "error"`. Un documento que no cumpla el esquema se rechaza.

**`clientes`.** Obligatorios: `nombre`, `apellidos`, `correo_hash`, `correo_cifrado`, `telefono_cifrado`, `direcciones`, `fecha_registro`, `activo`. El hash debe ser exactamente 64 hexadecimales. `direcciones` es un arreglo de al menos un objeto con calle, ciudad, estado y código postal de 5 dígitos. Nombre entre 2 y 80 caracteres, apellidos entre 2 y 100.

**`productos`.** Obligatorios: `sku`, `nombre`, `categoria`, `precio`, `moneda`, `proveedor`, `activo`. El SKU solo admite mayúsculas, dígitos y guion. El precio es `decimal` con mínimo 0.01. La moneda solo puede ser `MXN`. El proveedor exige nombre y un correo con forma `algo@dominio.ext`. La descripción, si viene, mide como máximo 1000 caracteres. `caracteristicas` es un objeto libre.

**`pedidos`.** Obligatorios: `cliente_id`, `fecha_pedido`, `productos`, `subtotal`, `impuestos`, `costo_envio`, `total`, `estado`. `productos` tiene al menos un renglón con `producto_id`, `sku`, `nombre`, `cantidad` entera mínima 1, `precio_unitario` decimal mínimo 0.01 y `subtotal` decimal mínimo 0. El total mínimo es 0.01. Si viene `envio`, exige paquetería, estado (`Pendiente`, `Preparando`, `En tránsito`, `Entregado`) y dirección.

**`pagos`.** Obligatorios: `pedido_id`, `referencia`, `metodo`, `monto`, `moneda`, `estado`, `fecha_pago`. La referencia usa el mismo patrón que el SKU. El monto mínimo es 0.01.

**`inventario`.** Obligatorios: `producto_id`, `almacen`, `existencias`, `reservadas`, `stock_minimo`, `ultima_actualizacion`. Las tres cantidades son enteros mayores o iguales a 0. El almacén tiene al menos 2 caracteres.

**`auditoria`.** Obligatorios: `usuario`, `accion`, `coleccion`, `documento_id`, `fecha`. La colección afectada solo puede ser `clientes`, `productos`, `pedidos`, `pagos` o `inventario`. `datos_anteriores` y `datos_nuevos` pueden ser objeto o `null`.

Estas sentencias no traen salida guardada en el archivo. Si la colección ya existe, MongoDB responde que el nombre está ocupado (`NamespaceExists`).

### Pruebas de validación

Archivo: `02_pruebas_validacion.txt`. El archivo guarda las consultas, no la respuesta de la shell. El efecto sale del validador de `productos`.

```javascript
db.productos.insertOne({
  sku: "LAP-001",
  nombre: "Laptop Lenovo IdeaPad",
  descripcion: "Laptop de 16 GB RAM y 512 GB SSD",
  categoria: "Electronica",
  precio: NumberDecimal("12500.00"),
  moneda: "MXN",
  proveedor: {
    nombre: "Distribuidora Tecnologia MX",
    correo: "ventas@ejemplo.com"
  },
  caracteristicas: { ram: "16 GB", almacenamiento: "512 GB SSD" },
  activo: true
})
```

Documento válido. Es el producto que después usan el pedido de prueba, el inventario y las búsquedas por SKU `LAP-001`. En los resultados aparece con precio 12500.00 y activo.

```javascript
db.productos.insertOne({
  sku: "LAP-002",
  nombre: "Laptop HP",
  categoria: "Electronica",
  precio: "10000",
  moneda: "MXN",
  proveedor: {
    nombre: "Distribuidora Tecnologia MX",
    correo: "ventas@ejemplo.com"
  },
  activo: true
})
```

El precio va como texto (`"10000"`) y el esquema exige `decimal`. La validación estricta rechaza el insert.

```javascript
db.productos.insertOne({
  sku: "LAP-003",
  nombre: "Laptop Dell",
  categoria: "Electronica",
  moneda: "MXN",
  proveedor: {
    nombre: "Distribuidora Tecnologia MX",
    correo: "ventas@ejemplo.com"
  },
  activo: true
})
```

Falta `precio`, que es obligatorio. El insert se rechaza.

```javascript
db.productos.updateOne(
  { sku: "LAP-001" },
  { $set: { precio: NumberDecimal("-500.00") } }
)
```

El precio mínimo del esquema es 0.01. Un decimal negativo no pasa la validación, así que `LAP-001` se queda en 12500.00. Las consultas posteriores lo confirman.

```javascript
db.productos.find({}, { _id: 0, sku: 1, nombre: 1, precio: 1 })
```

Lista sku, nombre y precio, sin `_id`. Sirve para ver qué inserts sí quedaron. En las capturas posteriores solo aparecen `LAP-001` y `PROD-001` … `PROD-025`; no hay `LAP-002` ni `LAP-003`.

### Verificaciones

Archivo: `03_verificaciones.txt`. Comprueban que la base y las colecciones quedaron creadas y que los clientes cifrados se pueden listar. El archivo no guarda la salida.

| Consulta | Para qué sirve |
| --- | --- |
| `db.getName()` | Confirma que la shell está en `ecommerce_nosql` |
| `show collections` | Lista los nombres de colecciones y vistas |
| `db.getCollectionInfos({ name: "clientes" })` | Muestra tipo, opciones y el validador `$jsonSchema` de `clientes` |
| `db.getCollectionInfos().map(...)` | Por cada colección indica si trae validador `$jsonSchema` |
| `db.clientes.countDocuments({})` | Cuenta clientes |
| `db.clientes.find({}, { nombre: 1, correo_hash: 1, correo_cifrado: 1, telefono_cifrado: 1, _id: 0 })` | Muestra que el correo útil de búsqueda es el hash y que correo y teléfono están cifrados |
| Conteo de las seis colecciones | Imprime `clientes`, `productos`, `pedidos`, `pagos`, `inventario` y `auditoria` con su `countDocuments` |

Con el sembrado y el cliente de `main.py`, el conjunto que usan el resto de consultas es: el cliente Juan, 20 clientes semilla, `LAP-001`, 25 productos `PROD-*`, el pedido de la laptop de prueba, 20 pedidos semilla, 20 pagos semilla, inventario de los productos existentes y 15 eventos de auditoría.

### Índices y `explain`

En la base hay 10 índices de la práctica, aparte del `_id` automático de cada colección. La comprobación los busca por nombre. No hay en la carpeta la salida del `explain` (plan, llaves examinadas ni documentos examinados), así que aquí queda la consulta mongosh equivalente y qué índice debería usar.

| # | Colección | Nombre del índice |
| --- | --- | --- |
| 1 | `clientes` | `idx_cliente_correo_hash_unico` |
| 2 | `productos` | `idx_producto_sku_unico` |
| 3 | `productos` | `idx_producto_texto` |
| 4 | `productos` | `idx_producto_categoria_precio` |
| 5 | `productos` | `idx_producto_precio_activo` |
| 6 | `pedidos` | `idx_pedido_cliente_fecha` |
| 7 | `pagos` | `idx_pago_referencia_unica` |
| 8 | `pagos` | `idx_pago_pedido_id` |
| 9 | `inventario` | `idx_inventario_producto_unico` |
| 10 | `auditoria` | `idx_auditoria_coleccion_fecha` |

Listar índices de una colección:

```javascript
db.productos.getIndexes()
```

Cinco `explain("executionStats")`. MongoDB elige el plan; no se fuerza índice con `hint()`. Un plan con etapa `IXSCAN` usó índice. `COLLSCAN` recorrió la colección.

```javascript
db.productos.find({ sku: "<sku existente>" }).explain("executionStats")
db.productos.find({ categoria: "<categoria existente>" }).sort({ precio: 1 }).explain("executionStats")
db.pedidos.find({ cliente_id: ObjectId("<id existente>") }).sort({ fecha_pedido: -1 }).explain("executionStats")
db.pagos.find({ referencia: "<referencia existente>" }).explain("executionStats")
db.inventario.find({ producto_id: ObjectId("<id existente>") }).explain("executionStats")
```

1. Producto por SKU. Apunta a `idx_producto_sku_unico`.
2. Productos de una categoría ordenados por precio. Apunta a `idx_producto_categoria_precio`.
3. Pedidos de un cliente, del más reciente al más antiguo. Apunta a `idx_pedido_cliente_fecha`.
4. Pago por referencia. Apunta a `idx_pago_referencia_unica`.
5. Inventario de un producto. Apunta a `idx_inventario_producto_unico`.

La salida útil de cada `explain` es `executionStats.nReturned`, `totalKeysExamined` y `totalDocsExamined`, más las etapas del `winningPlan`.

### Vistas

Cinco vistas. Si el nombre ya existe, no se vuelve a crear. No hay en la carpeta un volcado de documentos de estas vistas; el contenido se deduce del pipeline y de los datos de las colecciones fuente.

```javascript
db.createView("vista_productos_activos", "productos", [
  { $match: { activo: true } },
  { $project: { _id: 1, sku: 1, nombre: 1, categoria: 1, precio: 1, moneda: 1 } }
])
```

Catálogo activo, sin proveedor ni descripción. Con los datos de la práctica todos los productos están activos, así que la vista muestra `LAP-001` y `PROD-001` … `PROD-025`.

```javascript
db.createView("vista_inventario_disponible", "inventario", [
  { $lookup: {
      from: "productos",
      localField: "producto_id",
      foreignField: "_id",
      as: "producto"
  }},
  { $unwind: { path: "$producto", preserveNullAndEmptyArrays: true } },
  { $project: {
      _id: 0,
      producto_id: 1,
      sku: "$producto.sku",
      nombre: "$producto.nombre",
      almacen: 1,
      existencias: 1,
      reservadas: 1,
      stock_minimo: 1,
      disponibles: { $subtract: ["$existencias", "$reservadas"] }
  }}
])
```

Cada fila de inventario queda con el SKU y el nombre del producto, y con `disponibles = existencias - reservadas`. Los mismos pares nombre/disponibles salen en la consulta LOOKUP 15.

```javascript
db.createView("vista_resumen_pedidos", "pedidos", [
  { $project: {
      _id: 1,
      cliente_id: 1,
      fecha_pedido: 1,
      estado: 1,
      cantidad_renglones: { $size: { $ifNull: ["$productos", []] } },
      subtotal: 1,
      impuestos: 1,
      costo_envio: 1,
      total: 1,
      estado_envio: "$envio.estado"
  }}
])
```

Un renglón por pedido, con cuántos productos trae y el estado del envío, sin el arreglo completo.

```javascript
db.createView("vista_pagos_pedidos", "pagos", [
  { $lookup: {
      from: "pedidos",
      localField: "pedido_id",
      foreignField: "_id",
      as: "pedido"
  }},
  { $unwind: { path: "$pedido", preserveNullAndEmptyArrays: true } },
  { $project: {
      _id: 1,
      pedido_id: 1,
      referencia: 1,
      metodo: 1,
      monto: 1,
      moneda: 1,
      estado_pago: "$estado",
      fecha_pago: 1,
      estado_pedido: "$pedido.estado"
  }}
])
```

Cada pago junto al estado de su pedido. En los datos sembrados el estado del pago y el del pedido son `Pendiente`. El pedido de prueba de 12700 no entra porque no tiene pago.

```javascript
db.createView("vista_movimientos_auditoria", "auditoria", [
  { $project: {
      _id: 1, usuario: 1, accion: 1, coleccion: 1, documento_id: 1, fecha: 1
  }}
])
```

Bitácora sin `datos_anteriores` ni `datos_nuevos`. Los 15 eventos semilla son `INSERT` del usuario `seed_script` sobre `pedidos`.

Para leer una vista se consulta como colección, por ejemplo `db.vista_productos_activos.find()`.

### Triggers de Atlas

Cinco Database Triggers del cluster, uno por función. No se ejecutan dentro de mongosh: se pegan en el editor Function de Atlas (Watch Against: Collection, Event Type: Function, preimagen del documento desactivada). Solo escriben en el log. No modifican colecciones. El archivo no incluye las capturas de esos logs.

| Trigger | Colección | Operación | Qué registra si se dispara |
| --- | --- | --- | --- |
| `trg_nuevo_pedido` | `pedidos` | Insert | Id del pedido, estado y total. Exige documento completo |
| `trg_cambio_estado_pedido` | `pedidos` | Update | Solo si cambió `estado`: id y el estado nuevo |
| `trg_nuevo_pago` | `pagos` | Insert | Id del pago, referencia y estado. Exige documento completo |
| `trg_cambio_inventario` | `inventario` | Update | Si cambió `existencias`, `reservadas` o `stock_minimo`: id, campos y valores nuevos |
| `trg_cambio_producto` | `productos` | Update | Si cambió `nombre`, `precio`, `categoria` o `activo`: id, campos y valores nuevos |

---

## Expresiones regulares

Archivo de salida: `regex y resultados.txt`. Fecha de la captura: 2026-11-26T02:27:33.096Z. Veinte consultas, cero errores, diecisiete con al menos un documento. Proyección de productos: `_id`, `sku`, `nombre`, `categoria`, `precio`, `activo`. Proyección de clientes: `_id`, `nombre`, `apellidos`, `activo`. La opción `"i"` no distingue mayúsculas.

### REGEX 01 — Productos cuyo nombre inicia con A

```javascript
db.productos.find(
  { nombre: { $regex: "^A", $options: "i" } },
  { _id: 1, sku: 1, nombre: 1, categoria: 1, precio: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 1.

| SKU | Nombre | Categoría | Precio | Activo |
| --- | --- | --- | --- | --- |
| PROD-005 | Audifonos Bluetooth | Electronica | 850.00 | true |

### REGEX 02 — Productos cuyo nombre inicia con C

```javascript
db.productos.find(
  { nombre: { $regex: "^C", $options: "i" } },
  { _id: 1, sku: 1, nombre: 1, categoria: 1, precio: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 1.

| SKU | Nombre | Categoría | Precio | Activo |
| --- | --- | --- | --- | --- |
| PROD-010 | Cargador USB-C | Electronica | 350.00 | true |

### REGEX 03 — Productos cuyo nombre contiene a

```javascript
db.productos.find(
  { nombre: { $regex: "a", $options: "i" } },
  { _id: 1, sku: 1, nombre: 1, categoria: 1, precio: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 10 (hay más en la colección; el `limit` corta la respuesta).

| SKU | Nombre | Categoría | Precio | Activo |
| --- | --- | --- | --- | --- |
| LAP-001 | Laptop Lenovo IdeaPad | Electronica | 12500.00 | true |
| PROD-001 | Laptop Lenovo IdeaPad | Electronica | 12500.00 | true |
| PROD-003 | Teclado Mecanico | Electronica | 1200.00 | true |
| PROD-004 | Monitor Samsung 24 | Electronica | 3200.00 | true |
| PROD-005 | Audifonos Bluetooth | Electronica | 850.00 | true |
| PROD-006 | Memoria USB 64GB | Electronica | 180.00 | true |
| PROD-008 | Webcam Full HD | Electronica | 680.00 | true |
| PROD-009 | Bocina Bluetooth | Electronica | 950.00 | true |
| PROD-010 | Cargador USB-C | Electronica | 350.00 | true |
| PROD-011 | Playera Deportiva | Ropa | 299.00 | true |

### REGEX 04 — Productos cuyo nombre contiene e

```javascript
db.productos.find(
  { nombre: { $regex: "e", $options: "i" } },
  { _id: 1, sku: 1, nombre: 1, categoria: 1, precio: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 10.

| SKU | Nombre | Categoría | Precio | Activo |
| --- | --- | --- | --- | --- |
| LAP-001 | Laptop Lenovo IdeaPad | Electronica | 12500.00 | true |
| PROD-001 | Laptop Lenovo IdeaPad | Electronica | 12500.00 | true |
| PROD-002 | Mouse Logitech | Electronica | 450.00 | true |
| PROD-003 | Teclado Mecanico | Electronica | 1200.00 | true |
| PROD-005 | Audifonos Bluetooth | Electronica | 850.00 | true |
| PROD-006 | Memoria USB 64GB | Electronica | 180.00 | true |
| PROD-008 | Webcam Full HD | Electronica | 680.00 | true |
| PROD-009 | Bocina Bluetooth | Electronica | 950.00 | true |
| PROD-011 | Playera Deportiva | Ropa | 299.00 | true |
| PROD-012 | Sudadera | Ropa | 650.00 | true |

### REGEX 05 — Productos cuyo nombre termina con o

```javascript
db.productos.find(
  { nombre: { $regex: "o$", $options: "i" } },
  { _id: 1, sku: 1, nombre: 1, categoria: 1, precio: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 3. El `$` ancla el final del texto.

| SKU | Nombre | Categoría | Precio | Activo |
| --- | --- | --- | --- | --- |
| PROD-003 | Teclado Mecanico | Electronica | 1200.00 | true |
| PROD-019 | Lampara de Escritorio | Hogar | 550.00 | true |
| PROD-021 | Organizador de Escritorio | Hogar | 320.00 | true |

### REGEX 06 — Productos con SKU que inicia con LAP

```javascript
db.productos.find(
  { sku: { $regex: "^LAP" } },
  { _id: 1, sku: 1, nombre: 1, categoria: 1, precio: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 1. Sin `$options`, así que distingue mayúsculas. Solo sobrevivió el insert válido.

| SKU | Nombre | Categoría | Precio | Activo |
| --- | --- | --- | --- | --- |
| LAP-001 | Laptop Lenovo IdeaPad | Electronica | 12500.00 | true |

### REGEX 07 — Productos con SKU que contiene guion

```javascript
db.productos.find(
  { sku: { $regex: "-" } },
  { _id: 1, sku: 1, nombre: 1, categoria: 1, precio: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 10. Todos los SKU de la práctica llevan guion (`LAP-001`, `PROD-00N`); el límite deja fuera del ejemplo a partir de `PROD-010`.

| SKU | Nombre | Categoría | Precio | Activo |
| --- | --- | --- | --- | --- |
| LAP-001 | Laptop Lenovo IdeaPad | Electronica | 12500.00 | true |
| PROD-001 | Laptop Lenovo IdeaPad | Electronica | 12500.00 | true |
| PROD-002 | Mouse Logitech | Electronica | 450.00 | true |
| PROD-003 | Teclado Mecanico | Electronica | 1200.00 | true |
| PROD-004 | Monitor Samsung 24 | Electronica | 3200.00 | true |
| PROD-005 | Audifonos Bluetooth | Electronica | 850.00 | true |
| PROD-006 | Memoria USB 64GB | Electronica | 180.00 | true |
| PROD-007 | Disco SSD 1TB | Electronica | 1450.00 | true |
| PROD-008 | Webcam Full HD | Electronica | 680.00 | true |
| PROD-009 | Bocina Bluetooth | Electronica | 950.00 | true |

### REGEX 08 — Productos con SKU que termina en cifra

```javascript
db.productos.find(
  { sku: { $regex: "[0-9]$" } },
  { _id: 1, sku: 1, nombre: 1, categoria: 1, precio: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 10. Misma muestra que REGEX 07 porque todos los SKU visibles terminan en dígito.

| SKU | Nombre | Categoría | Precio | Activo |
| --- | --- | --- | --- | --- |
| LAP-001 | Laptop Lenovo IdeaPad | Electronica | 12500.00 | true |
| PROD-001 | Laptop Lenovo IdeaPad | Electronica | 12500.00 | true |
| PROD-002 | Mouse Logitech | Electronica | 450.00 | true |
| PROD-003 | Teclado Mecanico | Electronica | 1200.00 | true |
| PROD-004 | Monitor Samsung 24 | Electronica | 3200.00 | true |
| PROD-005 | Audifonos Bluetooth | Electronica | 850.00 | true |
| PROD-006 | Memoria USB 64GB | Electronica | 180.00 | true |
| PROD-007 | Disco SSD 1TB | Electronica | 1450.00 | true |
| PROD-008 | Webcam Full HD | Electronica | 680.00 | true |
| PROD-009 | Bocina Bluetooth | Electronica | 950.00 | true |

### REGEX 09 — Categorías que comienzan por vocal

```javascript
db.productos.find(
  { categoria: { $regex: "^[AEIOU]", $options: "i" } },
  { _id: 1, sku: 1, nombre: 1, categoria: 1, precio: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 10. Entran `Accesorios` y `Electronica`. `Ropa`, `Hogar` y `Deportes` no. El orden de la respuesta no es el del SKU.

| SKU | Nombre | Categoría | Precio | Activo |
| --- | --- | --- | --- | --- |
| PROD-015 | Gorra | Accesorios | 250.00 | true |
| PROD-017 | Botella Termica | Accesorios | 390.00 | true |
| PROD-016 | Mochila Escolar | Accesorios | 780.00 | true |
| PROD-018 | Reloj Digital | Accesorios | 1100.00 | true |
| PROD-006 | Memoria USB 64GB | Electronica | 180.00 | true |
| PROD-010 | Cargador USB-C | Electronica | 350.00 | true |
| PROD-002 | Mouse Logitech | Electronica | 450.00 | true |
| PROD-008 | Webcam Full HD | Electronica | 680.00 | true |
| PROD-005 | Audifonos Bluetooth | Electronica | 850.00 | true |
| PROD-009 | Bocina Bluetooth | Electronica | 950.00 | true |

### REGEX 10 — Categorías cuyo nombre contiene a

```javascript
db.productos.find(
  { categoria: { $regex: "a", $options: "i" } },
  { _id: 1, sku: 1, nombre: 1, categoria: 1, precio: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 10. En esta muestra coinciden con REGEX 09: `Accesorios` y `Electronica` contienen «a». `Ropa` también la contiene y queda fuera de estas 10 filas por el límite.

| SKU | Nombre | Categoría | Precio | Activo |
| --- | --- | --- | --- | --- |
| PROD-015 | Gorra | Accesorios | 250.00 | true |
| PROD-017 | Botella Termica | Accesorios | 390.00 | true |
| PROD-016 | Mochila Escolar | Accesorios | 780.00 | true |
| PROD-018 | Reloj Digital | Accesorios | 1100.00 | true |
| PROD-006 | Memoria USB 64GB | Electronica | 180.00 | true |
| PROD-010 | Cargador USB-C | Electronica | 350.00 | true |
| PROD-002 | Mouse Logitech | Electronica | 450.00 | true |
| PROD-008 | Webcam Full HD | Electronica | 680.00 | true |
| PROD-005 | Audifonos Bluetooth | Electronica | 850.00 | true |
| PROD-009 | Bocina Bluetooth | Electronica | 950.00 | true |

### REGEX 11 — Productos cuyo proveedor contiene a

```javascript
db.productos.find(
  { "proveedor.nombre": { $regex: "a", $options: "i" } },
  { _id: 1, sku: 1, nombre: 1, categoria: 1, precio: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 10. `Distribuidora Tecnologia MX` y `Distribuidora Comercial MX` contienen «a», así que el filtro abarca el catálogo. El límite devuelve los diez primeros.

| SKU | Nombre | Categoría | Precio | Activo |
| --- | --- | --- | --- | --- |
| LAP-001 | Laptop Lenovo IdeaPad | Electronica | 12500.00 | true |
| PROD-001 | Laptop Lenovo IdeaPad | Electronica | 12500.00 | true |
| PROD-002 | Mouse Logitech | Electronica | 450.00 | true |
| PROD-003 | Teclado Mecanico | Electronica | 1200.00 | true |
| PROD-004 | Monitor Samsung 24 | Electronica | 3200.00 | true |
| PROD-005 | Audifonos Bluetooth | Electronica | 850.00 | true |
| PROD-006 | Memoria USB 64GB | Electronica | 180.00 | true |
| PROD-007 | Disco SSD 1TB | Electronica | 1450.00 | true |
| PROD-008 | Webcam Full HD | Electronica | 680.00 | true |
| PROD-009 | Bocina Bluetooth | Electronica | 950.00 | true |

### REGEX 12 — Productos cuya descripción contiene e

```javascript
db.productos.find(
  { descripcion: { $regex: "e", $options: "i" } },
  { _id: 1, sku: 1, nombre: 1, categoria: 1, precio: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 10. La descripción de `LAP-001` es «Laptop de 16 GB RAM y 512 GB SSD». La de los `PROD-*` es «Producto de categoria …». Ambas contienen «e».

| SKU | Nombre | Categoría | Precio | Activo |
| --- | --- | --- | --- | --- |
| LAP-001 | Laptop Lenovo IdeaPad | Electronica | 12500.00 | true |
| PROD-001 | Laptop Lenovo IdeaPad | Electronica | 12500.00 | true |
| PROD-002 | Mouse Logitech | Electronica | 450.00 | true |
| PROD-003 | Teclado Mecanico | Electronica | 1200.00 | true |
| PROD-004 | Monitor Samsung 24 | Electronica | 3200.00 | true |
| PROD-005 | Audifonos Bluetooth | Electronica | 850.00 | true |
| PROD-006 | Memoria USB 64GB | Electronica | 180.00 | true |
| PROD-007 | Disco SSD 1TB | Electronica | 1450.00 | true |
| PROD-008 | Webcam Full HD | Electronica | 680.00 | true |
| PROD-009 | Bocina Bluetooth | Electronica | 950.00 | true |

### REGEX 13 — Clientes cuyo nombre empieza con A

```javascript
db.clientes.find(
  { nombre: { $regex: "^A", $options: "i" } },
  { _id: 1, nombre: 1, apellidos: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 0. Resultado: `[]`. Ningún cliente sembrado ni Juan tienen nombre que empiece con A.

### REGEX 14 — Clientes con nombre que contiene e

```javascript
db.clientes.find(
  { nombre: { $regex: "e", $options: "i" } },
  { _id: 1, nombre: 1, apellidos: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 10. Todos activos.

| Nombre | Apellidos | Activo |
| --- | --- | --- |
| Genaro | Maya Sandoval | true |
| Federico | Rascón Alba | true |
| Dolores | Valle Roque | true |
| Esther | Elizondo Pizarro | true |
| Emilio | Farías Gutiérrez | true |
| Guillermo | Zamora Santana | true |
| Diego | Ávalos Montenegro | true |
| Nelly | Solís Fonseca | true |
| Ilse | Almonte Ceballos | true |
| Esteban | Rentería Menéndez | true |

### REGEX 15 — Clientes con apellidos que empiezan con M

```javascript
db.clientes.find(
  { apellidos: { $regex: "^M", $options: "i" } },
  { _id: 1, nombre: 1, apellidos: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 1.

| Nombre | Apellidos | Activo |
| --- | --- | --- |
| Genaro | Maya Sandoval | true |

### REGEX 16 — Clientes con apellido que contiene a

```javascript
db.clientes.find(
  { apellidos: { $regex: "a", $options: "i" } },
  { _id: 1, nombre: 1, apellidos: 1, activo: 1 }
).limit(10)
```

Estado: OK. Muestras: 10.

| Nombre | Apellidos | Activo |
| --- | --- | --- |
| Genaro | Maya Sandoval | true |
| Federico | Rascón Alba | true |
| Horacio | Vélez Mares | true |
| Dolores | Valle Roque | true |
| Rosalia | Reyes Rodarte | true |
| Fabiola | Solorzano Saiz | true |
| Esther | Elizondo Pizarro | true |
| Emilio | Farías Gutiérrez | true |
| Guillermo | Zamora Santana | true |
| Diego | Ávalos Montenegro | true |

### REGEX 17 — Pedidos con estado que contiene a

```javascript
db.pedidos.find(
  { estado: { $regex: "a", $options: "i" } },
  { _id: 1, estado: 1, fecha_pedido: 1, total: 1 }
).limit(10)
```

Estado: OK. Muestras: 0. Resultado: `[]`. Todos los pedidos capturados están en `Pendiente`, y esa palabra no contiene «a».

### REGEX 18 — Pedidos con estado que empieza por p

```javascript
db.pedidos.find(
  { estado: { $regex: "^p", $options: "i" } },
  { _id: 1, estado: 1, fecha_pedido: 1, total: 1 }
).limit(10)
```

Estado: OK. Muestras: 10. El primero es el pedido de prueba de la laptop (19 de noviembre de 2026, total 12700). Los siguientes son semilla, un día aparte desde el 1 de noviembre, todos `Pendiente`.

| Fecha | Total | Estado |
| --- | --- | --- |
| 2026-11-19T04:45:49.536Z | 12700.00 | Pendiente |
| 2026-11-01T00:00:00Z | 15276.40 | Pendiente |
| 2026-11-02T00:00:00Z | 4558.00 | Pendiente |
| 2026-11-03T00:00:00Z | 4511.60 | Pendiente |
| 2026-11-04T00:00:00Z | 6066.00 | Pendiente |
| 2026-11-05T00:00:00Z | 4326.00 | Pendiente |
| 2026-11-06T00:00:00Z | 914.44 | Pendiente |
| 2026-11-07T00:00:00Z | 5776.00 | Pendiente |
| 2026-11-08T00:00:00Z | 4370.08 | Pendiente |
| 2026-11-09T00:00:00Z | 7052.00 | Pendiente |

### REGEX 19 — Pagos con referencia que contiene guion

```javascript
db.pagos.find(
  { referencia: { $regex: "-" } },
  { _id: 1, referencia: 1, metodo: 1, estado: 1, monto: 1 }
).limit(10)
```

Estado: OK. Muestras: 10. Las referencias `SEED-PAGO-00N` siempre llevan guion. No aparece un pago del pedido de 12700.

| Referencia | Método | Monto | Estado |
| --- | --- | --- | --- |
| SEED-PAGO-001 | Tarjeta | 15276.40 | Pendiente |
| SEED-PAGO-002 | Efectivo | 4558.00 | Pendiente |
| SEED-PAGO-003 | Efectivo | 4511.60 | Pendiente |
| SEED-PAGO-004 | Transferencia | 6066.00 | Pendiente |
| SEED-PAGO-005 | Efectivo | 4326.00 | Pendiente |
| SEED-PAGO-006 | Transferencia | 914.44 | Pendiente |
| SEED-PAGO-007 | Efectivo | 5776.00 | Pendiente |
| SEED-PAGO-008 | Efectivo | 4370.08 | Pendiente |
| SEED-PAGO-009 | Transferencia | 7052.00 | Pendiente |
| SEED-PAGO-010 | Efectivo | 1542.00 | Pendiente |

### REGEX 20 — Auditoría con acción que contiene a

```javascript
db.auditoria.find(
  { accion: { $regex: "a", $options: "i" } },
  { _id: 1, usuario: 1, accion: 1, coleccion: 1 }
).limit(10)
```

Estado: OK. Muestras: 0. Resultado: `[]`. Los eventos sembrados usan la acción `INSERT`, que no contiene «a». `UPDATE` tampoco entraría. `DELETE` no está en estos datos.

**Cierre de la captura:** `TOTAL REGEX: 20; ERRORES: 0; CONSULTAS CON MUESTRAS: 17`.

---

## `$lookup`

Archivo de salida: `lookup y resultados.txt`. Fecha de la captura: 2026-11-26T02:31:11.752Z. Veinte agregaciones, cero errores, las veinte con muestras. `$lookup` arma un arreglo con los documentos de la otra colección cuyo campo foráneo coincide. `$size` cuenta ese arreglo. El `$limit: 10` va al final del pipeline, así que son los 10 primeros documentos de la colección de origen después del cruce, no un total de la base.

### LOOKUP 01 — Pedidos con el cliente asociado

```javascript
db.pedidos.aggregate([
  { $lookup: {
      from: "clientes",
      localField: "cliente_id",
      foreignField: "_id",
      as: "cliente"
  }},
  { $project: { estado: 1, total: 1, "cliente.nombre": 1, "cliente.apellidos": 1 } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. Cada pedido encuentra exactamente un cliente.

| Total | Estado | Cliente |
| --- | --- | --- |
| 12700.00 | Pendiente | Juan Perez Lopez |
| 15276.40 | Pendiente | Genaro Maya Sandoval |
| 4558.00 | Pendiente | Federico Rascón Alba |
| 4511.60 | Pendiente | Horacio Vélez Mares |
| 6066.00 | Pendiente | Dolores Valle Roque |
| 4326.00 | Pendiente | Rosalia Reyes Rodarte |
| 914.44 | Pendiente | Fabiola Solorzano Saiz |
| 5776.00 | Pendiente | Esther Elizondo Pizarro |
| 4370.08 | Pendiente | Emilio Farías Gutiérrez |
| 7052.00 | Pendiente | Guillermo Zamora Santana |

### LOOKUP 02 — Pedidos con el nombre del cliente

```javascript
db.pedidos.aggregate([
  { $lookup: {
      from: "clientes",
      localField: "cliente_id",
      foreignField: "_id",
      as: "cliente"
  }},
  { $project: { fecha_pedido: 1, "cliente.nombre": 1, estado: 1 } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. Misma relación, proyectando solo el nombre y la fecha.

| Fecha | Estado | Nombre |
| --- | --- | --- |
| 2026-11-19T04:45:49.536Z | Pendiente | Juan |
| 2026-11-01T00:00:00Z | Pendiente | Genaro |
| 2026-11-02T00:00:00Z | Pendiente | Federico |
| 2026-11-03T00:00:00Z | Pendiente | Horacio |
| 2026-11-04T00:00:00Z | Pendiente | Dolores |
| 2026-11-05T00:00:00Z | Pendiente | Rosalia |
| 2026-11-06T00:00:00Z | Pendiente | Fabiola |
| 2026-11-07T00:00:00Z | Pendiente | Esther |
| 2026-11-08T00:00:00Z | Pendiente | Emilio |
| 2026-11-09T00:00:00Z | Pendiente | Guillermo |

### LOOKUP 03 — Cuántos clientes coinciden con cada pedido

```javascript
db.pedidos.aggregate([
  { $lookup: {
      from: "clientes",
      localField: "cliente_id",
      foreignField: "_id",
      as: "cliente"
  }},
  { $project: { estado: 1, clientes_encontrados: { $size: "$cliente" } } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. Los diez pedidos quedan en `Pendiente` con `clientes_encontrados: 1`. No hay pedidos huérfanos en esta muestra.

### LOOKUP 04 — Pedidos con el indicador activo del cliente

```javascript
db.pedidos.aggregate([
  { $lookup: {
      from: "clientes",
      localField: "cliente_id",
      foreignField: "_id",
      as: "cliente"
  }},
  { $project: { estado: 1, "cliente.activo": 1 } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. En los diez, `cliente.activo` es `true` y el pedido está `Pendiente`.

### LOOKUP 05 — Pedidos con la ciudad del cliente

```javascript
db.pedidos.aggregate([
  { $lookup: {
      from: "clientes",
      localField: "cliente_id",
      foreignField: "_id",
      as: "cliente"
  }},
  { $project: { estado: 1, "cliente.direcciones.ciudad": 1 } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. Los diez clientes tienen una sola dirección y la ciudad es Guadalajara. El pedido sigue en `Pendiente`.

### LOOKUP 06 — Pagos con el pedido correspondiente

```javascript
db.pagos.aggregate([
  { $lookup: {
      from: "pedidos",
      localField: "pedido_id",
      foreignField: "_id",
      as: "pedido"
  }},
  { $project: { referencia: 1, monto: 1, "pedido.estado": 1 } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. El monto del pago coincide con el total del pedido semilla y el pedido está `Pendiente`.

| Referencia | Monto | Estado del pedido |
| --- | --- | --- |
| SEED-PAGO-001 | 15276.40 | Pendiente |
| SEED-PAGO-002 | 4558.00 | Pendiente |
| SEED-PAGO-003 | 4511.60 | Pendiente |
| SEED-PAGO-004 | 6066.00 | Pendiente |
| SEED-PAGO-005 | 4326.00 | Pendiente |
| SEED-PAGO-006 | 914.44 | Pendiente |
| SEED-PAGO-007 | 5776.00 | Pendiente |
| SEED-PAGO-008 | 4370.08 | Pendiente |
| SEED-PAGO-009 | 7052.00 | Pendiente |
| SEED-PAGO-010 | 1542.00 | Pendiente |

### LOOKUP 07 — Pagos con el total del pedido

```javascript
db.pagos.aggregate([
  { $lookup: {
      from: "pedidos",
      localField: "pedido_id",
      foreignField: "_id",
      as: "pedido"
  }},
  { $project: { referencia: 1, "pedido.total": 1 } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. El total embebido repite el monto de LOOKUP 06: 15276.40, 4558.00, 4511.60, 6066.00, 4326.00, 914.44, 5776.00, 4370.08, 7052.00 y 1542.00, en ese orden de referencias `SEED-PAGO-001` a `SEED-PAGO-010`.

### LOOKUP 08 — Pagos con la fecha del pedido

```javascript
db.pagos.aggregate([
  { $lookup: {
      from: "pedidos",
      localField: "pedido_id",
      foreignField: "_id",
      as: "pedido"
  }},
  { $project: { referencia: 1, fecha_pago: 1, "pedido.fecha_pedido": 1 } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. En el sembrado la fecha de pago se copió de la fecha del pedido, y aquí salen iguales.

| Referencia | Fecha de pago | Fecha del pedido |
| --- | --- | --- |
| SEED-PAGO-001 | 2026-11-01 | 2026-11-01 |
| SEED-PAGO-002 | 2026-11-02 | 2026-11-02 |
| SEED-PAGO-003 | 2026-11-03 | 2026-11-03 |
| SEED-PAGO-004 | 2026-11-04 | 2026-11-04 |
| SEED-PAGO-005 | 2026-11-05 | 2026-11-05 |
| SEED-PAGO-006 | 2026-11-06 | 2026-11-06 |
| SEED-PAGO-007 | 2026-11-07 | 2026-11-07 |
| SEED-PAGO-008 | 2026-11-08 | 2026-11-08 |
| SEED-PAGO-009 | 2026-11-09 | 2026-11-09 |
| SEED-PAGO-010 | 2026-11-10 | 2026-11-10 |

### LOOKUP 09 — Cuántos pedidos coinciden con cada pago

```javascript
db.pagos.aggregate([
  { $lookup: {
      from: "pedidos",
      localField: "pedido_id",
      foreignField: "_id",
      as: "pedido"
  }},
  { $project: { referencia: 1, coincidencias: { $size: "$pedido" } } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. `SEED-PAGO-001` … `SEED-PAGO-010` tienen `coincidencias: 1`.

### LOOKUP 10 — Pagos que sí encontraron pedido

```javascript
db.pagos.aggregate([
  { $lookup: {
      from: "pedidos",
      localField: "pedido_id",
      foreignField: "_id",
      as: "pedido"
  }},
  { $match: { "pedido.0": { $exists: true } } },
  { $project: { referencia: 1, "pedido.estado": 1 } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. `pedido.0` existe cuando el arreglo del lookup no quedó vacío. Los diez pagos semilla pasan el filtro y el estado del pedido es `Pendiente`. Mismas referencias `SEED-PAGO-001` a `SEED-PAGO-010`.

### LOOKUP 11 — Inventario con el nombre del producto

```javascript
db.inventario.aggregate([
  { $lookup: {
      from: "productos",
      localField: "producto_id",
      foreignField: "_id",
      as: "producto"
  }},
  { $project: { almacen: 1, existencias: 1, "producto.nombre": 1 } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. Almacén de todos: Almacen Principal. Hay dos registros de la misma laptop porque `LAP-001` y `PROD-001` son documentos distintos.

| Existencias | Producto |
| --- | --- |
| 30 | Laptop Lenovo IdeaPad |
| 79 | Laptop Lenovo IdeaPad |
| 97 | Mouse Logitech |
| 43 | Teclado Mecanico |
| 94 | Monitor Samsung 24 |
| 68 | Audifonos Bluetooth |
| 85 | Memoria USB 64GB |
| 77 | Disco SSD 1TB |
| 71 | Webcam Full HD |
| 15 | Bocina Bluetooth |

### LOOKUP 12 — Inventario con el SKU

```javascript
db.inventario.aggregate([
  { $lookup: {
      from: "productos",
      localField: "producto_id",
      foreignField: "_id",
      as: "producto"
  }},
  { $project: { almacen: 1, "producto.sku": 1 } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. Almacén Principal en los diez. SKU en orden: `LAP-001`, `PROD-001`, `PROD-002`, `PROD-003`, `PROD-004`, `PROD-005`, `PROD-006`, `PROD-007`, `PROD-008`, `PROD-009`.

### LOOKUP 13 — Inventario con la categoría

```javascript
db.inventario.aggregate([
  { $lookup: {
      from: "productos",
      localField: "producto_id",
      foreignField: "_id",
      as: "producto"
  }},
  { $project: { existencias: 1, "producto.categoria": 1 } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. Esas diez filas son las primeras del inventario y todas son Electrónica. Existencias, en orden: 30, 79, 97, 43, 94, 68, 85, 77, 71, 15.

### LOOKUP 14 — Inventario con el precio

```javascript
db.inventario.aggregate([
  { $lookup: {
      from: "productos",
      localField: "producto_id",
      foreignField: "_id",
      as: "producto"
  }},
  { $project: { existencias: 1, "producto.precio": 1 } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10.

| Existencias | Precio |
| --- | --- |
| 30 | 12500.00 |
| 79 | 12500.00 |
| 97 | 450.00 |
| 43 | 1200.00 |
| 94 | 3200.00 |
| 68 | 850.00 |
| 85 | 180.00 |
| 77 | 1450.00 |
| 71 | 680.00 |
| 15 | 950.00 |

### LOOKUP 15 — Unidades disponibles

```javascript
db.inventario.aggregate([
  { $lookup: {
      from: "productos",
      localField: "producto_id",
      foreignField: "_id",
      as: "producto"
  }},
  { $project: {
      "producto.nombre": 1,
      disponibles: { $subtract: ["$existencias", "$reservadas"] }
  }},
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. `disponibles` resta lo reservado a las existencias.

| Producto | Disponibles |
| --- | --- |
| Laptop Lenovo IdeaPad | 28 |
| Laptop Lenovo IdeaPad | 75 |
| Mouse Logitech | 97 |
| Teclado Mecanico | 39 |
| Monitor Samsung 24 | 90 |
| Audifonos Bluetooth | 64 |
| Memoria USB 64GB | 80 |
| Disco SSD 1TB | 73 |
| Webcam Full HD | 70 |
| Bocina Bluetooth | 11 |

La diferencia contra LOOKUP 11 son las reservadas: 2, 4, 0, 4, 4, 4, 5, 4, 1 y 4.

### LOOKUP 16 — Productos con su inventario

```javascript
db.productos.aggregate([
  { $lookup: {
      from: "inventario",
      localField: "_id",
      foreignField: "producto_id",
      as: "inventarios"
  }},
  { $project: { sku: 1, nombre: 1, "inventarios.almacen": 1, "inventarios.existencias": 1 } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. El cruce va al revés: desde el producto hacia el inventario. Cada uno tiene un solo almacén.

| SKU | Nombre | Almacén | Existencias |
| --- | --- | --- | --- |
| LAP-001 | Laptop Lenovo IdeaPad | Almacen Principal | 30 |
| PROD-001 | Laptop Lenovo IdeaPad | Almacen Principal | 79 |
| PROD-002 | Mouse Logitech | Almacen Principal | 97 |
| PROD-003 | Teclado Mecanico | Almacen Principal | 43 |
| PROD-004 | Monitor Samsung 24 | Almacen Principal | 94 |
| PROD-005 | Audifonos Bluetooth | Almacen Principal | 68 |
| PROD-006 | Memoria USB 64GB | Almacen Principal | 85 |
| PROD-007 | Disco SSD 1TB | Almacen Principal | 77 |
| PROD-008 | Webcam Full HD | Almacen Principal | 71 |
| PROD-009 | Bocina Bluetooth | Almacen Principal | 15 |

### LOOKUP 17 — Cuántos registros de inventario tiene cada producto

```javascript
db.productos.aggregate([
  { $lookup: {
      from: "inventario",
      localField: "_id",
      foreignField: "producto_id",
      as: "inventarios"
  }},
  { $project: { sku: 1, almacenes: { $size: "$inventarios" } } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. `LAP-001` y `PROD-001` … `PROD-009` tienen `almacenes: 1`.

### LOOKUP 18 — Clientes con sus pedidos

```javascript
db.clientes.aggregate([
  { $lookup: {
      from: "pedidos",
      localField: "_id",
      foreignField: "cliente_id",
      as: "pedidos"
  }},
  { $project: { nombre: 1, apellidos: 1, "pedidos.estado": 1 } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. Cada cliente de la muestra tiene un pedido y está `Pendiente`.

| Nombre | Apellidos | Estado del pedido |
| --- | --- | --- |
| Juan | Perez Lopez | Pendiente |
| Genaro | Maya Sandoval | Pendiente |
| Federico | Rascón Alba | Pendiente |
| Horacio | Vélez Mares | Pendiente |
| Dolores | Valle Roque | Pendiente |
| Rosalia | Reyes Rodarte | Pendiente |
| Fabiola | Solorzano Saiz | Pendiente |
| Esther | Elizondo Pizarro | Pendiente |
| Emilio | Farías Gutiérrez | Pendiente |
| Guillermo | Zamora Santana | Pendiente |

### LOOKUP 19 — Cuántos pedidos tiene cada cliente

```javascript
db.clientes.aggregate([
  { $lookup: {
      from: "pedidos",
      localField: "_id",
      foreignField: "cliente_id",
      as: "pedidos"
  }},
  { $project: { nombre: 1, cantidad_pedidos: { $size: "$pedidos" } } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. Juan, Genaro, Federico, Horacio, Dolores, Rosalia, Fabiola, Esther, Emilio y Guillermo tienen `cantidad_pedidos: 1`.

### LOOKUP 20 — Pedidos con los pagos relacionados

```javascript
db.pedidos.aggregate([
  { $lookup: {
      from: "pagos",
      localField: "_id",
      foreignField: "pedido_id",
      as: "pagos"
  }},
  { $project: { estado: 1, total: 1, "pagos.estado": 1, "pagos.referencia": 1 } },
  { $limit: 10 }
])
```

Estado: OK. Muestras: 10. El pedido de prueba (12700) devuelve `pagos: []` porque `pruebas_subdocumetos.py` no inserta el cobro. Del segundo en adelante cada pedido semilla trae su `SEED-PAGO`.

| Total | Estado del pedido | Pago | Estado del pago |
| --- | --- | --- | --- |
| 12700.00 | Pendiente | (ninguno) | |
| 15276.40 | Pendiente | SEED-PAGO-001 | Pendiente |
| 4558.00 | Pendiente | SEED-PAGO-002 | Pendiente |
| 4511.60 | Pendiente | SEED-PAGO-003 | Pendiente |
| 6066.00 | Pendiente | SEED-PAGO-004 | Pendiente |
| 4326.00 | Pendiente | SEED-PAGO-005 | Pendiente |
| 914.44 | Pendiente | SEED-PAGO-006 | Pendiente |
| 5776.00 | Pendiente | SEED-PAGO-007 | Pendiente |
| 4370.08 | Pendiente | SEED-PAGO-008 | Pendiente |
| 7052.00 | Pendiente | SEED-PAGO-009 | Pendiente |

**Cierre de la captura:** `TOTAL LOOKUP: 20; ERRORES: 0; CONSULTAS CON MUESTRAS: 20`.

---

## Agregaciones y `$switch`

Treinta pipelines de solo lectura sobre `ecommerce_nosql`. En la carpeta está la definición de cada consulta. No está el archivo de resultados de esa corrida (`RESULTADOS_30_AGGREGATE.txt` no vino en los archivos), así que abajo queda la consulta y qué calcula. El tope de muestra de esa corrida, cuando se ejecutó, era 10 documentos.

```javascript
db.productos.aggregate([
  { $group: { _id: "$categoria", cantidad: { $sum: 1 } } },
  { $sort: { cantidad: -1 } }
])
```

**AGGREGATE 01 — Productos por categoría.** Cuenta documentos por `categoria`.

```javascript
db.productos.aggregate([
  { $group: { _id: "$activo", cantidad: { $sum: 1 } } }
])
```

**AGGREGATE 02 — Activos e inactivos.** Cuenta productos según el booleano `activo`.

```javascript
db.productos.aggregate([
  { $group: { _id: "$categoria", precio_promedio: { $avg: "$precio" } } }
])
```

**AGGREGATE 03 — Precio promedio por categoría.**

```javascript
db.productos.aggregate([
  { $group: {
      _id: "$categoria",
      minimo: { $min: "$precio" },
      maximo: { $max: "$precio" }
  }}
])
```

**AGGREGATE 04 — Precio mínimo y máximo por categoría.**

```javascript
db.productos.aggregate([
  { $sort: { precio: -1 } },
  { $project: { sku: 1, nombre: 1, precio: 1 } }
])
```

**AGGREGATE 05 — Productos más caros.** Orden descendente por precio.

```javascript
db.productos.aggregate([
  { $sort: { precio: 1 } },
  { $project: { sku: 1, nombre: 1, precio: 1 } }
])
```

**AGGREGATE 06 — Productos más económicos.** Orden ascendente por precio.

```javascript
db.productos.aggregate([
  { $group: { _id: "$proveedor.nombre", cantidad: { $sum: 1 } } },
  { $sort: { cantidad: -1 } }
])
```

**AGGREGATE 07 — Productos por proveedor.** Agrupa por `proveedor.nombre`.

```javascript
db.productos.aggregate([
  { $group: { _id: "$moneda", cantidad: { $sum: 1 } } }
])
```

**AGGREGATE 08 — Productos por moneda.** Con el validador, la única moneda es `MXN`.

```javascript
db.inventario.aggregate([
  { $group: { _id: "$almacen", existencias_totales: { $sum: "$existencias" } } }
])
```

**AGGREGATE 09 — Existencias totales por almacén.**

```javascript
db.inventario.aggregate([
  { $group: { _id: "$almacen", reservadas_totales: { $sum: "$reservadas" } } }
])
```

**AGGREGATE 10 — Unidades reservadas por almacén.**

```javascript
db.inventario.aggregate([
  { $project: {
      almacen: 1,
      disponibles: { $subtract: ["$existencias", "$reservadas"] }
  }},
  { $group: { _id: "$almacen", disponibles: { $sum: "$disponibles" } } }
])
```

**AGGREGATE 11 — Disponibles por almacén.** Primero resta reservadas a existencias en cada fila y luego suma por almacén.

```javascript
db.inventario.aggregate([
  { $match: { $expr: { $lt: ["$existencias", "$stock_minimo"] } } },
  { $project: { producto_id: 1, almacen: 1, existencias: 1, stock_minimo: 1 } }
])
```

**AGGREGATE 12 — Inventario bajo el mínimo.** `$expr` compara dos campos del mismo documento. El stock mínimo sembrado es 10 y las existencias parten de 15, así que un almacén recién sembrado no entra.

```javascript
db.inventario.aggregate([
  { $sort: { reservadas: -1 } },
  { $project: { producto_id: 1, reservadas: 1, existencias: 1 } }
])
```

**AGGREGATE 13 — Inventario ordenado por reservas.** De más unidades apartadas a menos.

```javascript
db.pedidos.aggregate([
  { $group: { _id: "$estado", cantidad: { $sum: 1 } } }
])
```

**AGGREGATE 14 — Pedidos por estado.**

```javascript
db.pedidos.aggregate([
  { $group: { _id: "$estado", monto: { $sum: "$total" } } }
])
```

**AGGREGATE 15 — Monto total de pedidos por estado.**

```javascript
db.pedidos.aggregate([
  { $group: { _id: "$estado", promedio: { $avg: "$total" } } }
])
```

**AGGREGATE 16 — Ticket promedio por estado.**

```javascript
db.pedidos.aggregate([
  { $group: {
      _id: { $dateToString: { format: "%Y-%m", date: "$fecha_pedido" } },
      cantidad: { $sum: 1 }
  }},
  { $sort: { _id: 1 } }
])
```

**AGGREGATE 17 — Pedidos por mes.** La clave es `año-mes` de `fecha_pedido`. En estos datos cae en `2026-11`.

```javascript
db.pedidos.aggregate([
  { $project: {
      estado: 1,
      lineas: { $size: "$productos" },
      total: 1
  }}
])
```

**AGGREGATE 18 — Renglones por pedido.** `lineas` es el tamaño del arreglo `productos`. El pedido de prueba tiene 1. Los de semilla tienen 2.

```javascript
db.pedidos.aggregate([
  { $unwind: "$productos" },
  { $group: {
      _id: "$productos.sku",
      unidades: { $sum: "$productos.cantidad" }
  }},
  { $sort: { unidades: -1 } }
])
```

**AGGREGATE 19 — Unidades vendidas por SKU.** `$unwind` deja un documento por renglón y luego suma `cantidad`.

```javascript
db.pedidos.aggregate([
  { $unwind: "$productos" },
  { $group: {
      _id: "$productos.sku",
      subtotal_acumulado: { $sum: "$productos.subtotal" }
  }}
])
```

**AGGREGATE 20 — Ingreso de renglones por SKU.** Suma el subtotal de cada línea, sin impuesto ni envío.

```javascript
db.pagos.aggregate([
  { $group: { _id: "$metodo", cantidad: { $sum: 1 } } }
])
```

**AGGREGATE 21 — Pagos por método.** Tarjeta, Transferencia o Efectivo.

```javascript
db.pagos.aggregate([
  { $group: { _id: "$estado", cantidad: { $sum: 1 } } }
])
```

**AGGREGATE 22 — Pagos por estado.**

```javascript
db.pagos.aggregate([
  { $group: { _id: "$metodo", monto_total: { $sum: "$monto" } } }
])
```

**AGGREGATE 23 — Monto cobrado por método.**

```javascript
db.auditoria.aggregate([
  { $group: { _id: "$accion", eventos: { $sum: 1 } } }
])
```

**AGGREGATE 24 — Eventos de auditoría por acción.**

```javascript
db.auditoria.aggregate([
  { $group: { _id: "$coleccion", eventos: { $sum: 1 } } }
])
```

**AGGREGATE 25 — Eventos por colección afectada.** Los de semilla apuntan a `pedidos`.

```javascript
db.productos.aggregate([
  { $project: {
      sku: 1,
      precio: 1,
      nivel: { $switch: {
        branches: [
          { case: { $lt: ["$precio", 1000] }, then: "economico" },
          { case: { $lt: ["$precio", 5000] }, then: "intermedio" }
        ],
        default: "premium"
      }}
  }}
])
```

**AGGREGATE 26 — SWITCH 1, nivel de precio.** Menos de 1000: `economico`. Menos de 5000: `intermedio`. El resto: `premium`. Con el catálogo, la laptop de 12500 queda en `premium`.

```javascript
db.inventario.aggregate([
  { $project: {
      almacen: 1,
      existencias: 1,
      nivel: { $switch: {
        branches: [
          { case: { $eq: ["$existencias", 0] }, then: "agotado" },
          { case: { $lt: ["$existencias", "$stock_minimo"] }, then: "bajo" }
        ],
        default: "suficiente"
      }}
  }}
])
```

**AGGREGATE 27 — SWITCH 2, nivel de inventario.** Cero existencias: `agotado`. Por debajo del mínimo: `bajo`. En otro caso: `suficiente`.

```javascript
db.pedidos.aggregate([
  { $project: {
      total: 1,
      estado: 1,
      categoria_monto: { $switch: {
        branches: [
          { case: { $lt: ["$total", 1000] }, then: "pequeno" },
          { case: { $lt: ["$total", 10000] }, then: "mediano" }
        ],
        default: "grande"
      }}
  }}
])
```

**AGGREGATE 28 — SWITCH 3, tamaño del pedido.** Menos de 1000: `pequeno` (en la muestra regex, el de 914.44). Menos de 10000: `mediano`. Desde 10000: `grande` (12700.00 y 15276.40).

```javascript
db.pagos.aggregate([
  { $project: {
      referencia: 1,
      estado: 1,
      grupo_estado: { $switch: {
        branches: [
          { case: { $in: ["$estado", ["aprobado", "pagado", "completado"]] }, then: "exitoso" },
          { case: { $in: ["$estado", ["rechazado", "fallido", "cancelado"]] }, then: "fallido" }
        ],
        default: "pendiente_u_otro"
      }}
  }}
])
```

**AGGREGATE 29 — SWITCH 4, grupo del pago.** Esas listas van en minúsculas. El estado guardado por el esquema es `Pendiente`, `Aprobado` o `Rechazado`, así que no entra en las ramas y cae en `pendiente_u_otro`.

```javascript
db.auditoria.aggregate([
  { $project: {
      accion: 1,
      coleccion: 1,
      tipo: { $switch: {
        branches: [
          { case: { $in: ["$accion", ["INSERT", "insert", "crear", "CREAR"]] }, then: "alta" },
          { case: { $in: ["$accion", ["UPDATE", "update", "actualizar", "ACTUALIZAR"]] }, then: "cambio" }
        ],
        default: "otro"
      }}
  }}
])
```

**AGGREGATE 30 — SWITCH 5, tipo de movimiento.** `INSERT` se clasifica como `alta`. `UPDATE` sería `cambio`. Cualquier otra acción, incluido `DELETE`, queda en `otro`.
