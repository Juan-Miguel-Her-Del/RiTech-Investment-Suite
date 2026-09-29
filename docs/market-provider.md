# Proveedor de cotización NASDAQ 100

La interfaz interna consulta el **índice NASDAQ 100**, no un ETF ni el conjunto de
sus componentes. Adaptadores disponibles: Financial Modeling Prep (`fmp`) y Twelve Data (`twelvedata`).

## Financial Modeling Prep

Configuración actual en `.env`:

```dotenv
MARKET_PROVIDER=fmp
MARKET_API_KEY=<clave propia de Financial Modeling Prep>
MARKET_SYMBOL=^NDX
```

El adaptador utiliza `GET https://financialmodelingprep.com/stable/quote` con parámetros
`symbol` y `apikey`, según la [documentación oficial](https://site.financialmodelingprep.com/developer/docs/stable/index-quote).
Recibe una lista con un objeto: `symbol`, `price` y `timestamp` (segundos Unix).
Valida el símbolo, precio positivo/finito y fecha. Expone el mismo contrato de RiTech
con `symbol: NDX`, `source: fmp` e `is_demo: false`; Flutter no requiere cambios.

Activar y probar desde la raíz:

```powershell
docker compose up --build -d --wait backend
docker compose exec backend python -m app.check_market
```

Una clave válida no garantiza acceso al índice: HTTP 402/403 indica restricciones
del plan o permisos; 401 indica clave rechazada y 429 límite de solicitudes.
Una respuesta vacía o un cuerpo `Error Message` también se reportan sin sustituir
la cotización por datos simulados ni exponer claves.

Resultado de la prueba con la clave configurada: HTTP 402 para `^NDX`. El adaptador
está instalado y activo, pero el acceso real sigue pendiente de habilitación en la cuenta.

## Configuración de Twelve Data

En `.env`: `MARKET_PROVIDER=twelvedata`, `MARKET_API_KEY=<clave propia>`,
`MARKET_SYMBOL=NDX`. Confirmar que la cuenta tenga acceso al índice y que el símbolo
coincida con el catálogo habilitado para su plan. Si el proveedor requiere otro símbolo,
configurarlo sin sustituir silenciosamente el índice por QQQ u otro instrumento.

```powershell
docker compose up -d --force-recreate backend
docker compose exec backend python -m app.check_market
```

La prueba controlada realiza exactamente una solicitud, muestra el modelo normalizado
y sale con código distinto de cero si falla. Nunca muestra la clave ni la URL con credenciales.
En modo demo la misma prueba devuelve `is_demo: true`; eso no acredita conectividad real.

## Contrato

Solicitud HTTPS al proveedor: `GET https://api.twelvedata.com/quote`, parámetros
`symbol` y `apikey`. Se leen `close` (decimal en texto) y `timestamp` (Unix en segundos).
Se validan el símbolo recibido, valor positivo/finito y fecha convertible a UTC.

Respuesta RiTech:

```json
{
  "symbol": "NDX",
  "name": "NASDAQ 100",
  "value": "20000.00",
  "updated_at": "2026-09-28T12:00:00Z",
  "source": "demo",
  "is_demo": true
}
```

El precio conserva precisión decimal y se expresa en puntos. `updated_at` es la fecha
entregada por el proveedor; no se reemplaza por la hora de la consulta. En modo demo
el valor fijo de ejemplo se genera con la hora actual y se identifica explícitamente.

## Límites y fallos

El cupo, los instrumentos disponibles y el retraso de datos dependen del plan contratado;
no se asume acceso gratuito ni tiempo real. Consultar el panel de la cuenta y la
[documentación oficial de Twelve Data](https://twelvedata.com/docs).
La [guía oficial de solicitudes](https://support.twelvedata.com/en/articles/5620512-how-to-create-a-request)
explica el consumo de créditos por endpoint.

- Timeout configurable: 8 segundos por defecto; se devuelve HTTP 504.
- Caché Redis: 60 segundos por defecto, por proveedor y símbolo.
- No hay reintentos automáticos que multipliquen el consumo de créditos.
- HTTP 429 o error lógico del proveedor: HTTP 503 con mensaje controlado.
- Respuesta malformada o fallo de transporte: HTTP 502.
- No se usan datos demo como sustituto silencioso de un fallo real.
- Si Redis falla, se consulta directamente al proveedor; solicitudes concurrentes
  pueden consumir más de un crédito. Ajustar límites antes de exposición pública.

La clave real y el acceso de la cuenta al índice son necesarios para certificar
la conectividad externa. Las pruebas automatizadas usan `httpx.MockTransport`.

La comprobación con la cuenta configurada devolvió HTTP 404 indicando que NDX está
disponible desde los planes Grow o Venture. Este resultado es una restricción del
plan, no un fallo de conexión. La API distingue este caso de una clave rechazada,
un símbolo inexistente y un error de transporte. Verificar las condiciones vigentes
en la cuenta antes de contratar un plan.

Referencia de límites: [créditos y errores 429](https://support.twelvedata.com/en/articles/5615854-credits).
