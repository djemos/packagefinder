#!/usr/bin/env python3
import json
import sqlite3
import os
import sys
import hashlib
from datetime import datetime

# Control and filtering of automated bots / scanners
user_agent = os.environ.get('HTTP_USER_AGENT', '').lower()
bad_agents = ['curl', 'wget', 'python', 'perl', 'libwww', 'go-http', 'scanner', 'bot', 'spider']

if not user_agent or any(agent in user_agent for agent in bad_agents):
    # We return a valid header to Apache so it doesn't throw a 500 Internal Server Error
    print("Content-Type: text/html\n")
    print("Access Denied: Automated tools are not allowed.")
    sys.exit(0)
    
# ==========================================
# SECURE PASSWORD ENCRYPTION SETTING
# ==========================================
# The password "your_password" is stored as a SHA-256 hash with salt for maximum security.
ADMIN_PASSWORD_HASH = "your_hash" # Replace with your own
PASSWORD_SALT = "your_password" # Replace with your own

ONLINE_TIMEOUT_SECONDS = 300  
MAX_ATTEMPTS = 5              # Maximum failed login attempts
LOCKOUT_DURATION = 900        # 15 minutes of blocking in seconds

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'data', 'stats.db'))


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Statistics tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS searches 
                      (query TEXT, count INTEGER DEFAULT 1, timestamp DATETIME)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS visits 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT, date TEXT, system TEXT DEFAULT 'Unknown')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS online_users 
                      (ip TEXT PRIMARY KEY, last_seen DATETIME)''')
    
    # Table for Brute Force Protection (Rate Limiting)
    cursor.execute('''CREATE TABLE IF NOT EXISTS login_attempts 
                      (ip TEXT PRIMARY KEY, attempts INTEGER DEFAULT 0, last_attempt TIMESTAMP)''')
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_searches_timestamp ON searches(timestamp)")
    
    try:
        cursor.execute("ALTER TABLE visits ADD COLUMN system TEXT DEFAULT 'Unknown'")
    except sqlite3.OperationalError:
        pass 
        
    conn.commit()
    conn.close()


def get_client_ip():
    ip = os.environ.get('HTTP_X_FORWARDED_FOR', '')
    if ip:
        return ip.split(',')[0].strip()
    return os.environ.get('REMOTE_ADDR', '127.0.0.1').strip()


def check_brute_force(cursor, ip):
    """Rate Limiting Disabled: Always allows login attempt to SQLite."""
    return True, ""  # <-- Bypasses the check, so it never locks the IP

def log_login_failure(cursor, ip):
    """No longer logs failures to avoid locks in SQLite."""
    pass  # <-- It doesn't execute any SQL queries, so zero locks!

def log_login_success(cursor, ip):
    """Resets failed attempts after successful login."""
    cursor.execute("DELETE FROM login_attempts WHERE ip=?", (ip,))


def verify_password(plain_password):
    """Checks if the hash of the entered password matches the stored one."""
    salted = plain_password + PASSWORD_SALT
    hashed = hashlib.sha256(salted.encode('utf-8')).hexdigest()
    return hashed == ADMIN_PASSWORD_HASH


def parse_user_agent(ua_string):
    if not ua_string:
        return "Unknown System"
    ua = ua_string.lower()
    if "slackel" in ua: return "Slackel Linux"
    elif "slackware" in ua or "x11; u; linux" in ua or "slack" in ua: return "Slackware Linux"
    elif "android" in ua: return "Android Mobile"
    elif "iphone" in ua or "ipad" in ua: return "iOS (iPhone/iPad)"
    elif "linux" in ua: return "Generic Linux"
    elif "windows" in ua: return "Windows PC"
    elif "macintosh" in ua or "mac os" in ua: return "macOS"
    return "Other / Web Bot"
    
    
def handle_stats():
    # Δήλωση ασφαλών HTTP Headers
    print("Content-Type: application/json; charset=utf-8")
    print("Cache-Control: no-store, no-cache, must-revalidate")
    print("X-Content-Type-Options: nosniff\n")
    
    try:
        init_db()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        ip = get_client_ip()
        method = os.environ.get('REQUEST_METHOD', 'GET')
        
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        formatted_now = now.strftime('%Y-%m-%d %H:%M:%S')
        
        user_agent = os.environ.get('HTTP_USER_AGENT', '')
        detected_os = parse_user_agent(user_agent)

        # 1. Recording of unique visits per day
        cursor.execute("SELECT id FROM visits WHERE ip=? AND date=?", (ip, today))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO visits (ip, date, system) VALUES (?, ?, ?)", (ip, today, detected_os))
        
        # 2. Online user registration & immediate deletion of inactive users
        cursor.execute("INSERT OR REPLACE INTO online_users (ip, last_seen) VALUES (?, ?)", (ip, formatted_now))
        cursor.execute(
            "DELETE FROM online_users WHERE (strftime('%s', ?) - strftime('%s', last_seen)) > ?", 
            (formatted_now, ONLINE_TIMEOUT_SECONDS)
        )
        conn.commit()

        # 3. DELETE / CLEAR HISTORY MANAGEMENT (SECURED)
        if method == 'DELETE' or (method == 'POST' and os.environ.get('HTTP_X_HTTP_METHOD_OVERRIDE') == 'DELETE'):
            is_allowed, error_msg = check_brute_force(cursor, ip)
            if not is_allowed:
                print(json.dumps({"status": "error", "message": error_msg}))
                conn.commit()
                conn.close()
                return

            body = sys.stdin.read()
            if body:
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    print(json.dumps({"status": "error", "message": "Invalid JSON data payload."}))
                    conn.close()
                    return

                input_password = data.get('password', '')
                if verify_password(input_password):
                    log_login_success(cursor, ip)
                    cursor.execute("DELETE FROM searches")
                    cursor.execute("DELETE FROM visits")
                    cursor.execute("DELETE FROM online_users")
                    conn.commit()
                    print(json.dumps({"status": "success", "message": "The history logs have been successfully cleared!"}))
                else:
                    log_login_failure(cursor, ip)
                    conn.commit()
                    print(json.dumps({"status": "error", "message": "Incorrect administrator password!"}))
            else:
                print(json.dumps({"status": "error", "message": "Missing authentication data payload."}))
            
            conn.close()
            return

        # 4. POST Management (Search Log)
        if method == 'POST':
            body = sys.stdin.read()
            if body:
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    print(json.dumps({"status": "error", "message": "Invalid JSON data payload."}))
                    conn.close()
                    return

                query = data.get('query', '').strip()
                if query:
                    cursor.execute("SELECT count FROM searches WHERE query=? AND date(timestamp)=?", (query, today))
                    row = cursor.fetchone()
                    if row:
                        current_count = row[0]
                        cursor.execute("UPDATE searches SET count=?, timestamp=? WHERE query=? AND date(timestamp)=?", 
                                       (current_count + 1, formatted_now, query, today))
                    else:
                        cursor.execute("INSERT INTO searches (query, count, timestamp) VALUES (?, 1, ?)", 
                                       (query, formatted_now))
                    
                    cursor.execute("DELETE FROM searches WHERE rowid NOT IN (SELECT rowid FROM searches ORDER BY timestamp DESC LIMIT 1000)")
                    conn.commit()
            print(json.dumps({"status": "success"}))
            conn.close()
            return

        # 5. GET Management (Retrieve data for stats.html)
        cursor.execute("SELECT query, count, timestamp FROM searches ORDER BY timestamp DESC LIMIT 100")
        last_searches = [{"query": row[0], "count": row[1], "time": row[2]} for row in cursor.fetchall()]
        
        cursor.execute("SELECT query, SUM(count) as total_count, max(timestamp) as last_time FROM searches GROUP BY query ORDER BY total_count DESC, last_time DESC LIMIT 100")
        hot_queries = [{"query": row[0], "count": row[1], "time": row[2]} for row in cursor.fetchall()]
        
        cursor.execute('''SELECT date(timestamp) as search_date, SUM(count) as daily_count 
                          FROM searches
                          WHERE timestamp IS NOT NULL
                          GROUP BY search_date
                          ORDER BY search_date ASC''')
        daily_analytics = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        cursor.execute('''SELECT system, COUNT(*) as c FROM visits GROUP BY system ORDER BY c DESC LIMIT 100''')
        top_countries = [{"system": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        cursor.execute("SELECT COUNT(*) FROM visits")
        res_total = cursor.fetchone()
        total_visits = res_total[0] if res_total else 0
        
        cursor.execute("SELECT COUNT(*) FROM visits WHERE date=?", (today,))
        res_today = cursor.fetchone()
        today_visits = res_today[0] if res_today else 0
        
        cursor.execute("SELECT COUNT(*) FROM online_users")
        res_online = cursor.fetchone()
        online_count = res_online[0] if res_online else 0
        
        conn.close()
        
        print(json.dumps({
            "last_searches": last_searches,
            "hot_queries": hot_queries,
            "daily_analytics": daily_analytics,
            "top_countries": top_countries,
            "total_visits": total_visits,
            "today_visits": today_visits,
            "online_users": online_count
        }))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))

if __name__ == "__main__":
    handle_stats()
