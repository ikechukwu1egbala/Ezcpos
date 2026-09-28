import 'dart:convert';

import 'package:http/http.dart' as http;

import '../storage/token_storage.dart';
import 'api_config.dart';

class ApiClient {
  ApiClient._();

  static final ApiClient instance = ApiClient._();

  final TokenStorage _tokenStorage = TokenStorage();

  Future<http.Response> get(
    String endpoint, {
    Map<String, String>? queryParameters,
  }) async {
    return _request(
      method: 'GET',
      endpoint: endpoint,
      queryParameters: queryParameters,
    );
  }

  Future<http.Response> post(
    String endpoint, {
    Map<String, dynamic>? body,
  }) async {
    return _request(
      method: 'POST',
      endpoint: endpoint,
      body: body,
    );
  }

  Future<http.Response> put(
    String endpoint, {
    Map<String, dynamic>? body,
  }) async {
    return _request(
      method: 'PUT',
      endpoint: endpoint,
      body: body,
    );
  }

  Future<http.Response> patch(
    String endpoint, {
    Map<String, dynamic>? body,
  }) async {
    return _request(
      method: 'PATCH',
      endpoint: endpoint,
      body: body,
    );
  }

  Future<http.Response> delete(
    String endpoint,
  ) async {
    return _request(
      method: 'DELETE',
      endpoint: endpoint,
    );
  }

  Future<http.Response> _request({
    required String method,
    required String endpoint,
    Map<String, dynamic>? body,
    Map<String, String>? queryParameters,
    bool retryAfterRefresh = true,
  }) async {
    final accessToken = await _tokenStorage.getAccessToken();

    final uri = Uri.parse(
      '${ApiConfig.baseUrl}$endpoint',
    ).replace(
      queryParameters: queryParameters,
    );

    final headers = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    if (accessToken != null && accessToken.isNotEmpty) {
      headers['Authorization'] = 'Bearer $accessToken';
    }

    final encodedBody = body == null ? null : jsonEncode(body);

    http.Response response;

    switch (method) {
      case 'GET':
        response = await http.get(
          uri,
          headers: headers,
        );
        break;

      case 'POST':
        response = await http.post(
          uri,
          headers: headers,
          body: encodedBody,
        );
        break;

      case 'PUT':
        response = await http.put(
          uri,
          headers: headers,
          body: encodedBody,
        );
        break;

      case 'PATCH':
        response = await http.patch(
          uri,
          headers: headers,
          body: encodedBody,
        );
        break;

      case 'DELETE':
        response = await http.delete(
          uri,
          headers: headers,
        );
        break;

      default:
        throw UnsupportedError(
          'Unsupported HTTP method: $method',
        );
    }

    if (response.statusCode == 401 && retryAfterRefresh) {
      final refreshed = await _refreshAccessToken();

      if (refreshed) {
        return _request(
          method: method,
          endpoint: endpoint,
          body: body,
          queryParameters: queryParameters,
          retryAfterRefresh: false,
        );
      }

      await _tokenStorage.clearTokens();
    }

    return response;
  }

  Future<bool> _refreshAccessToken() async {
    final refreshToken = await _tokenStorage.getRefreshToken();

    if (refreshToken == null || refreshToken.isEmpty) {
      return false;
    }

    try {
      final uri = Uri.parse(
        '${ApiConfig.baseUrl}${ApiConfig.refreshEndpoint}',
      );

      final response = await http.post(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode({
          'refresh': refreshToken,
        }),
      );

      if (response.statusCode != 200) {
        return false;
      }

      final data = jsonDecode(response.body) as Map<String, dynamic>;

      final newAccessToken = data['access'] as String?;

      if (newAccessToken == null || newAccessToken.isEmpty) {
        return false;
      }

      await _tokenStorage.saveTokens(
        accessToken: newAccessToken,
        refreshToken: refreshToken,
      );

      return true;
    } catch (_) {
      return false;
    }
  }
}
