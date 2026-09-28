import 'dart:convert';

import 'package:http/http.dart' as http;

import '../core/network/api_config.dart';
import '../core/storage/token_storage.dart';

class AuthService {
  AuthService._();

  static final AuthService instance = AuthService._();

  final TokenStorage _tokenStorage = TokenStorage();

  Future<bool> login({
    required String username,
    required String password,
  }) async {
    final uri = Uri.parse(
      '${ApiConfig.baseUrl}${ApiConfig.loginEndpoint}',
    );

    final response = await http.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'username': username,
        'password': password,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;

      final accessToken = data['access'] as String?;
      final refreshToken = data['refresh'] as String?;

      if (accessToken == null || refreshToken == null) {
        throw Exception('Login response did not contain JWT tokens.');
      }

      await _tokenStorage.saveTokens(
        accessToken: accessToken,
        refreshToken: refreshToken,
      );

      return true;
    }

    String message = 'Login failed.';

    try {
      final data = jsonDecode(response.body);

      if (data is Map<String, dynamic>) {
        if (data['detail'] != null) {
          message = data['detail'].toString();
        } else if (data['non_field_errors'] != null) {
          message = data['non_field_errors'].toString();
        }
      }
    } catch (_) {
      // Keep the default error message.
    }

    throw Exception(message);
  }

  Future<String?> getAccessToken() {
    return _tokenStorage.getAccessToken();
  }

  Future<String?> getRefreshToken() {
    return _tokenStorage.getRefreshToken();
  }

  Future<bool> isLoggedIn() {
    return _tokenStorage.hasTokens();
  }

  Future<void> logout() {
    return _tokenStorage.clearTokens();
  }
}
