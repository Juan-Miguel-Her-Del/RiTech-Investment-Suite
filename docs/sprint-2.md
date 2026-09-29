# Sprint 2 — alcance y aceptación

Fuente: proyecto RITECH, SCRUM Sprint 2 (ID 38), consultado el 28 de septiembre de 2026.
La pertenencia al sprint determina el alcance; algunas etiquetas conservan números de sprints anteriores.

| Jira | Entrega | Validación prevista |
|---|---|---|
| RITECH-11 | Estructura backend/frontend, README, ejemplos de entorno | Ejecución siguiendo README |
| RITECH-12 | Compose para API, PostgreSQL y Redis | Salud de los tres servicios |
| RITECH-13 | Flutter Material 3, Riverpod, navegación y cliente REST | Análisis, pruebas y compilación |
| RITECH-14 | Usuarios, portafolios, activos, cotizaciones, alertas, simulaciones y auditoría | Diagrama, relaciones y restricciones |
| RITECH-15 | Migración inicial, rollback y seed de desarrollo | Migrar base vacía, revertir y migrar nuevamente |
| RITECH-16 | Login JWT y roles Analista, Gerente, Administrador | Credenciales, expiración, tokens inválidos y permisos |
| RITECH-17 | Proveedor de mercado configurable | Configuración, contrato y prueba controlada |
| RITECH-18 | Cliente NASDAQ 100 | Normalización, timeout y errores del proveedor |
| RITECH-19 | GET /quotes/nasdaq100 autenticado | Valor, fecha y rechazo sin token |
| RITECH-29 | Login Flutter con validaciones y errores | Navegación al dashboard tras autenticación |
| RITECH-30 | Sesión y autorización en Flutter | Header Bearer y limpieza al cerrar sesión |

## Orden de implementación

1. Estructura del repositorio, entorno y esquema de datos.
2. Migraciones, seed y autenticación.
3. Proveedor de mercado y endpoint protegido.
4. Aplicación Flutter, sesión y pantalla inicial.
5. Pruebas, documentación y revisión de los criterios.

Las credenciales reales del proveedor se configuran localmente y no se incluyen en Git.
Los datos de prueba deben identificarse explícitamente como simulados.

## Evidencia de implementación

- RITECH-11/12: estructura y README; Compose inicia FastAPI, PostgreSQL 16 y Redis 7
  con comprobaciones de salud; `.env` generado localmente y excluido de Git.
- RITECH-13/29/30: Material 3, Riverpod, formulario validado, cliente HTTP, dashboard,
  Bearer y limpieza de sesión. Cinco pruebas Flutter aprobadas, análisis sin errores,
  compilación web y APK Android debug aprobadas.
- RITECH-14/15: ocho tablas documentadas, migración Alembic y seed idempotente;
  verificados upgrade, rollback y nuevo upgrade en PostgreSQL real mediante base temporal.
- RITECH-16: Argon2, JWT con expiración/emisor/audiencia, roles y permisos verificados.
- RITECH-17/18/19: adaptador Twelve Data, normalización, timeout, errores, caché Redis
  y endpoint autenticado implementados. Pruebas controladas aprobadas.
- Backend: 28 pruebas automatizadas aprobadas; integración PostgreSQL/Redis aprobada
  incluyendo login de los tres roles, permisos, seed y cotización demo.

## Pendiente de validación externa

RITECH-17/18/19 necesitan una clave real con acceso al índice NASDAQ 100 para
validar el proveedor contratado. No se realizó una consulta externa autenticada.
El proveedor local se cambió posteriormente a `fmp` con símbolo `^NDX`.
La consulta real devolvió HTTP 402: el plan no permite esta consulta.
No considerar la integración de mercado aceptada en producción hasta ejecutar
`python -m app.check_market` con el proveedor real y comprobar instrumento y fecha.

La sesión Flutter se conserva en memoria durante la ejecución; no incluye refresh
tokens ni persistencia entre reinicios, que no figuran en los criterios del sprint.
