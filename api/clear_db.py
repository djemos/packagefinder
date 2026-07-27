#!/usr/bin/env python3
import json
import sqlite3
import os
import sys
import hashlib
from datetime import datetime
# Σιγουρευτείτε ότι η μεταβλητή DB_FILE είναι ορισμένη (π.χ. DB_FILE = 'stats.db')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'data', 'stats.db'))

def clear_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Διαγραφή των δεδομένων
    cursor.execute("DELETE FROM searches")
    cursor.execute("DELETE FROM visits")
    cursor.execute("DELETE FROM online_users")
    cursor.execute("DELETE FROM login_attempts")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='visits'")
    
    # 2. Απαραίτητο Commit για να κλείσει η τρέχουσα συναλλαγή
    conn.commit()
    
    # 3. Απομόνωση (isolation_level = None) για να τρέξει το VACUUM εκτός transaction
    old_isolation = conn.isolation_level
    conn.isolation_level = None
    cursor.execute("VACUUM")
    conn.isolation_level = old_isolation # Επαναφορά στην αρχική κατάσταση
    
    conn.close()
    print("Η βάση δεδομένων καθαρίστηκε επιτυχώς!")
