import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode});
  final String message;
  final int? statusCode;
  @override
  String toString() => message;
}

class ApiClient {
  ApiClient(this.client, this.baseUrl);
  final http.Client client;
  final String baseUrl;

  Future<Map<String, dynamic>> request(
    String path, {
    Map<String, dynamic>? body,
    String? token,
  }) async {
    final uri = Uri.parse('${baseUrl.replaceAll(RegExp(r'/+$'), '')}$path');
    final headers = {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
    try {
      final response =
          await (body == null
                  ? client.get(uri, headers: headers)
                  : client.post(uri, headers: headers, body: jsonEncode(body)))
              .timeout(const Duration(seconds: 15));
      if (response.statusCode < 200 || response.statusCode >= 300) {
        final message = switch (response.statusCode) {
          401 =>
            path == '/auth/login'
                ? 'Correo o contraseña incorrectos.'
                : 'Tu sesión expiró. Vuelve a iniciar sesión.',
          403 => 'No tienes permiso para realizar esta acción.',
          422 => 'Revisa los datos ingresados.',
          429 => 'Demasiados intentos. Espera un momento.',
          503 || 504 => 'El servicio no está disponible. Intenta más tarde.',
          _ => 'No pudimos completar la solicitud. Intenta nuevamente.',
        };
        throw ApiException(message, statusCode: response.statusCode);
      }
      final data = jsonDecode(response.body);
      if (data is! Map<String, dynamic>) throw const FormatException();
      return data;
    } on TimeoutException {
      throw const ApiException(
        'La conexión tardó demasiado. Intenta nuevamente.',
      );
    } on http.ClientException {
      throw const ApiException('No se pudo conectar. Revisa tu conexión.');
    } on FormatException {
      throw const ApiException('El servidor devolvió una respuesta inválida.');
    }
  }
}
