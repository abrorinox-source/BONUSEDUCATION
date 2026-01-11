# Google Sheets Setup Instructions

## 📊 Proper Timestamp Configuration

### Problem:
When you manually edit points in Google Sheets, the timestamp doesn't update automatically. This causes the bot to overwrite your changes with Firebase data.

### Solution:
Use a Google Sheets formula to automatically update the timestamp when points change.

---

## 🔧 Setup Instructions:

### Step 1: Open Your Google Sheet
Open the sheet linked in `config.py` (SHEET_ID)

### Step 2: Add Formula to Column F (last_updated)

Instead of manual timestamps, use this formula in cell **F2**:

**For English Google Sheets:**
```
=IF(E2="", "", TEXT(NOW(), "yyyy-MM-dd HH:mm:ss"))
```

**For Russian Google Sheets (Русский):**
```
=ЕСЛИ(E2=""; ""; ТЕКСТ(ТДАТА(); "yyyy-MM-dd HH:mm:ss"))
```

**For Uzbek/Russian region (semicolon separator):**
```
=ЕСЛИ(E2="";"";ТЕКСТ(ТДАТА();"yyyy-MM-dd HH:mm:ss"))
```

**What this does:**
- Automatically updates timestamp when you edit column E (points)
- Uses the correct format: `2025-01-10 12:30:45`
- Leaves blank if no points

### Step 3: Apply to All Rows

1. Click cell **F2**
2. Copy the formula (Ctrl+C or Cmd+C)
3. Select **F3** to **F1000** (or your last row)
4. Paste (Ctrl+V or Cmd+V)

---

## ⚠️ IMPORTANT NOTE:

**This formula has a limitation:**
- Google Sheets formulas only recalculate when:
  - The sheet is opened/edited
  - Cell is manually edited
  - On periodic auto-recalculation (random intervals)

**Better Solution Below** ⬇️

---

## 🎯 RECOMMENDED: Use Apps Script (Best Solution)

This will ALWAYS update timestamp when points change:

### Step 1: Open Script Editor
1. In Google Sheets, click **Extensions** → **Apps Script**
2. Delete any existing code
3. Paste this code:

```javascript
function onEdit(e) {
  // Get the edited range
  var sheet = e.source.getActiveSheet();
  var range = e.range;
  
  // Check if edited column is E (Points)
  if (range.getColumn() == 5) { // Column E
    var row = range.getRow();
    
    // Skip header row
    if (row > 1) {
      // Update timestamp in column F
      var timestampCell = sheet.getRange(row, 6); // Column F
      var now = new Date();
      var formattedTime = Utilities.formatDate(now, Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm:ss");
      timestampCell.setValue(formattedTime);
    }
  }
}
```

### Step 2: Save and Authorize
1. Click **Save** (💾 icon)
2. Name it: "Auto Timestamp"
3. Click **Run** → Select `onEdit`
4. Click **Review permissions** → Allow access

### Step 3: Test
1. Go back to your Sheet
2. Change any value in column E (points)
3. Column F should automatically update! ✅

---

## 📋 Column Structure:

| A | B | C | D | E | F |
|---|---|---|---|---|---|
| user_id | full_name | phone | username | points | last_updated |
| 123456 | John Doe | +998... | @john | 150 | 2025-01-10 12:30:45 |

---

## ✅ After Setup:

**Without Apps Script (Formula only):**
- ⚠️ Timestamp updates sometimes (unreliable)
- Manual edit required to force update

**With Apps Script (Recommended):**
- ✅ Timestamp updates immediately when points change
- ✅ Bot correctly syncs: Sheets → Firebase
- ✅ Your manual edits are preserved!

---

## 🧪 Testing:

1. Edit a student's points in Sheets
2. Check if timestamp updated automatically
3. Restart bot
4. Check CMD logs: Should show "✅ Sheets → Firebase"
5. Check Firebase: Should have your edited points!

---

## 📞 Support:

If timestamp still not working:
- Check Apps Script is authorized
- Check column E is actually column 5 (count from A=1)
- Check timezone in Apps Script settings

---

**With Apps Script, your manual edits will ALWAYS be preserved!** 🎉
