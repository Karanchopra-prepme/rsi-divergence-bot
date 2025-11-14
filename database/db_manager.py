"""
Database manager for storing divergences and preventing duplicate alerts
UPDATED: Added hours parameter support
"""

import sqlite3
from datetime import datetime, timedelta
from config.settings import DATABASE_PATH
import os

class DatabaseManager:
    """Manage database operations for divergence tracking"""
    
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self._ensure_directory_exists()
        self._initialize_database()
    
    def _ensure_directory_exists(self):
        """Create database directory if it doesn't exist"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def _initialize_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Divergences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS divergences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                type TEXT NOT NULL,
                price REAL NOT NULL,
                rsi REAL NOT NULL,
                strength REAL NOT NULL,
                volume_confirmed BOOLEAN,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                alerted BOOLEAN DEFAULT FALSE,
                alerted_at TIMESTAMP
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_symbol_time 
            ON divergences(symbol, timeframe, detected_at)
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Database initialized")
    
    def save_divergence(self, divergence):
        """
        Save a divergence or reversal signal to database
        
        Args:
            divergence: Dictionary with signal info (divergence or RSI S/R)
        
        Returns:
            Integer: ID of saved record
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get signal type - handle both divergences and RSI S/R signals
        signal_type = divergence.get('type') or divergence.get('direction') or 'UNKNOWN'
        
        # Volume confirmed - default to False for RSI S/R signals
        volume_confirmed = divergence.get('volume_confirmed', False)
        
        cursor.execute('''
            INSERT INTO divergences 
            (symbol, timeframe, type, price, rsi, strength, volume_confirmed, alerted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            divergence['symbol'],
            divergence['timeframe'],
            signal_type,
            divergence['current_price'],
            divergence['current_rsi'],
            divergence['strength'],
            volume_confirmed,
            False
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def mark_as_alerted(self, record_id):
        """Mark a divergence as alerted"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE divergences 
            SET alerted = TRUE, alerted_at = ? 
            WHERE id = ?
        ''', (datetime.now(), record_id))
        
        conn.commit()
        conn.close()
    
    def is_duplicate_alert(self, symbol, timeframe, divergence_type, hours=2):
        """
        Check if similar alert was sent recently (cooldown period)
        
        Args:
            symbol: Trading pair
            timeframe: Timeframe
            divergence_type: 'BULLISH' or 'BEARISH'
            hours: Cooldown period in hours (default 2)
        
        Returns:
            Boolean: True if duplicate, False if new
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate cooldown time using hours parameter
        cooldown_time = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT COUNT(*) FROM divergences
            WHERE symbol = ?
            AND timeframe = ?
            AND type = ?
            AND alerted = TRUE
            AND alerted_at > ?
        ''', (symbol, timeframe, divergence_type, cooldown_time))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def get_recent_divergences(self, hours=24):
        """
        Get divergences from recent hours
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            List of divergence records
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT * FROM divergences
            WHERE detected_at > ?
            ORDER BY detected_at DESC
        ''', (cutoff_time,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return rows
    
    def get_statistics(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total divergences
        cursor.execute('SELECT COUNT(*) FROM divergences')
        total = cursor.fetchone()[0]
        
        # Bullish count
        cursor.execute("SELECT COUNT(*) FROM divergences WHERE type = 'BULLISH'")
        bullish = cursor.fetchone()[0]
        
        # Bearish count
        cursor.execute("SELECT COUNT(*) FROM divergences WHERE type = 'BEARISH'")
        bearish = cursor.fetchone()[0]
        
        # Alerted count
        cursor.execute('SELECT COUNT(*) FROM divergences WHERE alerted = TRUE')
        alerted = cursor.fetchone()[0]
        
        # Last 24 hours
        cutoff = datetime.now() - timedelta(hours=24)
        cursor.execute('SELECT COUNT(*) FROM divergences WHERE detected_at > ?', (cutoff,))
        last_24h = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total': total,
            'bullish': bullish,
            'bearish': bearish,
            'alerted': alerted,
            'last_24h': last_24h
        }
    
    def cleanup_old_records(self, days=30):
        """
        Delete records older than specified days
        
        Args:
            days: Number of days to keep
        
        Returns:
            Number of deleted records
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            DELETE FROM divergences
            WHERE detected_at < ?
        ''', (cutoff_time,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted

# Test the database manager
if __name__ == "__main__":
    print("=" * 60)
    print("Testing Database Manager")
    print("=" * 60)
    
    db = DatabaseManager()
    
    # Test saving divergence
    print("\n1. Testing save divergence...")
    test_div = {
        'symbol': 'BTC/USDT',
        'timeframe': '15m',
        'type': 'BULLISH',
        'current_price': 42000,
        'current_rsi': 35.5,
        'strength': 75.0,
        'volume_confirmed': True
    }
    
    record_id = db.save_divergence(test_div)
    print(f"✓ Saved with ID: {record_id}")
    
    # Test duplicate check with hours parameter
    print("\n2. Testing duplicate check with hours parameter...")
    is_dup = db.is_duplicate_alert('BTC/USDT', '15m', 'BULLISH', hours=2)
    print(f"Is duplicate (before alert): {is_dup}")
    
    # Mark as alerted
    db.mark_as_alerted(record_id)
    print("✓ Marked as alerted")
    
    is_dup = db.is_duplicate_alert('BTC/USDT', '15m', 'BULLISH', hours=2)
    print(f"Is duplicate (after alert, 2 hours): {is_dup}")
    
    # Test with different hours
    is_dup = db.is_duplicate_alert('BTC/USDT', '15m', 'BULLISH', hours=0.01)
    print(f"Is duplicate (after alert, 0.01 hours): {is_dup}")
    
    # Get statistics
    print("\n3. Database statistics:")
    stats = db.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✓ Database manager test complete!")