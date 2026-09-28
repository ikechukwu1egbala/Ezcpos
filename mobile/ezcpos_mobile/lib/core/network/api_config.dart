class ApiConfig {
  ApiConfig._();

  // Development API.
  // Django is running locally on the same Android device.
  static const String baseUrl = 'http://127.0.0.1:8000';

  static const String loginEndpoint = '/api/token/';
  static const String refreshEndpoint = '/api/token/refresh/';
}
