/**
 * Google Sheets with SORT BUTTON
 * No trigger needed for button!
 */

/**
 * Create menu when sheet opens
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🏆 RANKING')
      .addItem('📊 Tartiblash', 'sortByPoints')
      .addSeparator()
      .addItem('✅ HAFTA → POINTS', 'addWeeklyPoints')
      .addToUi();
}

/**
 * Sort sheet by POINTS
 */
function sortByPoints() {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('sheet1');
    
    if (!sheet) {
      SpreadsheetApp.getUi().alert('sheet1 topilmadi!');
      return;
    }
    
    var lastRow = sheet.getLastRow();
    
    if (lastRow < 3) {
      SpreadsheetApp.getUi().alert('Kamida 2 ta talaba bo\'lishi kerak');
      return;
    }
    
    // Sort data range by column E (POINTS)
    var range = sheet.getRange(2, 1, lastRow - 1, 15); // A2:O(lastRow)
    range.sort({column: 5, ascending: false});
    
    // Show success message
    SpreadsheetApp.getActiveSpreadsheet().toast(
      'Tartiblandi!',
      '✅ RANKING',
      2
    );
    
  } catch (error) {
    SpreadsheetApp.getUi().alert('Xatolik: ' + error);
  }
}

/**
 * Add weekly points to main points
 */
function addWeeklyPoints() {
  try {
    var ui = SpreadsheetApp.getUi();
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('sheet1');
    
    if (!sheet) {
      ui.alert('sheet1 topilmadi!');
      return;
    }
    
    var lastRow = sheet.getLastRow();
    
    if (lastRow < 2) {
      ui.alert('Ma\'lumot yo\'q!');
      return;
    }
    
    // Confirm
    var response = ui.alert(
      'HAFTA → POINTS',
      'Barcha talabalarning HAFTA ballarini POINTS ga qo\'shasizmi?',
      ui.ButtonSet.YES_NO
    );
    
    if (response !== ui.Button.YES) {
      return;
    }
    
    var count = 0;
    var totalAdded = 0;
    
    // Get all data at once (faster than row-by-row)
    var dataRange = sheet.getRange(2, 1, lastRow - 1, 15); // A2:O(lastRow)
    var data = dataRange.getValues();
    
    var updates = [];
    
    // Process each student
    for (var i = 0; i < data.length; i++) {
      var row = data[i];
      var rowNum = i + 2;
      
      // Check if row has data (USER_ID not empty)
      if (!row[0]) {
        // Empty row - stop processing
        break;
      }
      
      var currentPoints = parseFloat(row[4]) || 0; // E (POINTS)
      var weeklyPoints = parseFloat(row[14]) || 0; // O (HAFTA)
      
      if (weeklyPoints === 0) continue;
      
      var newTotal = currentPoints + weeklyPoints;
      
      // Prepare update
      updates.push({
        row: rowNum,
        points: newTotal
      });
      
      count++;
      totalAdded += weeklyPoints;
    }
    
    // Apply all updates at once
    if (updates.length > 0) {
      var timestamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
      
      for (var i = 0; i < updates.length; i++) {
        var rowNum = updates[i].row;
        
        // Update POINTS
        sheet.getRange(rowNum, 5).setValue(updates[i].points);
        
        // Update timestamp
        sheet.getRange(rowNum, 6).setValue(timestamp);
      }
    }
    
    // Show result
    SpreadsheetApp.getActiveSpreadsheet().toast(
      count + ' ta talaba, ' + totalAdded + ' ball qo\'shildi',
      '✅ HAFTA Qo\'shildi',
      3
    );
    
  } catch (error) {
    SpreadsheetApp.getUi().alert('Xatolik: ' + error);
  }
}

/**
 * Auto timestamp when POINTS changed
 */
function onEdit(e) {
  if (!e) return;
  
  var sheet = e.source.getActiveSheet();
  var range = e.range;
  
  if (sheet.getName() !== 'sheet1') return;
  
  var col = range.getColumn();
  var row = range.getRow();
  
  if (row < 2) return;
  
  // Auto timestamp for column E (POINTS)
  if (col === 5) {
    var timestamp = Utilities.formatDate(
      new Date(), 
      Session.getScriptTimeZone(), 
      'yyyy-MM-dd HH:mm:ss'
    );
    sheet.getRange(row, 6).setValue(timestamp);
  }
}
