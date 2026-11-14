# Salón API - versión MVC

API REST del sistema de gestión del salón, implementada con FastAPI, PostgreSQL y
Supabase Auth. Esta carpeta contiene una versión alternativa del backend,
organizada con un patrón MVC simplificado.

## Alcance

La aplicación ofrece endpoints para autenticación, clientes, profesionales,
servicios, descuentos, ventas y turnos. FastAPI sirve JSON; no hay vistas HTML
en el backend. La interfaz de escritorio Tkinter y la futura interfaz web Vite
son clientes HTTP independientes.

Esta es una aplicación monolítica: todos los módulos se ejecutan y despliegan
juntos. MVC describe aquí cómo se separan las responsabilidades dentro de la
aplicación, no una arquitectura de microservicios.

## Arquitectura MVC

El flujo general es:

```text
Cliente HTTP
		-> ruta FastAPI
		-> schema Pydantic
		-> controller
		-> uno o más models
		-> PostgreSQL o Supabase Auth
		-> respuesta JSON común
```

Responsabilidad de cada parte:

- `schemas/`: define y valida los cuerpos, parámetros y respuestas de la API.
	FastAPI rechaza automáticamente una solicitud que no cumpla el schema.
- `routes/`: declara métodos y paths HTTP, aplica dependencias de seguridad,
	obtiene controllers y construye respuestas HTTP.
- `controllers/`: coordina el flujo de la operación. Por ejemplo,
	`AppointmentController` consulta profesionales, servicios, clientes y agenda
	antes de pedir que se guarde una reserva.
- `models/`: consulta y modifica los datos, y contiene reglas de negocio ligadas
	a esos datos. `AppointmentModel`, por ejemplo, calcula disponibilidad y valida
	transiciones de estado además de persistir turnos.
- `db/`: crea el pool de PostgreSQL, proporciona transacciones y contiene el
	helper `Crud` para operaciones simples de una tabla.
- `security.py`: valida tokens Supabase y aplica autorización basada en roles.
- `responses.py`: normaliza respuestas exitosas y errores.
- `errors.py` y `exceptions/`: contienen la excepción base y errores específicos
	de cada funcionalidad.
- `config/`: lee configuración del entorno y del archivo `.env` local.

Los models reciben la misma conexión cuando una operación necesita coordinar
varias tablas. Así, por ejemplo, una venta y sus detalles o un turno y sus
detalles participan de la misma transacción abierta por la ruta.

## Estructura

```text
app_mvc/
	config/          Configuración tipada
	controllers/     Coordinación de operaciones
	db/              Pool, transacciones y Crud
	exceptions/      Errores específicos por funcionalidad
	models/          Consultas, persistencia y reglas de negocio
	routes/          Routers FastAPI y registro central
	schemas/         Contratos y validación Pydantic
	errors.py        Excepción base de la aplicación
	responses.py     Respuestas y manejadores comunes
	security.py      Validación JWT y autorización por rol
	main.py          Creación y configuración de FastAPI
```

## Requisitos

- Python 3.12 o superior.
- `uv` para instalar dependencias y ejecutar la API.
- PostgreSQL con el esquema del proyecto aplicado.
- Un proyecto Supabase Auth configurado.

Las dependencias están declaradas en `pyproject.toml`; `uv.lock` fija las
versiones resueltas.

## Configuración

La aplicación busca el archivo `app_mvc/.env`. También se pueden proporcionar
las mismas variables mediante el entorno del proceso. Usa valores propios del
entorno local; no guardes contraseñas, tokens ni claves reales en el repositorio.

Variables disponibles:

| Variable | Requerida | Descripción |
| --- | --- | --- |
| `DATABASE_URL` | Sí | Cadena de conexión a PostgreSQL. |
| `SUPABASE_URL` | Sí | URL del proyecto Supabase, por ejemplo `https://<project>.supabase.co`. |
| `SUPABASE_ANON_KEY` | Sí | Clave publicable/anon usada por el servidor para solicitar login y refresh. No es la `service_role`. |
| `SUPABASE_SERVICE_ROLE_KEY` | Para gestionar vendedores | Clave administrativa usada solo por la API para invitar/listar/eliminar usuarios de Supabase Auth. Nunca la pongas en Vite o en el escritorio. |
| `SUPABASE_INVITE_REDIRECT_URL` | Sí para invitar | URL del callback del frontend, por ejemplo `http://localhost:4321/auth/callback`. Debe estar permitida en Supabase Auth. |
| `JWT_ALGORITHM` | No | Algoritmo aceptado: `ES256` o `HS256`. Por defecto `ES256`. Debe coincidir con Supabase. |
| `SUPABASE_JWT_SECRET` | Solo para HS256 | Secreto de firma JWT del proyecto. No se usa para `ES256`. |
| `JWT_EXPIRATION_HOURS` | No | Vida máxima aceptada para un token, en horas. Por defecto `1`; ajústala a la duración configurada en Supabase. |
| `ENVIRONMENT` | No | Entorno de ejecución. En `production` se deshabilita `/docs`. |
| `LOG_LEVEL` | No | Nivel de logging. |
| `CORS_ORIGINS` | No | Orígenes web permitidos; por defecto `http://localhost:3000`. |
| `ZONA_HORARIA` | No | Zona horaria del salón. Por defecto `America/Argentina/Buenos_Aires`. |

