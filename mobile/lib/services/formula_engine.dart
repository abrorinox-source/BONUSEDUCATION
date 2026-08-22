import '../models/spreadsheet.dart';

class FormulaEngine {
  /// Evaluates the first safe subset of formulas used by the spreadsheet.
  /// Column names are referenced directly, e.g. `MASHQ + TEST * 2`.
  /// Function support is intentionally small and deterministic for mobile use.
  double evaluate(String formula, Map<String, dynamic> row, List<SpreadsheetColumn> columns) {
    final normalized = formula.trim();
    if (normalized.isEmpty) return 0;

    final values = <String, double>{};
    for (final column in columns) {
      final raw = row[column.id];
      values[column.name] = _number(raw);
      values[column.id] = _number(raw);
    }

    final expanded = normalized.replaceAllMapped(
      RegExp(r'[A-Za-z_][A-Za-z0-9_]*'),
      (match) => values.containsKey(match.group(0))
          ? values[match.group(0)!]!.toString()
          : match.group(0)!,
    );

    return _simpleExpression(expanded);
  }

  double _number(dynamic value) {
    if (value is num) return value.toDouble();
    return double.tryParse(value?.toString() ?? '') ?? 0;
  }

  double _simpleExpression(String expression) {
    // MVP evaluator: +, -, *, / and parentheses are supported.
    // Production parser will be extended with SUM/AVG/MIN/MAX/IF and
    // circular-dependency validation before formulas are persisted.
    final parser = _ExpressionParser(expression);
    return parser.parse();
  }
}

class _ExpressionParser {
  final String input;
  int index = 0;

  _ExpressionParser(this.input);

  double parse() {
    final value = _expression();
    _skip();
    if (index != input.length) {
      throw FormatException('Invalid formula near ${input.substring(index)}');
    }
    return value;
  }

  double _expression() {
    var value = _term();
    while (true) {
      _skip();
      if (_match('+')) value += _term();
      else if (_match('-')) value -= _term();
      else return value;
    }
  }

  double _term() {
    var value = _factor();
    while (true) {
      _skip();
      if (_match('*')) value *= _factor();
      else if (_match('/')) value /= _factor();
      else return value;
    }
  }

  double _factor() {
    _skip();
    if (_match('(')) {
      final value = _expression();
      if (!_match(')')) throw const FormatException('Missing )');
      return value;
    }
    var sign = 1.0;
    if (_match('-')) sign = -1;
    _skip();
    final start = index;
    while (index < input.length && RegExp(r'[0-9.]').hasMatch(input[index])) index++;
    if (start == index) throw FormatException('Expected number at $index');
    return sign * double.parse(input.substring(start, index));
  }

  bool _match(String char) {
    if (index < input.length && input[index] == char) {
      index++;
      return true;
    }
    return false;
  }

  void _skip() {
    while (index < input.length && input[index].trim().isEmpty) index++;
  }
}
