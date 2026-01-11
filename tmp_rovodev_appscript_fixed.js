/**
 * Google Apps Script for Auto-Timestamp on Points Edit
 * DO NOT RUN MANUALLY - This triggers automatically on cell edits
 */

function onEdit(e) {
  // Check if event object exists (prevents manual run errors)
  if (!e) {
    Logger.log("⚠️ This function runs automatically when you edit cells. Do not run manually.");
    return;
  }
  
  try {
    // Get the edited range
    var sheet = e.source.getActiveSheet();
    var range = e.range;
    
    // Check if edited column is E (Points)
    if (range.getColumn() == 5) { // Column E = 5
      var row = range.getRow();
      
      // Skip header row
      if (row > 1) {
        // Update timestamp in column F
        var timestampCell = sheet.getRange(row, 6); // Column F = 6
        
        // Get current time in Tashkent timezone (UTC+5)
        var now = new Date();
        var tashkentTime = new Date(now.toLocaleString('en-US', {timeZone: 'Asia/Tashkent'}));
        
        // Force format with padding zeros
        var year = tashkentTime.getFullYear();
        var month = String(tashkentTime.getMonth() + 1).padStart(2, '0');
        var day = String(tashkentTime.getDate()).padStart(2, '0');
        var hours = String(tashkentTime.getHours()).padStart(2, '0');
        var minutes = String(tashkentTime.getMinutes()).padStart(2, '0');
        var seconds = String(tashkentTime.getSeconds()).padStart(2, '0');
        var formattedTime = year + '-' + month + '-' + day + ' ' + hours + ':' + minutes + ':' + seconds;
        
        timestampCell.setValue(formattedTime);
        timestampCell.setNumberFormat('@'); // Force text format
        
        Logger.log("✅ Timestamp updated for row " + row);
      }
    }
  } catch (error) {
    Logger.log("❌ Error: " + error.toString());
  }
}


/**
 * TEST FUNCTION - Run this manually to verify the script works
 */
function testTimestampUpdate() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  
  // Update timestamp for row 2 as a test
  var timestampCell = sheet.getRange(2, 6); // Row 2, Column F
  
  // Get current time in Tashkent timezone (UTC+5)
  var now = new Date();
  var tashkentTime = new Date(now.toLocaleString('en-US', {timeZone: 'Asia/Tashkent'}));
  
  // Force format with padding zeros
  var year = tashkentTime.getFullYear();
  var month = String(tashkentTime.getMonth() + 1).padStart(2, '0');
  var day = String(tashkentTime.getDate()).padStart(2, '0');
  var hours = String(tashkentTime.getHours()).padStart(2, '0');
  var minutes = String(tashkentTime.getMinutes()).padStart(2, '0');
  var seconds = String(tashkentTime.getSeconds()).padStart(2, '0');
  var formattedTime = year + '-' + month + '-' + day + ' ' + hours + ':' + minutes + ':' + seconds;
  
  timestampCell.setValue(formattedTime);
  timestampCell.setNumberFormat('@'); // Force text format
  
  Logger.log("✅ Test successful! Timestamp updated in row 2, column F");
  Logger.log("Tashkent time: " + formattedTime);
  Logger.log("Script timezone: " + Session.getScriptTimeZone());
  Logger.log("Using: Asia/Tashkent (UTC+5)");
  
  SpreadsheetApp.getUi().alert("✅ Test successful!\n\nTimestamp updated in row 2, column F.\nNow try editing a value in column E (points) to see automatic updates.");
}


/**
 * SETUP FUNCTION - Run once to create the trigger
 * This ensures onEdit runs automatically
 */
function setupTrigger() {
  // Delete existing triggers
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    ScriptApp.deleteTrigger(triggers[i]);
  }
  
  // Create new onEdit trigger
  ScriptApp.newTrigger('onEdit')
    .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet())
    .onEdit()
    .create();
  
  Logger.log("✅ Trigger created successfully!");
  SpreadsheetApp.getUi().alert("✅ Setup complete!\n\nThe auto-timestamp trigger is now active.\nTry editing a value in column E (points).");
}
