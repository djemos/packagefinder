#!/usr/bin/env python3
import sqlite3
import os
from pathlib import Path
from datetime import date

# ΔΙΑΔΡΟΜΗ ΓΙΑ ΤΗ ΒΑΣΗ SQLITE (SLACKWARE)
# Προσαρμόστε τη διαδρομή ανάλογα με το project σας
BASE = Path("/srv/httpd/htdocs/packagefinder")
DB_FILE = BASE / "data/stats.db"

def get_valid_date(prompt_message):
    print(prompt_message)
    while True:
        try:
            year = int(input("  Έτος (YYYY): "))
            month = int(input("  Μήνας (1-12): "))
            day = int(input("  Ημέρα (1-31): "))
            
            chosen_date = date(year, month, day)
            return chosen_date.strftime('%Y-%m-%d')
        except ValueError:
            print("❌ Σφάλμα: Μη έγκυρη ημερομηνία ή λανθασμένοι αριθμοί. Προσπαθήστε ξανά.")
def delete_date_range():
    print("=" * 60)
    print(" ΔΙΑΔΡΑΣΤΙΚΗ ΔΙΑΓΡΑΦΗ ΕΓΓΡΑΦΩΝ ΑΠΟ ΗΜΕΡΟΜΗΝΙΑ ΣΕ ΗΜΕΡΟΜΗΝΙΑ (SQLITE)")
    print("=" * 60)

    # 1. Εισαγωγή Ημερομηνίας Έναρξης (Από)
    start_date = get_valid_date("📅 Εισάγετε Ημερομηνία Έναρξης (ΑΠΟ):")
    print("-" * 40)
    
    # 2. Εισαγωγή Ημερομηνίας Λήξης (Έως)
    while True:
        end_date = get_valid_date("📅 Εισάγετε Ημερομηνία Λήξης (ΕΩΣ):")
        if end_date >= start_date:
            break
        print("❌ Σφάλμα: Η ημερομηνία λήξης πρέπει να είναι ίδια ή μεταγενέστερη από την έναρξη!")
        print("-" * 40)

    print("=" * 60)
    print(f"⚠️ Πρόκειται να διαγραφούν ΟΛΑ τα δεδομένα από {start_date} έως {end_date}!")
    confirm = input("Είστε σίγουροι; Πληκτρολογήστε 'yes' για επιβεβαίωση: ")
    
    if confirm.lower() != 'yes':
        print("❌ Η διαγραφή ακυρώθηκε.")
        return

    # 3. Σύνδεση στη βάση δεδομένων SQLite
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Αποτυχία σύνδεσης στη SQLite βάση ({DB_FILE}): {str(e)}")
        return

    # 4. Υπολογισμός εγγραφών που θα διαγραφούν (χρήση ? αντί για %s)
    cursor.execute("SELECT COUNT(*) FROM searches WHERE DATE(timestamp) BETWEEN ? AND ?", (start_date, end_date))
    searches_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM visits WHERE date BETWEEN ? AND ?", (start_date, end_date))
    visits_count = cursor.fetchone()[0]
    
    # 5. Εκτέλεση της διαγραφής με BETWEEN (χρήση ? αντί για %s)
    cursor.execute("DELETE FROM searches WHERE DATE(timestamp) BETWEEN ? AND ?", (start_date, end_date))
    cursor.execute("DELETE FROM visits WHERE date BETWEEN ? AND ?", (start_date, end_date))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("=" * 60)
    print("🎉 Η διαγραφή ολοκληρώθηκε με επιτυχία από τη SQLite βάση!")
    print(f"   • Διαγράφηκαν {searches_count} αναζητήσεις (searches).")
    print(f"   • Διαγράφηκαν {visits_count} επισκέψεις (visits).")
    print("=" * 60)
    print("Ανανεώστε τη σελίδα stats.html με Ctrl+F5 για να δείτε το ενημερωμένο γράφημα.")

if __name__ == "__main__":
    delete_date_range()
