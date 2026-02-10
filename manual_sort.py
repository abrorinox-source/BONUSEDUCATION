"""
Manual Ranking - Sort Sheet by POINTS
Run this whenever you want to sort the sheet
"""

from sheets_manager import sheets_manager

def sort_by_points():
    service = sheets_manager.service
    sheet_id = sheets_manager.sheet_id
    
    print('📊 Sorting sheet by POINTS...')
    print()
    
    # Get sheet info
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sheet1_id = spreadsheet['sheets'][0]['properties']['sheetId']
    
    # Get student count
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range='sheet1!A2:A'
    ).execute()
    
    student_count = len(result.get('values', []))
    last_row = student_count + 1
    
    print(f'Students: {student_count}')
    print(f'Sorting rows 2-{last_row}...')
    print()
    
    # Sort by column E (POINTS) descending
    request = {
        'requests': [{
            'sortRange': {
                'range': {
                    'sheetId': sheet1_id,
                    'startRowIndex': 1,  # Row 2
                    'endRowIndex': last_row,
                    'startColumnIndex': 0,  # Column A
                    'endColumnIndex': 19  # Column S
                },
                'sortSpecs': [{
                    'dimensionIndex': 4,  # Column E (POINTS)
                    'sortOrder': 'DESCENDING'
                }]
            }
        }]
    }
    
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body=request
    ).execute()
    
    print('✅ Sheet sorted!')
    print()
    
    # Show top 5
    import time
    time.sleep(1)
    
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range='sheet1!B2:E6'
    ).execute()
    
    values = result.get('values', [])
    
    if values:
        print('🏆 TOP 5:')
        print('=' * 60)
        
        for i, row in enumerate(values, 1):
            if len(row) >= 4:
                name = row[0]
                points = row[3]
                medal = '🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else f'{i}.'
                print(f'{medal:3} {name:30} {points:>6} pts')
        
        print('=' * 60)
    
    print()
    print('✅ Done!')

if __name__ == '__main__':
    sort_by_points()
