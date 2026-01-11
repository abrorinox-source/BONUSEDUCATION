"""
Google Sheets Manager
Handles all Google Sheets operations and synchronization
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
import config
from database import db


class GoogleSheetsManager:
    """Manages Google Sheets operations"""
    
    def __init__(self):
        """Initialize Google Sheets API"""
        self.credentials = service_account.Credentials.from_service_account_file(
            config.FIREBASE_KEY_PATH,
            scopes=config.GOOGLE_SCOPES
        )
        self.service = build('sheets', 'v4', credentials=self.credentials)
        self.sheet_id = config.SHEET_ID
        self.sync_lock = asyncio.Lock()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # READ OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def fetch_all_data(self) -> List[Dict[str, Any]]:
        """Fetch all data from Google Sheets"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range='Sheet1!A2:F'  # Skip header row
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
    
    def update_row(self, user_id: str, points: int) -> bool:
        """Update specific user's points in Sheets"""
        try:
            # Find the row for this user
            all_data = self.fetch_all_data()
            row_index = None
            
            for idx, user in enumerate(all_data):
                if user['user_id'] == user_id:
                    row_index = idx + 2  # +2 because of header and 0-index
                    break
            
            if row_index is None:
                print(f"User {user_id} not found in Sheets")
                return False
            
            # Update the points column (E) and last_updated (F)
            range_name = f'Sheet1!E{row_index}:F{row_index}'
            values = [[points, datetime.now().strftime('%Y-%m-%d %H:%M:%S')]]
            
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
    
    def add_user(self, user_data: Dict[str, Any]) -> bool:
        """Add new user to Google Sheets"""
        try:
            values = [[
                user_data.get('user_id', ''),
                user_data.get('full_name', ''),
                user_data.get('phone', ''),
                user_data.get('username', ''),
                user_data.get('points', 0),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]]
            
            body = {'values': values}
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range='Sheet1!A:F',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
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
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
    # SMART DELTA SYNC
    # ═══════════════════════════════════════════════════════════════════════════
    
    async def smart_delta_sync(self) -> Dict[str, int]:
        """
        Timestamp-Based Bidirectional Sync
        Latest modification wins based on last_updated timestamp
        """
        async with self.sync_lock:
            stats = {'updated': 0, 'added': 0, 'deleted': 0, 'errors': 0, 'skipped': 0}
            
            try:
                # Get all active Firebase users
                firebase_active_users = db.get_all_users(role='student', status='active')
                firebase_active_ids = {u['user_id'] for u in firebase_active_users}
                
                # Fetch from Sheets
                sheets_data = self.fetch_all_data()
                sheets_user_ids = {row['user_id'] for row in sheets_data}
                
                # Remove deleted/banned users from Sheets
                users_to_delete = sheets_user_ids - firebase_active_ids
                for user_id in users_to_delete:
                    # Check if user exists in Firebase but not active
                    user = db.get_user(user_id)
                    if user and user.get('status') in ['deleted', 'banned']:
                        self.delete_user(user_id)
                        stats['deleted'] += 1
                        print(f"🗑️ Removed {user.get('status')} user from Sheets: {user.get('full_name', user_id)}")
                
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
                        })
                        stats['added'] += 1
                        print(f"✅ Added active Firebase user to Sheets: {user['full_name']}")
                
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
                    
                    # Check if points are different
                    if firebase_points == sheets_points:
                        # No difference, skip
                        stats['skipped'] += 1
                        continue
                    
                    # Points are different - check which is newer
                    if sheets_timestamp and firebase_timestamp:
                        if sheets_timestamp > firebase_timestamp:
                            # Sheets is newer - update Firebase
                            db.update_user(user_id, {'points': sheets_points})
                            db.log_manual_edit(user_id, user_name, firebase_points, sheets_points)
                            stats['updated'] += 1
                            print(f"✅ Sheets → Firebase: {user_name} ({firebase_points} → {sheets_points})")
                        
                        elif firebase_timestamp > sheets_timestamp:
                            # Firebase is newer - update Sheets
                            self.update_row(user_id, firebase_points)
                            stats['updated'] += 1
                            print(f"✅ Firebase → Sheets: {user_name} ({sheets_points} → {firebase_points})")
                        
                        else:
                            # Same timestamp but different points (conflict)
                            # Use Firebase as source of truth
                            self.update_row(user_id, firebase_points)
                            stats['updated'] += 1
                            print(f"⚠️ Conflict resolved (Firebase wins): {user_name} → {firebase_points}")
                    
                    elif sheets_timestamp:
                        # Only Sheets has timestamp - use Sheets
                        db.update_user(user_id, {'points': sheets_points})
                        db.log_manual_edit(user_id, user_name, firebase_points, sheets_points)
                        stats['updated'] += 1
                        print(f"✅ Sheets → Firebase: {user_name} ({firebase_points} → {sheets_points})")
                    
                    elif firebase_timestamp:
                        # Only Firebase has timestamp - use Firebase
                        self.update_row(user_id, firebase_points)
                        stats['updated'] += 1
                        print(f"✅ Firebase → Sheets: {user_name} ({sheets_points} → {firebase_points})")
                    
                    else:
                        # No timestamps - use Firebase as source of truth
                        self.update_row(user_id, firebase_points)
                        stats['updated'] += 1
                        print(f"⚠️ No timestamps, using Firebase: {user_name} → {firebase_points}")
                
                # Update sync statistics
                settings = db.get_settings()
                db.update_settings({
                    'last_sync_time': datetime.now().isoformat(),
                    'sync_statistics.total_syncs': settings['sync_statistics']['total_syncs'] + 1,
                    'sync_statistics.successful_syncs': settings['sync_statistics']['successful_syncs'] + 1
                })
                
                print(f"🔄 Sync complete: {stats['updated']} updated, {stats['added']} added, {stats['skipped']} skipped")
                return stats
            
            except Exception as e:
                print(f"❌ Sync error: {e}")
                stats['errors'] += 1
                
                # Update failure statistics
                settings = db.get_settings()
                db.update_settings({
                    'sync_statistics.total_syncs': settings['sync_statistics']['total_syncs'] + 1,
                    'sync_statistics.failed_syncs': settings['sync_statistics']['failed_syncs'] + 1,
                    'sync_statistics.last_error': str(e)
                })
                
                return stats
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse Sheets timestamp string to datetime"""
        if not timestamp_str:
            return None
        
        try:
            # Try multiple formats (including European/Russian formats)
            formats = [
                '%Y-%m-%d %H:%M:%S',       # 2025-01-10 14:30:45 (Expected format)
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
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            print(f"⚠️ Could not parse timestamp '{timestamp_str}' with any known format")
            return None
        except Exception as e:
            print(f"Error parsing timestamp '{timestamp_str}': {e}")
            return None
    
    def _parse_firebase_timestamp(self, timestamp) -> Optional[datetime]:
        """Parse Firebase timestamp to datetime"""
        if not timestamp:
            return None
        
        try:
            # Firebase SERVER_TIMESTAMP returns DatetimeWithNanoseconds
            if hasattr(timestamp, 'timestamp'):
                return datetime.fromtimestamp(timestamp.timestamp())
            
            # If it's already a datetime
            if isinstance(timestamp, datetime):
                return timestamp
            
            # If it's a string
            if isinstance(timestamp, str):
                return self._parse_timestamp(timestamp)
            
            return None
        except Exception as e:
            print(f"Error parsing Firebase timestamp: {e}")
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
        One-way sync: Sheets → Firebase
        Force all Sheets data to Firebase
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
                        # Update existing
                        db.update_user(user_id, {'points': row['points']})
                        stats['updated'] += 1
                    else:
                        # Add new
                        db.create_user(user_id, {
                            'full_name': row['full_name'],
                            'phone': row.get('phone', ''),
                            'username': row.get('username', ''),
                            'points': row['points'],
                            'status': 'active',
                            'role': 'student'
                        })
                        stats['added'] += 1
                
                print(f"✅ Sheets → Firebase sync: {stats['updated']} updated, {stats['added']} added")
                return stats
            
            except Exception as e:
                print(f"❌ Sheets → Firebase error: {e}")
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
                # Check if sync is enabled
                if db.is_sync_enabled():
                    await self.smart_delta_sync()
                
                # Get sync interval from settings
                settings = db.get_settings()
                interval = settings.get('sync_interval', config.DEFAULT_SYNC_INTERVAL)
                
                await asyncio.sleep(interval)
            
            except asyncio.CancelledError:
                print("🛑 Background sync task cancelled")
                break
            except Exception as e:
                print(f"⚠️ Background sync error: {e}")
                await asyncio.sleep(5)  # Wait before retry


# Global sheets manager instance
sheets_manager = GoogleSheetsManager()
