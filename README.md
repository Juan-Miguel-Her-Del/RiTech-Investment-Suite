# RiTech Investment Suite

Aplicación académica en **Flutter**, con API **FastAPI**, PostgreSQL y Redis.
Alcance: las once tareas del [SCRUM Sprint 2](docs/sprint-2.md).

## Estructura

- `ritech_investment_suite/`: aplicación Flutter, Material 3 y Riverpod.
- `backend/app/`: API, autenticación, modelos y proveedor de mercado.
- `backend/migrations/`: migraciones Alembic versionadas.
- `backend/tests/`: pruebas del servidor y migraciones.
- `docs/`: modelo de datos, proveedor y trazabilidad del sprint.
- `compose.yaml`: servicios locales.

## Iniciar el entorno en Windows

Requisitos: Docker Desktop iniciado y Flutter 3.41.6 / Dart 3.11.4 o compatible.
Desde la raíz del repositorio:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start.ps1
```

El script crea `.env` con secretos aleatorios si no existe y ejecuta
`docker compose up --build -d --wait`. Las migraciones se aplican al iniciar la API.
PostgreSQL y Redis solo son accesibles en la red de Compose. La API queda en
`http://localhost:8000`; documentación interactiva: `http://localhost:8000/docs`.

Crear los usuarios de desarrollo (solicita una contraseña de al menos 12 caracteres):

```powershell
docker compose exec backend python -m app.seed
```

Usuarios: `analista@ritech.local`, `gerente@ritech.local` y `administrador@ritech.local`.
El seed es idempotente: no duplica registros ni cambia contraseñas existentes.
No crea usuarios automáticamente al iniciar el servicio.

Iniciar Flutter web con un origen permitido por la API:

```powershell
cd ritech_investment_suite
flutter pub get
flutter run -d chrome --web-port 3000 --dart-define=API_BASE_URL=http://localhost:8000
```

En emulador Android, `flutter run` utiliza `http://10.0.2.2:8000` por defecto.
En dispositivo físico, configura una URL accesible con `--dart-define=API_BASE_URL=...`;
el puerto de Compose está enlazado a localhost de forma predeterminada.
Las compilaciones Android de desarrollo permiten HTTP local; para distribución utiliza HTTPS.
Las plataformas iOS/macOS requieren su entorno de compilación Apple.

## Sesión y permisos

`POST /auth/login` recibe JSON con `email` y `password`; devuelve `access_token`,
`expires_in` y `user`. Contraseñas con Argon2 y JWT con expiración, emisor y audiencia.
`GET /auth/me` y `GET /quotes/nasdaq100` requieren `Authorization: Bearer <token>`.
Los tres roles pueden consultar cotizaciones; `GET /admin/users` es exclusivo del Administrador.
El servidor consulta el rol vigente en la base de datos en cada solicitud.

Flutter mantiene el token únicamente en memoria mediante Riverpod: cerrar la aplicación
requiere autenticarse nuevamente. Al cerrar sesión, expirar el tiempo o recibir un 401
en una consulta protegida, vuelve al login. Cerrar sesión limpia el cliente;
el token emitido conserva validez en el servidor hasta su expiración (30 minutos por defecto).

## Cotizaciones

El entorno inicial usa `MARKET_PROVIDER=demo`, con datos **simulados y señalizados**.
Para el proveedor real, configurar las variables descritas en [proveedor de mercado](docs/market-provider.md).
Nunca incorporar claves a Flutter ni al repositorio.

## Migraciones y rollback

```powershell
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
# Solo en una base desechable: este rollback elimina las tablas y sus datos.
docker compose exec backend alembic downgrade base
docker compose exec backend alembic upgrade head
```

Crear una nueva revisión con `alembic revision --autogenerate -m "descripcion"`,
revisar el SQL y versionar el archivo. No editar una migración que ya se haya desplegado.

## Pruebas

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
cd backend
../.venv/Scripts/python.exe -m pytest -q
cd ../ritech_investment_suite
flutter analyze
flutter test
flutter build web
flutter build apk --debug
```

Las pruebas rápidas del backend usan SQLite aislado y un proveedor HTTP controlado.
La ejecución de Compose verifica PostgreSQL/Redis reales; `/health/ready` comprueba ambos.

Validación de integración reproducible, con una base temporal independiente que se elimina al terminar:

```powershell
docker compose exec backend python -m app.verify_stack
```

## Convenciones de equipo

Ramas por tarea, por ejemplo `feature/RITECH-16-auth`; commits con la clave Jira.
Antes de integrar: revisar criterios, ejecutar pruebas y documentar cambios de contrato.
No versionar `.env`, tokens, claves ni contraseñas. Detener con `docker compose down`;
esto conserva el volumen de PostgreSQL.
