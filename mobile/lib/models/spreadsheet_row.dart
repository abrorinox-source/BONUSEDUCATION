class SpreadsheetRow {
  final String id;
  final Map<String, dynamic> cells;

  const SpreadsheetRow({required this.id, required this.cells});

  SpreadsheetRow copyWithCell(String columnId, dynamic value) => SpreadsheetRow(
        id: id,
        cells: {...cells, columnId: value},
      );

  factory SpreadsheetRow.fromMap(String id, Map<String, dynamic> data) => SpreadsheetRow(
        id: id,
        cells: Map<String, dynamic>.from(data['values'] as Map? ?? {}),
      );
}