Ejemplo de `.env` local, con marcadores y no credenciales reales:

```dotenv
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<database>
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=<public-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<server-only-secret-key>
SUPABASE_INVITE_REDIRECT_URL=http://localhost:4321/auth/callback
JWT_ALGORITHM=ES256
JWT_EXPIRATION_HOURS=24
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
ZONA_HORARIA=America/Argentina/Buenos_Aires
```

Con `ES256`, PyJWT usa la biblioteca `cryptography` y obtiene la clave pública
desde el endpoint JWKS de Supabase. Con `HS256`, la configuración debe incluir
`SUPABASE_JWT_SECRET`. El backend registra el tipo de error JWT rechazado, pero
no debe registrar ni compartir el token.

## Instalación y ejecución

Ejecuta estos comandos desde la raíz del repositorio:

```sh
uv sync --project app_mvc
uv run --project app_mvc uvicorn app_mvc.main:app --reload --host 0.0.0.0 --port 8000
```

La documentación interactiva queda en `http://127.0.0.1:8000/docs` durante el
desarrollo. La especificación OpenAPI está en `/openapi.json`. Para detener el
servidor, usa `Ctrl+C` en la terminal que lo está ejecutando.

Al iniciar, `main.py` abre el pool de conexiones; al apagar, lo cierra. El pool
se configura con un máximo de tres conexiones. La dependencia compartida
`get_db_connection()` de `db/database.py` toma una conexión del pool dentro de
`db.transaction()`. Las rutas y la validación del rol usan esa dependencia, que
FastAPI reutiliza dentro de la misma petición. Al finalizar, confirma los
cambios si todo salió bien, o hace rollback si una excepción escapó; después
devuelve la conexión al pool para que otra petición pueda reutilizarla.

## Autenticación y JWT

### Personal y escritorio

`POST /auth/login` envía email y contraseña a Supabase Auth. La respuesta incluye
el `access_token` y el `refresh_token`; ambos se devuelven dentro de `data` por
el formato común de respuestas. El cliente de escritorio conserva los tokens en
memoria y envía el access token así:

```http
Authorization: Bearer <access_token>
```

Cuando una solicitud protegida recibe `401`, el cliente puede renovar la sesión
con `POST /auth/refresh`, enviando el refresh token. Supabase emite los tokens
actualizados.

### Verificación del access token

`current_user` en `security.py`:

1. Requiere el esquema `Bearer`.
2. Verifica la firma usando JWKS para `ES256`, o `SUPABASE_JWT_SECRET` para
	 `HS256`.
3. Restringe los algoritmos al valor configurado; no confía en un algoritmo
	 indicado libremente por el token.
4. Comprueba el emisor (`<SUPABASE_URL>/auth/v1`) y la audiencia
	 `authenticated`.
5. Comprueba `iat`, `exp` y que la duración no exceda
	 `JWT_EXPIRATION_HOURS`.

Un token válido identifica al usuario mediante el claim `sub`, pero no concede
por sí solo un rol de la aplicación.

### Roles y autorización

`current_staff` busca el UUID de `sub` en `perfiles`. Si no hay perfil de
personal, se rechaza el acceso. `require_role(...)` comprueba el rol guardado en
la base; el rol no se toma de la interfaz ni de un dato enviado por el cliente.

Los roles usados por la aplicación son `dueno` y `vendedor`. Como regla general:

- Clientes: requieren personal autenticado (`dueno` o `vendedor`).
- Servicios: catálogo público; gestión para personal (`dueno` o `vendedor`).
- Profesionales: lectura pública; cambios solo para `dueno`.
- Descuentos: descuentos públicos vigentes; gestión solo para `dueno`.
- Ventas: requieren personal (`dueno` o `vendedor`).
- Gestión de turnos: requiere personal (`dueno` o `vendedor`).
- Disponibilidad y reserva pública de turnos: no requieren sesión.
- Login y refresh: públicos.

La función `es_duena()` del desktop consulta `/discounts/management`; una
respuesta `403` indica que la sesión corresponde a un vendedor. La decisión
definitiva siempre se vuelve a aplicar en el backend.

