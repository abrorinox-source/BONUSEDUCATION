import 'package:flutter/material.dart';
import '../models/spreadsheet.dart';
import '../models/spreadsheet_row.dart';
import '../services/formula_engine.dart';

class SpreadsheetScreen extends StatefulWidget {
  const SpreadsheetScreen({super.key});

  @override
  State<SpreadsheetScreen> createState() => _SpreadsheetScreenState();
}

class _SpreadsheetScreenState extends State<SpreadsheetScreen> {
  final _engine = FormulaEngine();
  final _horizontal = ScrollController();

  final List<SpreadsheetColumn> _columns = [
    const SpreadsheetColumn(id: 'name', name: 'O\'quvchi', type: ColumnType.text, order: 0, editable: false),
    const SpreadsheetColumn(id: 'mashq', name: 'MASHQ', type: ColumnType.number, order: 1),
    const SpreadsheetColumn(id: 'lugat', name: 'LUG\'AT', type: ColumnType.number, order: 2),
    const SpreadsheetColumn(id: 'diktant', name: 'DIKTANT', type: ColumnType.number, order: 3),
    const SpreadsheetColumn(id: 'test', name: 'TEST', type: ColumnType.number, order: 4),
    const SpreadsheetColumn(id: 'total', name: 'TOTAL', type: ColumnType.formula, order: 5, editable: false, formula: 'MASHQ + LUG\'AT + DIKTANT + TEST'),
  ];

