import 'dart:async';
import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:ritech_investment_suite/core/api_client.dart';
import 'package:ritech_investment_suite/features/auth/session.dart';

void main() {
  test('Una respuesta tardía no restaura una sesión cerrada', () async {
    final pending = Completer<http.Response>();
    final container = ProviderContainer(
      overrides: [
        apiClientProvider.overrideWithValue(
          ApiClient(MockClient((_) => pending.future), 'http://test'),
        ),
      ],
    );
    addTearDown(container.dispose);
    final controller = container.read(sessionProvider.notifier);
    final login = controller.login('ana@example.com', 'password');
    controller.logout();
    pending.complete(
      http.Response(
        jsonEncode({
          'access_token': 'token',
          'expires_in': 60,
          'user': {'name': 'Ana', 'role': 'Analista'},
        }),
        200,
      ),
    );
    await login;
    expect(container.read(sessionProvider).asData?.value, isNull);
  });

  test('Un error de una sesión anterior no cierra la sesión actual', () async {
    final container = ProviderContainer(
      overrides: [
        apiClientProvider.overrideWithValue(
          ApiClient(
            MockClient(
              (_) async => http.Response(
                jsonEncode({
                  'access_token': 'new-token',
                  'expires_in': 60,
                  'user': {'name': 'Ana', 'role': 'Analista'},
                }),
                200,
              ),
            ),
            'http://test',
          ),
        ),
      ],
    );
    addTearDown(container.dispose);
    final controller = container.read(sessionProvider.notifier);
    await controller.login('ana@example.com', 'password');
    controller.expireIfCurrent('old-token');
    expect(container.read(sessionProvider).asData!.value!.token, 'new-token');
    controller.expireIfCurrent('new-token');
    expect(container.read(sessionProvider).asData?.value, isNull);
  });
}