La gestión de vendedores usa Supabase Admin desde el backend. El escritorio
solo solicita nombre y email: el servidor fija el rol `vendedor`, envía la
invitación al frontend Astro (`web/src/pages/auth/callback.astro`) y la persona
configura su propia contraseña desde el enlace recibido.
Eliminar un vendedor borra su usuario de Auth; la clave foránea elimina su fila
de `perfiles` en cascada. El endpoint no permite eliminar el perfil de la dueña.

### OAuth de clientes

Esta API MVC no inicia el flujo OAuth de clientes. El frontend Vite puede
iniciarlo directamente con Supabase Auth y luego enviar el access token a los
endpoints que requieran sesión cuando esos endpoints estén implementados con
esa política. Crear una cuenta en `auth.users` no crea automáticamente una fila
en `clientes`; el vínculo se realiza explícitamente mediante
`clientes.user_id`. El escritorio, en cambio, usa login por email y contraseña
para personal.

## Respuestas y errores

Las respuestas exitosas se envuelven con `success_response`:

```json
{
	"success": true,
	"message": "Operación exitosa",
	"data": {},
	"errors": null
}
```

El cliente debe leer el contenido útil desde `data`. Los errores usan el mismo
envoltorio, con `success: false`, `data: null`, un mensaje, `errors` opcional y
un `code`. Los manejadores globales cubren `AppError`, `HTTPException`, errores
de validación de FastAPI y excepciones inesperadas. Las excepciones inesperadas
se registran en el servidor; el detalle interno no se devuelve al cliente.

Respuestas HTTP habituales:

- `401`: falta un token, es inválido o expiró.
- `403`: el usuario autenticado no tiene el rol requerido.
- `404`: el recurso no existe o no está disponible.
- `409`: conflicto con el estado actual, por ejemplo horario ocupado o
	descuento chisme ya configurado.
- `422`: datos incorrectos o regla de negocio incumplida.
- `500`: error inesperado del servidor.

## Módulos y endpoints

Todos los endpoints de negocio devuelven el formato común, salvo que se indique
lo contrario. Los prefijos se montan en `routes/__init__.py`.

| Módulo | Endpoint | Acceso | Propósito |
| --- | --- | --- | --- |
| Auth | `POST /auth/login` | Público | Inicia sesión con email y contraseña en Supabase Auth. |
| Auth | `POST /auth/refresh` | Público | Renueva la sesión usando `refresh_token`. |
| Personal | `GET /admin/staff/` | `dueno` | Lista perfiles de personal junto con sus emails de Auth. |
| Personal | `POST /admin/staff/` | `dueno` | Invita un vendedor, crea su cuenta Auth y registra el perfil `vendedor`. |
| Personal | `DELETE /admin/staff/{user_id}` | `dueno` | Elimina la cuenta Auth del vendedor y su perfil asociado. |
| Clientes | `GET /clients/?only_active=true` | Personal | Lista clientes; `only_active=false` incluye inactivos. |
| Clientes | `GET /clients/{client_id}` | Personal | Obtiene un cliente. |
| Clientes | `POST /clients/` | Personal | Crea un cliente. |
| Clientes | `PUT /clients/{client_id}` | Personal | Actualiza sus datos. |
| Clientes | `PATCH /clients/{client_id}/activate` | Personal | Reactiva un cliente. |
| Clientes | `DELETE /clients/{client_id}` | Personal | Desactiva lógicamente un cliente. |
| Profesionales | `GET /professionals/?only_active=true` | Público | Lista profesionales. |
| Profesionales | `GET /professionals/{professional_id}` | Público | Obtiene un profesional. |
| Profesionales | `POST /professionals/` | `dueno` | Crea un profesional. |
| Profesionales | `PUT /professionals/{professional_id}` | `dueno` | Actualiza sus datos. |
| Profesionales | `DELETE /professionals/{professional_id}` | `dueno` | Desactiva lógicamente un profesional. |
| Servicios | `GET /services/` | Público | Lista servicios activos y visibles online. |
| Servicios | `GET /services/{service_id}` | Público | Obtiene un servicio público. |
| Servicios | `GET /services/management` | Personal | Lista el catálogo de gestión, incluso inactivos/no visibles. |
| Servicios | `GET /services/management/{service_id}` | Personal | Obtiene un servicio para gestión. |
| Servicios | `POST /services/` | Personal | Crea un servicio. |
| Servicios | `PUT /services/{service_id}` | Personal | Actualiza un servicio. |
| Servicios | `DELETE /services/{service_id}` | Personal | Desactiva lógicamente un servicio. |
| Descuentos | `GET /discounts/` | Público | Lista promociones vigentes de servicios activos y visibles. |
| Descuentos | `GET /discounts/management` | `dueno` | Lista todos los descuentos. |
| Descuentos | `GET /discounts/management/{discount_id}` | `dueno` | Obtiene un descuento. |
| Descuentos | `POST /discounts/` | `dueno` | Crea un descuento. |
| Descuentos | `PUT /discounts/{discount_id}` | `dueno` | Actualiza un descuento. |
| Descuentos | `DELETE /discounts/{discount_id}` | `dueno` | Desactiva lógicamente un descuento. |
| Turnos | `GET /appointments/availability` | Público | Calcula horarios para profesional, fecha y servicios. |
| Turnos | `POST /appointments/` | Público | Reserva un turno para una invitada. |
| Turnos | `GET /admin/appointments/?start_date=...&end_date=...` | Personal | Lista turnos por rango; admite filtros `professional_id` y `status`. |
| Turnos | `GET /admin/appointments/{appointment_id}` | Personal | Obtiene un turno. |
| Turnos | `POST /admin/appointments/` | Personal | Registra una reserva desde la gestión. |
| Turnos | `POST /admin/appointments/{appointment_id}/cancel` | Personal | Cancela un turno. |
| Turnos | `PATCH /admin/appointments/{appointment_id}/status` | Personal | Cambia el estado permitido. |
| Ventas | `GET /sales/` | Personal | Lista ventas e importes calculados. |
| Ventas | `GET /sales/{sale_id}` | Personal | Obtiene una venta. |
| Ventas | `POST /sales/` | Personal | Registra la venta de un turno realizado. |

