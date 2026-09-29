import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import '../../core/api_client.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  final client = http.Client();
  ref.onDispose(client.close);
  const configured = String.fromEnvironment('API_BASE_URL');
  final defaultUrl = !kIsWeb && defaultTargetPlatform == TargetPlatform.android
      ? 'http://10.0.2.2:8000'
      : 'http://localhost:8000';
  return ApiClient(client, configured.isEmpty ? defaultUrl : configured);
});

class Session {
  const Session({required this.token, required this.name, required this.role});
  final String token;
  final String name;
  final String role;
}

final sessionProvider =
    NotifierProvider<SessionController, AsyncValue<Session?>>(
      SessionController.new,
    );

class SessionController extends Notifier<AsyncValue<Session?>> {
  Timer? _expiry;
  int _generation = 0;
  @override
  AsyncValue<Session?> build() {
    ref.onDispose(() => _expiry?.cancel());
    return const AsyncData(null);
  }

  Future<void> login(String email, String password) async {
    final generation = ++_generation;
    _expiry?.cancel();
    state = const AsyncLoading();
    try {
      final data = await ref
          .read(apiClientProvider)
          .request(
            '/auth/login',
            body: {'email': email.trim().toLowerCase(), 'password': password},
          );
      if (!ref.mounted || generation != _generation) return;
      final token = data['access_token'];
      final seconds = data['expires_in'];
      final user = data['user'];
      if (token is! String ||
          token.isEmpty ||
          seconds is! int ||
          seconds <= 0 ||
          user is! Map<String, dynamic> ||
          user['name'] is! String ||
          user['role'] is! String) {
        throw const ApiException('El servidor devolvió una sesión inválida.');
      }
      state = AsyncData(
        Session(token: token, name: user['name'], role: user['role']),
      );
      _expiry = Timer(Duration(seconds: seconds), logout);
    } catch (error, stack) {
      if (ref.mounted && generation == _generation)
        state = AsyncError(error, stack);
    }
  }

  void logout() {
    _generation++;
    _expiry?.cancel();
    state = const AsyncData(null);
  }

  void expireIfCurrent(String token) {
    if (state.asData?.value?.token == token) logout();
  }
}
