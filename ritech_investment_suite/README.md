# RiTech — aplicación Flutter

Frontend Flutter Material 3 con Riverpod. Incluye inicio de sesión, sesión JWT en
memoria y dashboard con cotización NASDAQ 100.

Consulta el [README del repositorio](../README.md) para iniciar FastAPI,
PostgreSQL y Redis, crear usuarios de desarrollo y ejecutar la aplicación.

```powershell
flutter pub get
flutter run -d chrome --web-port 3000 --dart-define=API_BASE_URL=http://localhost:8000
flutter analyze
flutter test
flutter build web
```

Organización: `lib/core/` contiene el cliente HTTP; `lib/features/auth/` gestiona
login y sesión; `lib/features/dashboard/` consulta y presenta la cotización.
