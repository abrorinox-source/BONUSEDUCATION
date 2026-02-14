# 🎓 Multi-Group Feature Implementation Guide

## 📊 Overview

This bot now supports **multiple groups** with separate Google Sheets tabs for each group. Teachers can manage multiple classes/groups in one bot.

---

## ✅ What's Been Completed

### 1. **Database Schema (Firebase)**
- ✅ Added `groups` collection
- ✅ Added `group_id` field to users
- ✅ Group management methods:
  - `create_group(group_data)` - Create new group
  - `get_group(group_id)` - Get group details
  - `get_all_groups(status)` - List all groups
  - `update_group(group_id, updates)` - Update group
  - `delete_group(group_id)` - Soft delete group
  - `get_teacher_groups(teacher_id)` - Get teacher's groups
- ✅ User filtering by group:
  - `get_all_users(group_id=...)` 
  - `get_ranking(group_id=...)`

### 2. **Google Sheets Manager**
- ✅ Multi-sheet support:
  - `fetch_all_data(sheet_name)` - Read from specific tab
  - `update_row(user_id, points, sheet_name)` - Update specific tab
  - `add_user(user_data, sheet_name)` - Add to specific tab
- ✅ Sheet management:
  - `get_sheet_names()` - List all tabs
  - `create_sheet_tab(sheet_name)` - Create new tab with headers

### 3. **UI Keyboards**
- ✅ Group management keyboards:
  - `get_groups_management_keyboard(teacher_id)` - Main menu
  - `get_groups_list_keyboard(groups, action)` - List groups
  - `get_group_detail_keyboard(group_id)` - Group actions
  - `get_group_selection_keyboard(groups)` - For student registration

---

## 🔧 How It Works

### **Architecture:**
```
Bot
 ├── Teacher creates groups
 │   ├── Group A → Google Sheets Tab "10-A"
 │   ├── Group B → Google Sheets Tab "11-B"
 │   └── Group C → Google Sheets Tab "9-C"
 │
 ├── Students register and select group
 │   └── User data saved with group_id
 │
 └── Sync works per group
     └── Each group syncs with its own sheet tab
```

### **Group Structure (Firebase):**
```javascript
{
  "group_id": "abc123",
  "name": "Class 10-A",
  "sheet_name": "10-A",
  "teacher_id": "123456789",
  "status": "active",
  "created_at": "2026-02-13..."
}
```

### **User with Group:**
```javascript
{
  "user_id": "987654321",
  "full_name": "John Doe",
  "group_id": "abc123",  // ← New field
  "points": 50,
  "role": "student",
  "status": "active"
}
```

---

## ⏳ TODO - Implementation Steps

### **Step 1: Teacher Group Management Handlers**
Need to create handlers in `handlers/teacher.py`:

```python
@router.callback_query(F.data == "settings:groups")
async def handle_groups_management(callback: CallbackQuery):
    """Show groups management menu"""
    # TODO: Implement

@router.callback_query(F.data == "groups:create")
async def handle_create_group(callback: CallbackQuery, state: FSMContext):
    """Start group creation process"""
    # TODO: Implement - Ask for group name and sheet name

@router.callback_query(F.data == "groups:list")
async def handle_groups_list(callback: CallbackQuery):
    """Show all teacher's groups"""
    # TODO: Implement

@router.callback_query(F.data.startswith("group_view:"))
async def handle_group_detail(callback: CallbackQuery):
    """Show group details"""
    # TODO: Implement
```

### **Step 2: Student Group Selection**
Update `handlers/registration.py`:

```python
# After student enters name/phone, show group selection:
@router.message(RegistrationStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    # ... existing code ...
    
    # Get all active groups
    groups = db.get_all_groups(status='active')
    
    if groups:
        await message.answer(
            "Select your class/group:",
            reply_markup=get_group_selection_keyboard(groups)
        )
        await state.set_state(RegistrationStates.waiting_for_group)
    else:
        # No groups - use default
        # ... continue registration ...
```

### **Step 3: Update Sync Methods**
Modify sync methods to work per group:

```python
async def smart_delta_sync(self, group_id: str = None):
    """Sync specific group or all groups"""
    if group_id:
        # Sync single group
        group = db.get_group(group_id)
        sheet_name = group['sheet_name']
        users = db.get_all_users(group_id=group_id, role='student', status='active')
        # ... sync with sheet_name ...
    else:
        # Sync all groups
        groups = db.get_all_groups(status='active')
        for group in groups:
            # ... sync each group ...
```

---

## 📝 Usage Example

### **Teacher creates group:**
1. Settings → Manage Groups → Create New Group
2. Enter group name: "Class 10-A"
3. Enter sheet name: "10-A"
4. Bot creates Firebase group + Google Sheets tab "10-A"

### **Student registers:**
1. /start
2. Enter name, phone
3. **Select group: "Class 10-A"**
4. User saved with `group_id`

### **Sync:**
- Force Sync → syncs all groups
- Each group syncs with its own sheet tab
- Students see only their group's ranking

---

## 🎯 Benefits

✅ **One bot for multiple classes**  
✅ **Separate sheets per group**  
✅ **Independent rankings per group**  
✅ **Easy to manage**  
✅ **Scalable**

---

## 🚀 Next Steps

1. **Implement teacher group management handlers** (20 min)
2. **Update student registration with group selection** (15 min)
3. **Update sync methods for multi-group** (20 min)
4. **Test with 2-3 groups** (10 min)
5. **Deploy to Render** (5 min)

**Total estimate:** ~70 minutes to complete

---

## 📌 Notes

- Default group can be created automatically for backward compatibility
- Teachers can switch between groups
- Students can only see their own group's data
- Each group has independent:
  - Student list
  - Points system
  - Ranking
  - Sync schedule

