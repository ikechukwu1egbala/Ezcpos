import 'package:flutter/material.dart';

import 'core/theme/app_theme.dart';
import 'features/auth/login_page.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const EzcPosApp());
}

class EzcPosApp extends StatelessWidget {
  const EzcPosApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'EZC POS',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const LoginPage(),
    );
  }
}