Los valores de `status` para turnos son `pending`, `confirmed`, `completed`,
`cancelled` y `absent`. Los filtros de fechas usan formato ISO (`YYYY-MM-DD`).

## Reglas principales

### Clientes

Se requiere al menos teléfono o email. El listado puede excluir inactivos y la
baja es lógica. Al reservar un turno públicamente, el backend busca o crea el
cliente por teléfono dentro de la transacción.

### Servicios y descuentos

El precio y la duración del servicio se validan en el schema y en PostgreSQL.
Los descuentos de tipo `service` deben asociarse a un servicio; los de tipo
`gossip` no se asocian a un servicio y solo puede existir una configuración.
La lista pública excluye descuentos inactivos, fuera de vigencia o asociados a
servicios que no sean activos y visibles online.

### Turnos

La reserva requiere profesional activo, servicios activos, fecha futura, horario
de atención y una franja sin superposición con turnos activos ni bloqueos. La
duración se obtiene sumando las duraciones de los servicios. Los horarios
disponibles se generan en pasos de 15 minutos. La base de datos también tiene
una restricción de exclusión para impedir solapamientos simultáneos de una misma
profesional; si ocurre una carrera durante la reserva, se devuelve conflicto.

Transiciones permitidas:

- `pending` -> `confirmed` o `cancelled`.
- `confirmed` -> `completed`, `cancelled` o `absent`.
- Los estados finales no tienen transiciones posteriores.
- Un turno no puede marcarse completado o ausente antes de su inicio.

### Ventas

Solo se cobra un turno realizado, con detalles y sin venta previa. El controller
coordina las comprobaciones y el descuento chisme; `SaleModel` persiste la venta
y sus detalles copiando los precios guardados en el turno. La ruta proporciona
una conexión transaccional compartida para que un error al guardar un detalle
revierta también la cabecera de la venta.

## Desarrollo y pruebas

Comprobar sintaxis e importación:

```sh
uv run --project app_mvc python -m compileall -q app_mvc
uv run --project app_mvc python -c 'from app_mvc.main import app; print(len(app.openapi()["paths"]))'
```

La verificación anterior no prueba PostgreSQL. Las operaciones que dependen de
la base deben probarse también con una instancia de desarrollo, en particular
las transacciones, el bloqueo `FOR UPDATE`, las restricciones de unicidad y la
restricción de solapamiento de turnos.

## Relación con el escritorio

El cliente Tkinter vive en `../desktop`. Su `SalonService` adapta los paths y
nombres de los contratos MVC a los nombres que consumen las pantallas antiguas.
Para iniciarlo desde la carpeta `desktop`:

```sh
uv sync
SALON_API_URL=http://127.0.0.1:8000 uv run main.py
```

El frontend Vite puede iniciar OAuth directamente con Supabase. El access token
debe validarse en el backend antes de acceder a rutas protegidas. La creación o
vinculación de una cuenta OAuth con `clientes.user_id` es explícita; no ocurre
automáticamente al crear el usuario en `auth.users`.

## Seguridad de configuración

- No guardes credenciales ni tokens en README, capturas, código o commits.
- Mantén `.env` fuera del control de versiones; usa valores separados para
	desarrollo y producción.
- En frontend usa solo la clave publicable de Supabase; nunca expongas
	`service_role` ni `SUPABASE_JWT_SECRET`.
- Si una contraseña, clave o token fue compartido, rótalo/revócalo.