  final List<SpreadsheetRow> _rows = [
    const SpreadsheetRow(id: '1', cells: {'name': 'Ali Valiyev', 'mashq': 10, 'lugat': 8, 'diktant': 9, 'test': 20}),
    const SpreadsheetRow(id: '2', cells: {'name': 'Sardor Karimov', 'mashq': 8, 'lugat': 10, 'diktant': 8, 'test': 18}),
    const SpreadsheetRow(id: '3', cells: {'name': 'Bekzod Aliyev', 'mashq': 9, 'lugat': 7, 'diktant': 10, 'test': 19}),
    const SpreadsheetRow(id: '4', cells: {'name': 'Jasur Olimov', 'mashq': 7, 'lugat': 9, 'diktant': 8, 'test': 17}),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('10-A • Jadval'),
        actions: [
          IconButton(icon: const Icon(Icons.add_box_outlined), tooltip: 'Ustun qo\'shish', onPressed: _addColumn),
          IconButton(icon: const Icon(Icons.refresh), tooltip: 'Yangilash', onPressed: () => setState(() {})),
        ],
      ),
      body: Column(
        children: [
          _toolbar(),
          const Divider(height: 1),
          Expanded(child: _grid()),
        ],
      ),
    );
  }

  Widget _toolbar() => Container(
        height: 52,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        child: Row(children: [
          const Icon(Icons.table_chart_outlined),
          const SizedBox(width: 10),
          const Text('10-A', style: TextStyle(fontWeight: FontWeight.w700)),
          const Spacer(),
          FilledButton.icon(onPressed: _addColumn, icon: const Icon(Icons.add), label: const Text('Ustun')),
        ]),
      );

  Widget _grid() {
    final sorted = [..._columns]..sort((a, b) => a.order.compareTo(b.order));
    return Scrollbar(
      controller: _horizontal,
      thumbVisibility: true,
      child: SingleChildScrollView(
        controller: _horizontal,
        scrollDirection: Axis.horizontal,
        child: SingleChildScrollView(
          child: DataTable(
            columnSpacing: 0,
            headingRowHeight: 48,
            dataRowMinHeight: 48,
            dataRowMaxHeight: 56,
            border: TableBorder.all(color: Theme.of(context).dividerColor),
            columns: [
              const DataColumn(label: SizedBox(width: 42, child: Center(child: Text('#')))),
              ...sorted.map((column) => DataColumn(label: _header(column))),
            ],
            rows: _rows.asMap().entries.map((entry) {
              final index = entry.key;
              final row = entry.value;
              return DataRow(cells: [
                DataCell(SizedBox(width: 42, child: Center(child: Text('${index + 1}')))),
                ...sorted.map((column) => DataCell(_cell(row, column))),
              ]);
            }).toList(),
          ),
        ),
      ),
    );
  }

  Widget _header(SpreadsheetColumn column) {
    return SizedBox(
      width: column.id == 'name' ? 190 : 120,
      child: InkWell(
        onTap: () => _columnMenu(column),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          child: Row(children: [
            Expanded(child: Text(column.name, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w700))),
            const Icon(Icons.more_vert, size: 18),
          ]),
        ),
      ),
    );
  }

  Widget _cell(SpreadsheetRow row, SpreadsheetColumn column) {
    final value = column.isFormula ? _formulaValue(row, column) : row.cells[column.id];
    final width = column.id == 'name' ? 190.0 : 120.0;
    return SizedBox(
      width: width,
      child: column.editable
          ? InkWell(
              onTap: () => _editCell(row, column),
              child: Padding(padding: const EdgeInsets.symmetric(horizontal: 10), child: Text('${value ?? ''}')),
            )
          : Padding(padding: const EdgeInsets.symmetric(horizontal: 10), child: Text('${value ?? ''}', style: const TextStyle(fontWeight: FontWeight.w600))),
    );
  }

  dynamic _formulaValue(SpreadsheetRow row, SpreadsheetColumn column) {
    try {
      return _engine.evaluate(column.formula ?? '', row.cells, _columns).toStringAsFixed(0);
    } catch (_) {
      return '#ERROR';
    }
  }

  Future<void> _editCell(SpreadsheetRow row, SpreadsheetColumn column) async {
    final controller = TextEditingController(text: '${row.cells[column.id] ?? ''}');
    final result = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('${column.name} • ${row.cells['name']}'),
        content: TextField(controller: controller, autofocus: true, keyboardType: column.type == ColumnType.number ? TextInputType.number : TextInputType.text),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Bekor qilish')), FilledButton(onPressed: () => Navigator.pop(context, controller.text), child: const Text('Saqlash'))],
      ),
    );
    if (result != null) {
      setState(() {
        final value = column.type == ColumnType.number || column.type == ColumnType.points ? num.tryParse(result) ?? 0 : result;
        final index = _rows.indexWhere((r) => r.id == row.id);
        _rows[index] = row.copyWithCell(column.id, value);
      });
    }
  }

  Future<void> _addColumn() async {
    final nameController = TextEditingController();
    ColumnType type = ColumnType.number;
    final formulaController = TextEditingController();
    final created = await showDialog<SpreadsheetColumn>(
      context: context,
      builder: (context) => StatefulBuilder(builder: (context, setDialogState) => AlertDialog(
        title: const Text('Yangi ustun'),
        content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: nameController, decoration: const InputDecoration(labelText: 'Ustun nomi')),
          const SizedBox(height: 12),
          DropdownButtonFormField<ColumnType>(value: type, decoration: const InputDecoration(labelText: 'Turi'), items: ColumnType.values.map((t) => DropdownMenuItem(value: t, child: Text(t.name))).toList(), onChanged: (v) => setDialogState(() => type = v ?? ColumnType.number)),
          if (type == ColumnType.formula) ...[
            const SizedBox(height: 12),
            TextField(controller: formulaController, decoration: const InputDecoration(labelText: 'Formula', hintText: 'MASHQ + TEST * 2')),
          ],
        ])),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Bekor qilish')), FilledButton(onPressed: () { if (nameController.text.trim().isEmpty) return; Navigator.pop(context, SpreadsheetColumn(id: 'custom_${DateTime.now().millisecondsSinceEpoch}', name: nameController.text.trim(), type: type, order: _columns.length, editable: type != ColumnType.formula, formula: type == ColumnType.formula ? formulaController.text.trim() : null)); }, child: const Text('Yaratish'))],
      )),
    );
    if (created != null) setState(() => _columns.add(created));
  }

  void _columnMenu(SpreadsheetColumn column) {
    showModalBottomSheet(context: context, builder: (context) => SafeArea(child: Wrap(children: [
      ListTile(leading: const Icon(Icons.edit), title: const Text('Ustunni tahrirlash'), onTap: () { Navigator.pop(context); _renameColumn(column); }),
      ListTile(leading: const Icon(Icons.delete_outline), title: const Text('Ustunni o\'chirish'), onTap: () { Navigator.pop(context); if (column.id != 'name') setState(() => _columns.removeWhere((c) => c.id == column.id)); }),
    ])));
  }

  Future<void> _renameColumn(SpreadsheetColumn column) async {
    final controller = TextEditingController(text: column.name);
    final name = await showDialog<String>(context: context, builder: (context) => AlertDialog(title: const Text('Ustun nomi'), content: TextField(controller: controller, autofocus: true), actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Bekor qilish')), FilledButton(onPressed: () => Navigator.pop(context, controller.text.trim()), child: const Text('Saqlash'))]));
    if (name != null && name.isNotEmpty) setState(() { final i = _columns.indexWhere((c) => c.id == column.id); _columns[i] = SpreadsheetColumn(id: column.id, name: name, type: column.type, order: column.order, editable: column.editable, formula: column.formula); });
  }
}
