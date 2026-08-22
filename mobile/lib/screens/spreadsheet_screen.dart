import 'package:flutter/material.dart';
import '../models/spreadsheet.dart';
import '../models/spreadsheet_row.dart';
import '../services/spreadsheet_service.dart';
import '../services/formula_engine_v2.dart';

class SpreadsheetScreen extends StatefulWidget {
  final String groupId;
  const SpreadsheetScreen({super.key, required this.groupId});
  @override
  State<SpreadsheetScreen> createState() => _SpreadsheetScreenState();
}

class _SpreadsheetScreenState extends State<SpreadsheetScreen> {
  final _service = SpreadsheetService();
  final _engine = FormulaEngineV2();
  final _horizontal = ScrollController();

  @override
  void dispose() { _horizontal.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Spreadsheet'), actions: [
      IconButton(icon: const Icon(Icons.add_box_outlined), tooltip: 'Ustun qo\'shish', onPressed: _addColumn),
    ]),
    body: StreamBuilder<List<Map<String,dynamic>>>(
      stream: _service.watchColumns(widget.groupId),
      builder: (context, columnsSnap) {
        if (columnsSnap.hasError) return Center(child: Text('Ustunlar xatosi: ${columnsSnap.error}'));
        if (!columnsSnap.hasData) return const Center(child: CircularProgressIndicator());
        return StreamBuilder<List<Map<String,dynamic>>>(
          stream: _service.watchStudents(widget.groupId),
          builder: (context, studentsSnap) {
            if (studentsSnap.hasError) return Center(child: Text('Studentlar xatosi: ${studentsSnap.error}'));
            if (!studentsSnap.hasData) return const Center(child: CircularProgressIndicator());
            final columns = columnsSnap.data!.map((m) => SpreadsheetColumn.fromMap(m['id'] as String, m)).toList();
            final rows = studentsSnap.data!.map((m) => SpreadsheetRow.fromMap(m['id'] as String, m)).toList();
            columns.sort((a,b)=>a.order.compareTo(b.order));
            return _grid(columns, rows);
          },
        );
      },
    ),
  );

  Widget _grid(List<SpreadsheetColumn> columns, List<SpreadsheetRow> rows) =>
    Scrollbar(controller: _horizontal, thumbVisibility: true, child: SingleChildScrollView(
      controller: _horizontal, scrollDirection: Axis.horizontal,
      child: DataTable(
        columnSpacing: 0, border: TableBorder.all(color: Theme.of(context).dividerColor),
        columns: [const DataColumn(label: SizedBox(width:42,child:Center(child:Text('#')))), ...columns.map(_header)],
        rows: rows.asMap().entries.map((e) => DataRow(cells: [
          DataCell(SizedBox(width:42,child:Center(child:Text('${e.key+1}')))),
          ...columns.map((c)=>DataCell(_cell(e.value,c,columns)))
        ])).toList(),
      ),
    ));

  DataColumn _header(SpreadsheetColumn c) => DataColumn(label: SizedBox(width:c.id=='name'?190:120,child:InkWell(
    onTap: ()=>_columnMenu(c), child: Padding(padding:const EdgeInsets.symmetric(horizontal:10),child:Row(children:[Expanded(child:Text(c.name,overflow:TextOverflow.ellipsis,style:const TextStyle(fontWeight:FontWeight.bold))),const Icon(Icons.more_vert,size:18)])))));

  Widget _cell(SpreadsheetRow row, SpreadsheetColumn c, List<SpreadsheetColumn> columns) {
    dynamic value=row.cells[c.id];
    if(c.isFormula){ try { value=_engine.evaluate(c.formula??'',row.cells,columns).toStringAsFixed(0); } catch(_){ value='#ERROR'; } }
    return SizedBox(width:c.id=='name'?190:120,child:c.editable?InkWell(
      onTap:()=>_editCell(row,c),child:Padding(padding:const EdgeInsets.symmetric(horizontal:10),child:Text('${value??''}')),
    ):Padding(padding:const EdgeInsets.symmetric(horizontal:10),child:Text('${value??''}',style:const TextStyle(fontWeight:FontWeight.w600))));
  }

  Future<void> _editCell(SpreadsheetRow row, SpreadsheetColumn c) async {
    final controller=TextEditingController(text:'${row.cells[c.id]??''}');
    final result=await showDialog<String>(context:context,builder:(_)=>AlertDialog(title:Text(c.name),content:TextField(controller:controller,autofocus:true,keyboardType:c.type==ColumnType.number||c.type==ColumnType.points?TextInputType.number:TextInputType.text),actions:[TextButton(onPressed:()=>Navigator.pop(context),child:const Text('Bekor qilish')),FilledButton(onPressed:()=>Navigator.pop(context,controller.text),child:const Text('Saqlash'))]));
    if(result==null)return;
    dynamic value=(c.type==ColumnType.number||c.type==ColumnType.points)?num.tryParse(result):result;
    if(value==null && (c.type==ColumnType.number||c.type==ColumnType.points)) { if(mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Son kiriting'))); return; }
    await _service.setCell(groupId:widget.groupId,studentId:row.id,columnId:c.id,value:value);
  }

  Future<void> _addColumn() async {
    final name=TextEditingController(); final formula=TextEditingController(); ColumnType type=ColumnType.number;
    final result=await showDialog<({String name,ColumnType type,String? formula})>(context:context,builder:(ctx)=>StatefulBuilder(builder:(ctx,setState)=>AlertDialog(
      title:const Text('Yangi ustun'),content:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,children:[TextField(controller:name,decoration:const InputDecoration(labelText:'Nomi')),DropdownButtonFormField<ColumnType>(value:type,items:ColumnType.values.map((t)=>DropdownMenuItem(value:t,child:Text(t.name))).toList(),onChanged:(v)=>setState(()=>type=v??ColumnType.number)),if(type==ColumnType.formula)TextField(controller:formula,decoration:const InputDecoration(labelText:'Formula'))])),
      actions:[TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Bekor qilish')),FilledButton(onPressed:()=>name.text.trim().isEmpty?null:Navigator.pop(ctx,(name:name.text.trim(),type:type,formula:type==ColumnType.formula?formula.text.trim():null)),child:const Text('Yaratish'))])));
    if(result!=null) await _service.createColumn(groupId:widget.groupId,name:result.name,type:result.type.name,formula:result.formula);
  }

  void _columnMenu(SpreadsheetColumn c)=>showModalBottomSheet(context:context,builder:(ctx)=>SafeArea(child:Wrap(children:[
    ListTile(leading:const Icon(Icons.edit),title:const Text('Nomini o\'zgartirish'),onTap:(){Navigator.pop(ctx);_rename(c);}),
    ListTile(leading:const Icon(Icons.delete),title:const Text('O\'chirish'),onTap:(){Navigator.pop(ctx);_service.deleteColumn(widget.groupId,c.id);}),
  ])));

  Future<void> _rename(SpreadsheetColumn c) async { final t=TextEditingController(text:c.name); final n=await showDialog<String>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Ustun nomi'),content:TextField(controller:t),actions:[TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Bekor qilish')),FilledButton(onPressed:()=>Navigator.pop(ctx,t.text.trim()),child:const Text('Saqlash'))])); if(n!=null&&n.isNotEmpty) await _service.renameColumn(widget.groupId,c.id,n); }
}
