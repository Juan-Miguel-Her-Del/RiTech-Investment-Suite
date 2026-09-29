import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:ritech_investment_suite/core/api_client.dart';
import 'package:ritech_investment_suite/features/auth/session.dart';
import 'package:ritech_investment_suite/main.dart';

void main() {
  testWidgets('Valida campos requeridos sin enviar solicitudes', (
    tester,
  ) async {
    await tester.pumpWidget(const ProviderScope(child: MyApp()));
    await tester.tap(find.text('Iniciar sesión'));
    await tester.pump();
    expect(find.text('Ingresa tu correo electrónico.'), findsOneWidget);
    expect(find.text('Ingresa tu contraseña.'), findsOneWidget);
  });

  testWidgets('Login, autorización del dashboard y cierre de sesión', (
    tester,
  ) async {
    final requests = <http.Request>[];
    final client = MockClient((request) async {
      requests.add(request);
      if (request.url.path == '/auth/login') {
        expect(jsonDecode(request.body)['email'], 'analista@ritech.local');
        return http.Response(
          jsonEncode({
            'access_token': 'test-token',
            'expires_in': 1800,
            'user': {'name': 'Ana', 'role': 'Analista'},
          }),
          200,
        );
      }
      expect(request.headers['Authorization'], 'Bearer test-token');
      return http.Response(
        jsonEncode({
          'value': '20000',
          'updated_at': '2026-09-28T12:00:00Z',
          'is_demo': true,
        }),
        200,
      );
    });
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(ApiClient(client, 'http://test')),
        ],
        child: const MyApp(),
      ),
    );
    await tester.enterText(
      find.byType(TextFormField).at(0),
      'analista@ritech.local',
    );
    await tester.enterText(find.byType(TextFormField).at(1), 'password');
    await tester.tap(find.text('Iniciar sesión'));
    await tester.pumpAndSettle();
    expect(find.text('Hola, Ana'), findsOneWidget);
    expect(find.text('Datos simulados de desarrollo'), findsOneWidget);
    expect(requests.length, 2);
    await tester.tap(find.byTooltip('Cerrar sesión'));
    await tester.pumpAndSettle();
    expect(find.text('Iniciar sesión'), findsOneWidget);
    expect(find.text('Hola, Ana'), findsNothing);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('Muestra error comprensible al rechazar credenciales', (
    tester,
  ) async {
    final client = MockClient((_) async => http.Response('{}', 401));
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(ApiClient(client, 'http://test')),
        ],
        child: const MyApp(),
      ),
    );
    await tester.enterText(find.byType(TextFormField).at(0), 'ana@example.com');
    await tester.enterText(find.byType(TextFormField).at(1), 'wrong');
    await tester.tap(find.text('Iniciar sesión'));
    await tester.pumpAndSettle();
    expect(find.text('Correo o contraseña incorrectos.'), findsOneWidget);
    expect(find.text('RiTech · Dashboard'), findsNothing);
  });
}
