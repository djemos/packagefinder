#!/usr/bin/env python3
import sqlite3
import os
from datetime import datetime

# Υπολογισμός του μονοπατιού της βάσης
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'data', 'stats.db'))

def delete_future_data():
    if not os.path.exists(DB_FILE):
        print(f"Σφάλμα: Η βάση δεδομένων δεν βρέθηκε στο {DB_FILE}")
        return

    # Παίρνουμε τη σημερινή ημερομηνία σε μορφή YYYY-MM-DD (π.χ. '2026-07-15')
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print(f"Σύνδεση στη βάση: {DB_FILE}")
    print(f"Σημερινή ημερομηνία ελέγχου: {today_str}")
    print("-" * 50)

    # 1. Καθαρισμός μελλοντικών εγγραφών στον πίνακα searches
    # Χρησιμοποιούμε τη date() επειδή το timestamp περιέχει και ώρα
    cursor.execute("SELECT COUNT(*) FROM searches WHERE date(timestamp) > ?", (today_str,))
    future_searches = cursor.fetchone()[0]
    
    if future_searches > 0:
        cursor.execute("DELETE FROM searches WHERE date(timestamp) > ?", (today_str,))
        print(f"Διαγράφηκαν {future_searches} μελλοντικές εγγραφές αναζητήσεων.")
    else:
        print("Δεν βρέθηκαν μελλοντικές αναζητήσεις.")

    # 2. Καθαρισμός μελλοντικών εγγραφών στον πίνακα visits
    cursor.execute("SELECT COUNT(*) FROM visits WHERE date > ?", (today_str,))
    future_visits = cursor.fetchone()[0]
    
    if future_visits > 0:
        cursor.execute("DELETE FROM visits WHERE date > ?", (today_str,))
        print(f"Διαγράφηκαν {future_visits} μελλοντικές εγγραφές επισκέψεων.")
    else:
        print("Δεν βρέθηκαν μελλοντικές επισκέψεις.")

    conn.commit()
    conn.close()
    
    print("-" * 50)
    print("Ο καθαρισμός ολοκληρώθηκε με ασφάλεια!")

if __name__ == "__main__":
    delete_future_data()
