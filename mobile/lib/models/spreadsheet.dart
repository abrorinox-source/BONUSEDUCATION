class SpreadsheetColumn {
  final String id;
  final String name;
  final ColumnType type;
  final int order;
  final bool editable;
  final String? formula;

  const SpreadsheetColumn({
    required this.id,
    required this.name,
    required this.type,
    required this.order,
    this.editable = true,
    this.formula,
  });

  bool get isFormula => type == ColumnType.formula;

  Map<String, dynamic> toMap() => {
        'name': name,
        'type': type.name,
        'order': order,
        'editable': editable,
        'formula': formula,
      };

  factory SpreadsheetColumn.fromMap(String id, Map<String, dynamic> map) {
    final typeName = map['type'] as String? ?? 'number';
    return SpreadsheetColumn(
      id: id,
      name: map['name'] as String? ?? 'Column',
      type: ColumnType.values.firstWhere(
        (e) => e.name == typeName,
        orElse: () => ColumnType.number,
      ),
      order: (map['order'] as num?)?.toInt() ?? 0,
      editable: map['editable'] as bool? ?? true,
      formula: map['formula'] as String?,
    );
  }
}

enum ColumnType { text, number, boolean, date, points, formula }
