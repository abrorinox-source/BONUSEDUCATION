"""
Google Sheets Manager
Handles all Google Sheets operations and synchronization
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime, timezone
import config
from database import db
import os
import json


class GoogleSheetsManager:
    """Manages Google Sheets operations"""
    
    def __init__(self):
        """Initialize Google Sheets API"""
        # Try to get credentials from environment variable first (for Render)
        firebase_creds = os.getenv('FIREBASE_CREDENTIALS')
        
        if firebase_creds:
            # Use credentials from environment variable
            cred_dict = json.loads(firebase_creds)
            self.credentials = service_account.Credentials.from_service_account_info(
                cred_dict,
                scopes=config.GOOGLE_SCOPES
            )
        else:
            # Use credentials from file (for local development)
            self.credentials = service_account.Credentials.from_service_account_file(
                config.FIREBASE_KEY_PATH,
                scopes=config.GOOGLE_SCOPES
            )
        
        self.service = build('sheets', 'v4', credentials=self.credentials)
        self.sheet_id = config.SHEET_ID
        self.sync_lock = asyncio.Lock()
        self.background_task = None  # Track the background sync task
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SHEET/TAB MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_sheet_names(self) -> List[str]:
        """Get all sheet names (tabs) from the spreadsheet"""
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
            sheets = spreadsheet.get('sheets', [])
            return [sheet['properties']['title'] for sheet in sheets]
        except HttpError as e:
            print(f"Error getting sheet names: {e}")
            return []
    
    def create_sheet_tab(self, sheet_name: str) -> bool:
        """Create a new sheet tab with header row"""
        try:
            # Check if sheet already exists
            existing_sheets = self.get_sheet_names()
            if sheet_name in existing_sheets:
                print(f"Sheet '{sheet_name}' already exists")
                return True
            
            # Create new sheet
            request = {
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }
            
            body = {'requests': [request]}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body=body
            ).execute()
            
            # Add header row
            header_values = [['User ID', 'Full Name', 'Phone', 'Username', 'Points', 'Last Updated']]
            header_body = {'values': header_values}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=f'{sheet_name}!A1:F1',
                valueInputOption='RAW',
                body=header_body
            ).execute()
            
            print(f"✅ Created new sheet tab: {sheet_name}")
            return True
        
        except HttpError as e:
            print(f"Error creating sheet tab: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # READ OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def fetch_all_data(self, sheet_name: str = 'Sheet1') -> List[Dict[str, Any]]:
        """Fetch all data from Google Sheets (specific sheet/tab)"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=f'{sheet_name}!A2:F'  # Skip header row
            ).execute()
            
            rows = result.get('values', [])
            users = []
            
            for row in rows:
                if len(row) < 5:  # Skip incomplete rows
                    continue
                
                try:
                    # Skip rows with empty user_id or full_name
                    if not row[0] or not row[0].strip():
                        continue
                    if not row[1] or not row[1].strip():
                        continue
                    
                    # Parse points with validation
                    points_value = 0
                    if len(row) > 4 and row[4] and row[4].strip():
                        try:
                            points_value = int(row[4])
                        except ValueError:
                            print(f"Warning: Invalid points value '{row[4]}' for user {row[0]}, defaulting to 0")
                            points_value = 0
                    
                    user_data = {
                        'user_id': str(row[0]).strip(),
                        'full_name': row[1].strip(),
                        'phone': row[2].strip() if len(row) > 2 and row[2] else '',
                        'username': row[3].strip() if len(row) > 3 and row[3] else '',
                        'points': points_value,
                        'last_updated': row[5].strip() if len(row) > 5 and row[5] else ''
                    }
                    users.append(user_data)
                except (ValueError, IndexError) as e:
                    print(f"Error parsing row: {row}, Error: {e}")
                    continue
            
            return users
        
        except HttpError as e:
            print(f"Google Sheets API error: {e}")
            return []
    
    # ═══════════════════════════════════════════════════════════════════════════
    # WRITE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def update_row(self, user_id: str, points: int, sheet_name: str = 'Sheet1') -> bool:
        """Update specific user's points in Sheets"""
        try:
            # Find the row for this user
            all_data = self.fetch_all_data(sheet_name=sheet_name)
            row_index = None
            
            for idx, user in enumerate(all_data):
                if user['user_id'] == user_id:
                    row_index = idx + 2  # +2 because of header and 0-index
                    break
            
            if row_index is None:
                print(f"User {user_id} not found in Sheets")
                return False
            
            # Update the points column (E) and last_updated (F)
            range_name = f'{sheet_name}!E{row_index}:F{row_index}'
            values = [[points, datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')]]
            
            body = {'values': values}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return True
        
        except HttpError as e:
            print(f"Error updating Sheets: {e}")
            return False
    
    def add_user(self, user_data: Dict[str, Any], sheet_name: str = 'Sheet1') -> bool:
        """Add new user to Google Sheets - finds first empty row after header"""
        try:
            # Get all data including empty rows
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=f'{sheet_name}!A2:A'  # Get all user_id column starting from row 2
            ).execute()
            
            rows = result.get('values', [])
            
            # Find first empty row (row with empty user_id)
            target_row = 2  # Start from row 2 (after header)
            for idx, row in enumerate(rows):
                # If row is completely empty or first cell is empty
                if not row or not row[0] or not row[0].strip():
                    target_row = idx + 2  # +2 because enumerate starts at 0 and we start at row 2
                    break
                target_row = idx + 3  # Next row after last filled row
            
            # Prepare data
            values = [[
                user_data.get('user_id', ''),
                user_data.get('full_name', ''),
                user_data.get('phone', ''),
                user_data.get('username', ''),
                user_data.get('points', 0),
                datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            ]]
            
            body = {'values': values}
            
            # Insert at specific row
            range_name = f'{sheet_name}!A{target_row}:F{target_row}'
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"✅ Added user to {sheet_name} row {target_row}: {user_data.get('full_name', 'Unknown')}")
            return True
        
        except HttpError as e:
            print(f"Error adding user to Sheets: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user from Google Sheets"""
        try:
            all_data = self.fetch_all_data()
            row_index = None
            
            for idx, user in enumerate(all_data):
                if user['user_id'] == user_id:
                    row_index = idx + 1  # +1 for header
                    break
            
            if row_index is None:
                return False
            
            # Delete the row
            request = {
                'deleteDimension': {
                    'range': {
                        'sheetId': 0,
                        'dimension': 'ROWS',
                        'startIndex': row_index,
                        'endIndex': row_index + 1
                    }
                }
            }
            
            body = {'requests': [request]}
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body=body
            ).execute()
            
            return True
        
        except HttpError as e:
            print(f"Error deleting from Sheets: {e}")
            return False
    
    def bulk_update(self, updates: List[Dict[str, Any]]) -> bool:
        """Bulk update multiple rows"""
        try:
            data = []
            for update in updates:
                row_index = update['row_index']
                values = [
                    update['user_id'],
                    update['full_name'],
                    update['phone'],
                    update['username'],
                    update['points'],
                    datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                ]
                
                data.append({
                    'range': f'Sheet1!A{row_index}:F{row_index}',
                    'values': [values]
                })
            
            body = {
                'valueInputOption': 'RAW',
                'data': data
            }
            
            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=self.sheet_id,
                body=body
            ).execute()
            
            return True
        
        except HttpError as e:
            print(f"Error bulk updating Sheets: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SMART DELTA SYNC - MULTI-GROUP SUPPORT
    # ═══════════════════════════════════════════════════════════════════════════
    
    async def smart_delta_sync(self) -> Dict[str, int]:
        """
        Multi-group sync wrapper - syncs all groups
        """
        groups = db.get_all_groups(status='active')
        
        if not groups:
            # No groups - use legacy single sheet sync
            print("⚠️ No groups found, using default Sheet1")
            return await self._smart_delta_sync_single('Sheet1', None)
        
        # Sync all groups
        total_stats = {'updated': 0, 'added': 0, 'deleted': 0, 'errors': 0, 'skipped': 0}
        
        for group in groups:
            print(f"\n📚 Syncing: {group['name']} ({group['sheet_name']})")
            try:
                stats = await self._smart_delta_sync_single(group['sheet_name'], group['group_id'])
                for key in total_stats:
                    total_stats[key] += stats.get(key, 0)
            except Exception as e:
                print(f"❌ Error syncing {group['name']}: {e}")
                total_stats['errors'] += 1
        
        print(f"\n🔄 Sync complete: {total_stats['updated']} updated, {total_stats['added']} added")
        return total_stats
    
    async def _smart_delta_sync_single(self, sheet_name: str, group_id: Optional[str]) -> Dict[str, int]:
        """
        Timestamp-Based Bidirectional Sync
        Latest modification wins based on last_updated timestamp
        """
        async with self.sync_lock:
            stats = {'updated': 0, 'added': 0, 'deleted': 0, 'errors': 0, 'skipped': 0}
            
            try:
                # Get all active Firebase users (filtered by group if provided)
                firebase_active_users = db.get_all_users(role='student', status='active', group_id=group_id)
                firebase_active_ids = {u['user_id'] for u in firebase_active_users}
                
                # Fetch from Sheets (specific sheet tab)
                sheets_data = self.fetch_all_data(sheet_name=sheet_name)
                sheets_user_ids = {row['user_id'] for row in sheets_data}
                
                # Remove deleted/banned users from Sheets
                users_to_delete = sheets_user_ids - firebase_active_ids
                for user_id in users_to_delete:
                    # Check if user exists in Firebase but not active
                    user = db.get_user(user_id)
                    if user and user.get('status') in ['deleted', 'banned']:
                        # Note: delete_user doesn't support sheet_name yet, skip for now
                        # self.delete_user(user_id, sheet_name=sheet_name)
                        stats['deleted'] += 1
                        print(f"🗑️ Would remove {user.get('status')} user from Sheets: {user.get('full_name', user_id)}")
                
                # Add new active Firebase users to Sheets (e.g., restored users)
                new_firebase_users = firebase_active_ids - sheets_user_ids
                for user_id in new_firebase_users:
                    user = db.get_user(user_id)
                    if user:
                        self.add_user({
                            'user_id': user_id,
                            'full_name': user['full_name'],
                            'phone': user.get('phone', ''),
                            'username': user.get('username', ''),
                            'points': user.get('points', 0)
                        }, sheet_name=sheet_name)
                        stats['added'] += 1
                        print(f"✅ Added active Firebase user to {sheet_name}: {user['full_name']}")
                
                # Sync Sheets data with Firebase
                for row in sheets_data:
                    user_id = row['user_id']
                    sheets_points = row['points']
                    user_name = row['full_name']
                    sheets_last_updated = row.get('last_updated', '')
                    
                    # Get from Firebase
                    user = db.get_user(user_id)
                    
                    if not user:
                        # New user in Sheets - add to Firebase
                        db.create_user(user_id, {
                            'full_name': user_name,
                            'phone': row.get('phone', ''),
                            'username': row.get('username', ''),
                            'points': sheets_points,
                            'status': 'active',
                            'role': 'student'
                        })
                        stats['added'] += 1
                        print(f"✅ Added new user from Sheets: {user_name}")
                        continue
                    
                    # User exists - compare timestamps
                    firebase_points = user.get('points', 0)
                    firebase_last_updated = user.get('last_updated')
                    
                    # Parse timestamps
                    sheets_timestamp = self._parse_timestamp(sheets_last_updated)
                    firebase_timestamp = self._parse_firebase_timestamp(firebase_last_updated)
                    
                    # Check if points are the same
                    if firebase_points == sheets_points:
                        # Points are same - check if timestamps are also close
                        # If both have timestamps and they're similar (within 5 seconds), skip
                        if sheets_timestamp and firebase_timestamp:
                            time_diff = abs((sheets_timestamp - firebase_timestamp).total_seconds())
                            if time_diff < 5:  # Within 5 seconds - skip
                                stats['skipped'] += 1
                                continue
                        # If points same but no timestamp info, skip anyway
                        stats['skipped'] += 1
                        continue
                    
                    # Points are different - check which is newer
                    if sheets_timestamp and firebase_timestamp:
                        if sheets_timestamp > firebase_timestamp:
                            # Sheets is newer - update Firebase (points + names from Sheets)
                            db.update_user(user_id, {
                                'points': sheets_points,
                                'full_name': row['full_name'],
                                'phone': row.get('phone', ''),
                                'username': row.get('username', '')
                            })
                            db.log_manual_edit(user_id, user_name, firebase_points, sheets_points)
                            stats['updated'] += 1
                            print(f"✅ Sheets → Firebase: {user_name} ({firebase_points} → {sheets_points})")
                        
                        elif firebase_timestamp > sheets_timestamp:
                            # Firebase is newer - update Sheets points, but update names from Sheets anyway
                            self.update_row(user_id, firebase_points, sheet_name=sheet_name)
                            # Also update names from Sheets (names always from Sheets)
                            db.update_user(user_id, {
                                'full_name': row['full_name'],
                                'phone': row.get('phone', ''),
                                'username': row.get('username', '')
                            })
                            stats['updated'] += 1
                            print(f"✅ Firebase → Sheets (points), Sheets → Firebase (names): {user_name}")
                        
                        else:
                            # Same timestamp but different points (conflict)
                            # Use Firebase points, Sheets names
                            self.update_row(user_id, firebase_points, sheet_name=sheet_name)
                            db.update_user(user_id, {
                                'full_name': row['full_name'],
                                'phone': row.get('phone', ''),
                                'username': row.get('username', '')
                            })
                            stats['updated'] += 1
                            print(f"⚠️ Conflict resolved (Firebase points, Sheets names): {user_name} → {firebase_points}")
                    
                    elif sheets_timestamp:
                        # Only Sheets has timestamp - use Sheets data
                        db.update_user(user_id, {
                            'points': sheets_points,
                            'full_name': row['full_name'],
                            'phone': row.get('phone', ''),
                            'username': row.get('username', '')
                        })
                        db.log_manual_edit(user_id, user_name, firebase_points, sheets_points)
                        stats['updated'] += 1
                        print(f"✅ Sheets → Firebase: {user_name} ({firebase_points} → {sheets_points})")
                    
                    elif firebase_timestamp:
                        # Only Firebase has timestamp - use Firebase points, Sheets names
                        self.update_row(user_id, firebase_points, sheet_name=sheet_name)
                        db.update_user(user_id, {
                            'full_name': row['full_name'],
                            'phone': row.get('phone', ''),
                            'username': row.get('username', '')
                        })
                        stats['updated'] += 1
                        print(f"✅ Firebase → Sheets (points), Sheets → Firebase (names): {user_name}")
                    
                    else:
                        # No timestamps - use Firebase points, Sheets names
                        self.update_row(user_id, firebase_points, sheet_name=sheet_name)
                        db.update_user(user_id, {
                            'full_name': row['full_name'],
                            'phone': row.get('phone', ''),
                            'username': row.get('username', '')
                        })
                        stats['updated'] += 1
                        print(f"⚠️ No timestamps, using Firebase points, Sheets names: {user_name} → {firebase_points}")
                
                # Update sync statistics
                settings = db.get_settings()
                sync_stats = settings.get('sync_statistics', {
                    'total_syncs': 0,
                    'successful_syncs': 0,
                    'failed_syncs': 0,
                    'last_error': None
                })
                
                sync_stats['total_syncs'] = sync_stats.get('total_syncs', 0) + 1
                sync_stats['successful_syncs'] = sync_stats.get('successful_syncs', 0) + 1
                
                db.update_settings({
                    'last_sync_time': datetime.now(timezone.utc).isoformat(),
                    'sync_statistics': sync_stats
                })
                
                print(f"🔄 Sync complete: {stats['updated']} updated, {stats['added']} added, {stats['skipped']} skipped")
                return stats
            
            except Exception as e:
                print(f"❌ Sync error: {e}")
                stats['errors'] += 1
                
                # Update failure statistics
                settings = db.get_settings()
                sync_stats = settings.get('sync_statistics', {
                    'total_syncs': 0,
                    'successful_syncs': 0,
                    'failed_syncs': 0,
                    'last_error': None
                })
                
                sync_stats['total_syncs'] = sync_stats.get('total_syncs', 0) + 1
                sync_stats['failed_syncs'] = sync_stats.get('failed_syncs', 0) + 1
                sync_stats['last_error'] = str(e)
                
                db.update_settings({
                    'sync_statistics': sync_stats
                })
                
                return stats
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse Sheets timestamp string to datetime (assumes local timezone UTC+5, converts to UTC)"""
        if not timestamp_str:
            return None
        
        try:
            # Clean up timestamp string (remove extra spaces, etc)
            timestamp_str = str(timestamp_str).strip()
            
            # Try multiple formats (including European/Russian formats)
            formats = [
                '%Y-%m-%d %H:%M:%S',       # 2026-02-13 20:33:48 (Standard format)
                '%Y-%m-%d %H:%M:%S.%f',    # With microseconds
                '%Y-%m-%d',                # Date only
                '%d/%m/%Y %H:%M:%S',       # European: 10/01/2025 14:30:45
                '%d/%m/%Y',                # European date: 10/01/2025
                '%d.%m.%Y %H:%M:%S',       # Russian: 10.01.2025 14:30:45
                '%d.%m.%Y',                # Russian date: 10.01.2025
                '%d.%m.%Y %H:%M',          # Russian short: 10.01.2025 14:30
            ]
            
            for fmt in formats:
                try:
                    # Parse the timestamp
                    dt = datetime.strptime(timestamp_str, fmt)
                    
                    # Sheets timestamps are in LOCAL timezone (UTC+5 for Toshkent/Uzbekistan)
                    # Convert from local to UTC by subtracting 5 hours
                    from datetime import timedelta
                    utc_dt = dt - timedelta(hours=5)
                    
                    # Make UTC-aware
                    return utc_dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            
            print(f"⚠️ Could not parse timestamp '{timestamp_str}' with any known format")
            return None
        except Exception as e:
            print(f"❌ Error parsing timestamp '{timestamp_str}': {e}")
            return None
    
    def _parse_firebase_timestamp(self, timestamp) -> Optional[datetime]:
        """Parse Firebase timestamp to datetime (UTC-aware)"""
        if not timestamp:
            return None
        
        try:
            # Firebase SERVER_TIMESTAMP returns DatetimeWithNanoseconds
            if hasattr(timestamp, 'timestamp'):
                # Use UTC explicitly
                dt = datetime.fromtimestamp(timestamp.timestamp(), tz=timezone.utc)
                return dt
            
            # If it's already a datetime
            if isinstance(timestamp, datetime):
                # If it has timezone info
                if timestamp.tzinfo is not None:
                    # If already UTC, return as-is
                    if timestamp.tzinfo == timezone.utc:
                        return timestamp
                    # Otherwise convert to UTC
                    utc_dt = timestamp.astimezone(timezone.utc)
                    # Remove timezone and re-add to avoid DST issues
                    naive_utc = utc_dt.replace(tzinfo=None)
                    return naive_utc.replace(tzinfo=timezone.utc)
                # If naive (no timezone), assume it's already UTC
                return timestamp.replace(tzinfo=timezone.utc)
            
            # If it's a string
            if isinstance(timestamp, str):
                return self._parse_timestamp(timestamp)
            
            return None
        except Exception as e:
            print(f"❌ Error parsing Firebase timestamp: {e}")
            return None
    
    async def sync_firebase_to_sheets(self) -> Dict[str, int]:
        """
        One-way sync: Firebase → Sheets
        Force all Firebase data to Sheets
        """
        async with self.sync_lock:
            stats = {'updated': 0, 'added': 0, 'deleted': 0, 'errors': 0}
            
            try:
                # Get all Firebase users (only active students)
                firebase_users = db.get_all_users(role='student', status='active')
                firebase_user_ids = {user['user_id'] for user in firebase_users}
                
                # Get all Sheets data
                sheets_data = self.fetch_all_data()
                sheets_user_ids = {row['user_id'] for row in sheets_data}
                
                # Sync active users
                for user in firebase_users:
                    user_id = user['user_id']
                    
                    if user_id in sheets_user_ids:
                        # Update existing
                        self.update_row(user_id, user['points'])
                        stats['updated'] += 1
                    else:
                        # Add new
                        self.add_user(user)
                        stats['added'] += 1
                
                # Remove deleted/banned users from Sheets
                users_to_delete = sheets_user_ids - firebase_user_ids
                for user_id in users_to_delete:
                    self.delete_user(user_id)
                    stats['deleted'] += 1
                    print(f"🗑️ Removed inactive user from Sheets: {user_id}")
                
                print(f"✅ Firebase → Sheets sync: {stats['updated']} updated, {stats['added']} added, {stats['deleted']} deleted")
                return stats
            
            except Exception as e:
                print(f"❌ Firebase → Sheets error: {e}")
                stats['errors'] += 1
                return stats
    
    async def sync_sheets_to_firebase(self) -> Dict[str, int]:
        """
        Hybrid sync: Sheets → Firebase
        - Names/phones from Sheets (always win)
        - Points based on timestamp (latest wins)
        """
        async with self.sync_lock:
            stats = {'updated': 0, 'added': 0, 'errors': 0}
            
            try:
                # Get all Sheets data
                sheets_data = self.fetch_all_data()
                
                for row in sheets_data:
                    user_id = row['user_id']
                    user = db.get_user(user_id)
                    
                    if user:
                        # Update existing user
                        # ALWAYS update names/phones from Sheets
                        update_data = {
                            'full_name': row['full_name'],
                            'phone': row.get('phone', ''),
                            'username': row.get('username', '')
                        }
                        
                        # For POINTS - check timestamps (latest wins)
                        sheets_points = row['points']
                        firebase_points = user.get('points', 0)
                        sheets_timestamp_str = row.get('last_updated', '')
                        firebase_timestamp_raw = user.get('last_updated')
                        
                        sheets_timestamp = self._parse_timestamp(sheets_timestamp_str)
                        firebase_timestamp = self._parse_firebase_timestamp(firebase_timestamp_raw)
                        
                        # DEBUG: Show raw and parsed timestamps
                        print(f"\n👤 User: {user['full_name']} (ID: {user_id})")
                        print(f"   📄 Sheets: {sheets_points} pts | Timestamp: '{sheets_timestamp_str}' → {sheets_timestamp}")
                        print(f"   🔥 Firebase: {firebase_points} pts | Timestamp: {firebase_timestamp_raw} → {firebase_timestamp}")
                        
                        # Compare timestamps for points only
                        if sheets_timestamp and firebase_timestamp:
                            if sheets_timestamp > firebase_timestamp:
                                # Sheets is newer - use Sheets points
                                update_data['points'] = sheets_points
                                print(f"   ✅ SHEETS WINS! ({sheets_timestamp} > {firebase_timestamp})")
                                print(f"   📊 Points: {firebase_points} → {sheets_points}")
                            else:
                                # Firebase is newer or equal - keep Firebase points
                                print(f"   ✅ FIREBASE WINS! ({firebase_timestamp} >= {sheets_timestamp})")
                                print(f"   📊 Points: {sheets_points} → {firebase_points} (no change)")
                        elif sheets_timestamp:
                            # Only Sheets has timestamp - use Sheets points
                            update_data['points'] = sheets_points
                            print(f"   ⚠️ Only Sheets has timestamp - using Sheets points: {sheets_points}")
                        else:
                            # No reliable timestamp - use Sheets points as default
                            update_data['points'] = sheets_points
                            print(f"   ⚠️ No reliable timestamps - defaulting to Sheets points: {sheets_points}")
                        
                        db.update_user(user_id, update_data)
                        stats['updated'] += 1
                    else:
                        # Add new user from Sheets
                        db.create_user(user_id, {
                            'full_name': row['full_name'],
                            'phone': row.get('phone', ''),
                            'username': row.get('username', ''),
                            'points': row['points'],
                            'status': 'active',
                            'role': 'student'
                        })
                        stats['added'] += 1
                
                print(f"✅ Hybrid sync: {stats['updated']} updated, {stats['added']} added")
                return stats
            
            except Exception as e:
                print(f"❌ Sheets → Firebase error: {e}")
                stats['errors'] += 1
                return stats
    
    async def sync_names_only(self) -> Dict[str, int]:
        """
        Sync ONLY names/phones from Sheets to Firebase
        Points are not touched
        """
        async with self.sync_lock:
            stats = {'updated': 0, 'errors': 0}
            
            try:
                sheets_data = self.fetch_all_data()
                
                for row in sheets_data:
                    user_id = row['user_id']
                    user = db.get_user(user_id)
                    
                    if user:
                        # Update ONLY names/phones, NOT points
                        db.update_user(user_id, {
                            'full_name': row['full_name'],
                            'phone': row.get('phone', ''),
                            'username': row.get('username', '')
                        })
                        stats['updated'] += 1
                        print(f"👤 Updated name: {row['full_name']}")
                
                print(f"✅ Names sync: {stats['updated']} updated")
                return stats
            
            except Exception as e:
                print(f"❌ Names sync error: {e}")
                stats['errors'] += 1
                return stats
    
    async def sync_points_only(self) -> Dict[str, int]:
        """
        Sync ONLY points based on timestamp (latest wins)
        Names are not touched
        """
        async with self.sync_lock:
            stats = {'updated': 0, 'skipped': 0, 'errors': 0}
            
            try:
                sheets_data = self.fetch_all_data()
                
                for row in sheets_data:
                    user_id = row['user_id']
                    user = db.get_user(user_id)
                    
                    if not user:
                        continue
                    
                    sheets_points = row['points']
                    firebase_points = user.get('points', 0)
                    
                    # Check timestamps
                    sheets_timestamp = self._parse_timestamp(row.get('last_updated', ''))
                    firebase_timestamp = self._parse_firebase_timestamp(user.get('last_updated'))
                    
                    if sheets_points == firebase_points:
                        stats['skipped'] += 1
                        continue
                    
                    # Compare timestamps
                    if sheets_timestamp and firebase_timestamp:
                        if sheets_timestamp > firebase_timestamp:
                            # Sheets newer - update Firebase
                            db.update_user(user_id, {'points': sheets_points})
                            stats['updated'] += 1
                            print(f"💰 Sheets → Firebase: {user['full_name']} ({firebase_points} → {sheets_points})")
                        elif firebase_timestamp > sheets_timestamp:
                            # Firebase newer - update Sheets
                            self.update_row(user_id, firebase_points)
                            stats['updated'] += 1
                            print(f"💰 Firebase → Sheets: {user['full_name']} ({sheets_points} → {firebase_points})")
                    elif sheets_timestamp:
                        db.update_user(user_id, {'points': sheets_points})
                        stats['updated'] += 1
                    elif firebase_timestamp:
                        self.update_row(user_id, firebase_points)
                        stats['updated'] += 1
                    else:
                        # No timestamp - use Firebase
                        self.update_row(user_id, firebase_points)
                        stats['updated'] += 1
                
                print(f"✅ Points sync: {stats['updated']} updated, {stats['skipped']} skipped")
                return stats
            
            except Exception as e:
                print(f"❌ Points sync error: {e}")
                stats['errors'] += 1
                return stats
    
    async def get_all_users_from_sheets(self) -> List[Dict[str, Any]]:
        """Get all users from Sheets (async wrapper)"""
        return self.fetch_all_data()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # BACKGROUND SYNC TASK
    # ═══════════════════════════════════════════════════════════════════════════
    
    async def background_sync_loop(self):
        """Background task that runs periodic sync"""
        print("🔄 Background sync task started")
        
        while True:
            try:
                # Get sync interval from settings (check every iteration for dynamic updates)
                settings = db.get_settings()
                interval = settings.get('sync_interval', config.DEFAULT_SYNC_INTERVAL)
                
                # Wait for the interval
                await asyncio.sleep(interval)
                
                # Perform sync (sync_enabled check already done in start/stop methods)
                await self.smart_delta_sync()
            
            except asyncio.CancelledError:
                print("🛑 Background sync task cancelled")
                break
            except Exception as e:
                print(f"⚠️ Background sync error: {e}")
                await asyncio.sleep(5)  # Wait before retry
    
    def start_background_sync(self):
        """Start the background sync task"""
        if self.background_task is None or self.background_task.done():
            self.background_task = asyncio.create_task(self.background_sync_loop())
            print("✅ Background sync task started")
            return True
        else:
            print("⚠️ Background sync task already running")
            return False
    
    def stop_background_sync(self):
        """Stop the background sync task"""
        if self.background_task and not self.background_task.done():
            self.background_task.cancel()
            print("🛑 Background sync task stopped")
            return True
        else:
            print("⚠️ No background sync task to stop")
            return False
    
    def is_sync_running(self):
        """Check if background sync task is running"""
        return self.background_task is not None and not self.background_task.done()


# Global sheets manager instance
sheets_manager = GoogleSheetsManager()
