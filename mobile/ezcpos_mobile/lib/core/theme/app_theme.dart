import 'package:flutter/material.dart';

class AppTheme {
  AppTheme._();

  static const Color ezcBrown = Color(0xFF6B3E26);
  static const Color ezcDarkBrown = Color(0xFF3E2416);
  static const Color ezcYellow = Color(0xFFFFC107);
  static const Color ezcLightBrown = Color(0xFFF4E4D6);
  static const Color ezcCream = Color(0xFFFFF9F3);

  static ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    scaffoldBackgroundColor: ezcCream,
    colorScheme: ColorScheme.fromSeed(
      seedColor: ezcBrown,
      primary: ezcBrown,
      secondary: ezcYellow,
      surface: Colors.white,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: ezcBrown,
      foregroundColor: Colors.white,
      elevation: 0,
      centerTitle: false,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: ezcBrown,
        foregroundColor: Colors.white,
        minimumSize: const Size(double.infinity, 52),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide.none,
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: ezcLightBrown),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(
          color: ezcBrown,
          width: 2,
        ),
      ),
    ),
    cardTheme: CardThemeData(
      color: Colors.white,
      elevation: 1,
      margin: const EdgeInsets.all(8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
    ),
  );
}
