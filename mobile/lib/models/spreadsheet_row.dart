class SpreadsheetRow {
  final String id;
  final Map<String, dynamic> cells;

  const SpreadsheetRow({required this.id, required this.cells});

  SpreadsheetRow copyWithCell(String columnId, dynamic value) => SpreadsheetRow(
        id: id,
        cells: {...cells, columnId: value},
      );

  factory SpreadsheetRow.fromMap(String id, Map<String, dynamic> data) {
    final values = Map<String, dynamic>.from(data['values'] as Map? ?? {});
    final name = data['fullName'] ?? data['full_name'] ?? data['name'];
    if (name != null) values['name'] = name;
    if (data.containsKey('points')) values['points'] = data['points'];
    return SpreadsheetRow(id: id, cells: values);
  }
}
