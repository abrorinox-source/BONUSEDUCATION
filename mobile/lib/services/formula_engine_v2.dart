import '../models/spreadsheet.dart';

class FormulaEngineV2 {
  double evaluate(String formula, Map<String, dynamic> row, List<SpreadsheetColumn> columns) {
    var expression = formula.trim();
    expression = expression.replaceAllMapped(RegExp(r'SUM\(([^)]*)\)', caseSensitive: false), (m) => _args(m.group(1)!, row, columns).fold(0.0, (a,b)=>a+b).toString());
    expression = expression.replaceAllMapped(RegExp(r'AVG\(([^)]*)\)', caseSensitive: false), (m) { final v=_args(m.group(1)!,row,columns); return (v.isEmpty?0:v.reduce((a,b)=>a+b)/v.length).toString(); });
    expression = expression.replaceAllMapped(RegExp(r'MIN\(([^)]*)\)', caseSensitive: false), (m) => (_args(m.group(1)!,row,columns).fold<double>(double.infinity,(a,b)=>a<b?a:b)).toString());
    expression = expression.replaceAllMapped(RegExp(r'MAX\(([^)]*)\)', caseSensitive: false), (m) => (_args(m.group(1)!,row,columns).fold<double>(double.negativeInfinity,(a,b)=>a>b?a:b)).toString());
    for (final c in columns) {
      final value = _number(row[c.id]);
      expression = expression.replaceAll(RegExp(r'\b${RegExp.escape(c.name)}\b'), value.toString());
    }
    return _Parser(expression).parse();
  }

  List<double> _args(String text, Map<String,dynamic> row, List<SpreadsheetColumn> columns) => text.split(',').map((x) {
    final name=x.trim(); final c=columns.cast<SpreadsheetColumn?>().firstWhere((c)=>c?.name==name,orElse:()=>null); return _number(c==null?name:row[c.id]);
  }).toList();
  double _number(dynamic x)=>x is num?x.toDouble():double.tryParse('$x')??0;
}

class _Parser {
  final String s; int i=0; _Parser(this.s);
  double parse(){final v=e(); _skip(); if(i!=s.length) throw FormatException('Invalid formula'); return v;}
  double e(){var v=t();while(true){_skip();if(_m('+'))v+=t();else if(_m('-'))v-=t();else return v;}}
  double t(){var v=f();while(true){_skip();if(_m('*'))v*=f();else if(_m('/'))v/=f();else return v;}}
  double f(){_skip();if(_m('(')){final v=e();if(!_m(')'))throw FormatException('Missing )');return v;}var st=i;if(_m('-')){}while(i<s.length&&RegExp(r'[0-9.]').hasMatch(s[i]))i++;if(st==i)throw FormatException('Expected number');return double.parse(s.substring(st,i));}
  bool _m(String c){if(i<s.length&&s[i]==c){i++;return true;}return false;} void _skip(){while(i<s.length&&s[i].trim().isEmpty)i++;}
}
