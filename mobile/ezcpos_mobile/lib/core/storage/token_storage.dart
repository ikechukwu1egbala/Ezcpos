import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TokenStorage {
  static const String _accessTokenKey = 'ezc_access_token';
  static const String _refreshTokenKey = 'ezc_refresh_token';

  final FlutterSecureStorage _storage =
      const FlutterSecureStorage();

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _storage.write(
      key: _accessTokenKey,
      value: accessToken,
    );

    await _storage.write(
      key: _refreshTokenKey,
      value: refreshToken,
    );
  }

  Future<String?> getAccessToken() async {
    return _storage.read(key: _accessTokenKey);
  }

  Future<String?> getRefreshToken() async {
    return _storage.read(key: _refreshTokenKey);
  }

  Future<void> clearTokens() async {
    await _storage.delete(key: _accessTokenKey);
    await _storage.delete(key: _refreshTokenKey);
  }

  Future<bool> hasTokens() async {
    final accessToken = await getAccessToken();
    final refreshToken = await getRefreshToken();

    return accessToken != null && refreshToken != null;
  }
}
