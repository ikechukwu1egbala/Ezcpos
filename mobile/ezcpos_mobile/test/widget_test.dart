import 'package:flutter_test/flutter_test.dart';
import 'package:ezcpos_mobile/main.dart';

void main() {
  testWidgets('EZC POS app loads', (WidgetTester tester) async {
    await tester.pumpWidget(const EzcPosApp());

    expect(find.text('EZC POS'), findsOneWidget);
  });
}
