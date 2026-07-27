#!/usr/bin/env python3
import sqlite3
import os
import calendar
from datetime import datetime, timedelta
import random

# Υπολογισμός του μονοπατιού της βάσης
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'data', 'stats.db'))

def insert_interactive_data():
    print("=" * 60)
    print(" ΔΥΝΑΜΙΚΗ ΕΙΣΑΓΩΓΗ ΔΟΚΙΜΑΣΤΙΚΩΝ ΔΕΔΟΜΕΝΩΝ ΣΤΟ STATS.DB")
    print("=" * 60)
    
    sample_queries = ["kernel", "firefox", "vlc", "slackel-live", "gimp", "python", "xfce", "mesa", "libreoffice", "smplayer", "thunderbird", "mixx"]
    sample_os = ["Generic Linux", "Android Mobile"]
    
    try:
        # 1. Ερωτήσεις για Ημερομηνία και Πλήθος
        year = int(input("Εισάγετε Έτος (π.χ. 2026): "))
        month = int(input("Εισάγετε Μήνα (1-12): "))
        if month < 1 or month > 12:
            print("Σφάλμα: Ο μήνας πρέπει να είναι από 1 έως 12!")
            return
            
        # ΝΕΟ: Ερώτηση για την ημέρα έναρξης
        day_input = input(f"Από ποια ημέρα του μήνα να ξεκινήσει; (1-{calendar.monthrange(year, month)[1]}) [Πατήστε Enter για τη σημερινή]: ")
        if day_input.strip() == "":
            # Αν είμαστε στον τρέχοντα μήνα/έτος, παίρνουμε το σήμερα, αλλιώς την τελευταία μέρα
            now = datetime.now()
            if now.year == year and now.month == month:
                start_day = now.day
            else:
                start_day = calendar.monthrange(year, month)[1]
        else:
            start_day = int(day_input)
            
        if start_day < 1 or start_day > calendar.monthrange(year, month)[1]:
            print("Σφάλμα: Μη έγκυρη ημέρα για τον συγκεκριμένο μήνα!")
            return

        M = int(input("Πόσες ημέρες θέλετε να εισαγάγετε συνολικά προς τα πίσω (M); "))
        K = int(input("Πόσες εγγραφές αναζητήσεων ανά ημέρα θέλετε (K); "))
        print("-" * 60)
        
        # 2. Επιλογή Συγκεκριμένου Query / Πακέτου
        print("Επιλέξτε το query που θέλετε να εισαχθεί:")
        print("0. Τυχαία επιλογή από τη λίστα")
        for idx, q in enumerate(sample_queries, 1):
            print(f"{idx}. {q}")
            
        choice = int(input(f"Εισάγετε τον αριθμό της επιλογής σας (0-{len(sample_queries)}): "))
        if choice < 0 or choice > len(sample_queries):
            print("Σφάλμα: Μη έγκυρη επιλογή!")
            return
            
        selected_query = None if choice == 0 else sample_queries[choice - 1]
        print("-" * 60)
        
    except ValueError:
        print("Σφάλμα: Παρακαλώ εισάγετε έγκυρους ακέραιους αριθμούς!")
        return

    # ΑΛΛΑΓΗ: Η base_date ορίζεται πλέον από την ημέρα start_day που επιλέχθηκε
    base_date = datetime(year, month, start_day)

    # Δημιουργία λίστας ημερομηνιών πηγαίνοντας προς τα πίσω
    target_dates = []
    for i in range(M):
        t_date = base_date - timedelta(days=i)
        # Διασφάλιση ότι δεν θα βγούμε έξω από τον επιλεγμένο μήνα (προαιρετικό αλλά ασφαλές)
        if t_date.month == month and t_date.year == year:
            target_dates.append(t_date.strftime('%Y-%m-%d'))

    if not target_dates:
        print("❌ Σφάλμα: Δεν δημιουργήθηκαν έγκυρες ημερομηνίες για αυτόν τον μήνα.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # --- ΚΑΘΑΡΙΣΜΟΣ ΜΟΝΟ ΤΩΝ ΗΜΕΡΩΝ ΠΟΥ ΘΑ ΞΑΝΑΓΡΑΦΟΥΝ ---
    print(f"Καθαρισμός παλιών δεδομένων για τις {len(target_dates)} συγκεκριμένες ημέρες...")
    for date_str in target_dates:
        cursor.execute("DELETE FROM searches WHERE date(timestamp) = ?", (date_str,))
        cursor.execute("DELETE FROM visits WHERE date = ?", (date_str,))
    conn.commit()
    
    print(f"Σύνδεση στη βάση: {DB_FILE}")
    print(f"Έναρξη εισαγωγής (πηγαίνοντας πίσω από {base_date.strftime('%Y-%m-%d')})...")
  
    # Loop για τις ημέρες
    for date_str in target_dates:
        # Εισαγωγή αναζητήσεων
        for _ in range(K):
            query = selected_query if selected_query else random.choice(sample_queries)
            count = random.randint(10, 40)
            
            random_hour = random.randint(0, 23)
            random_minute = random.randint(0, 59)
            random_second = random.randint(0, 59)
            timestamp_str = f"{date_str} {random_hour:02d}:{random_minute:02d}:{random_second:02d}"
            cursor.execute("INSERT INTO searches (query, count, timestamp) VALUES (?, ?, ?)", 
                           (query, count, timestamp_str))
        
        # Εισαγωγή visits
        num_visits_today = K * random.randint(3, 6)
        for _ in range(num_visits_today):
            mock_ip = f"192.168.1.{random.randint(1, 254)}"
            mock_os = random.choice(sample_os)
            cursor.execute("INSERT INTO visits (ip, date, system) VALUES (?, ?, ?)", 
                           (mock_ip, date_str, mock_os))

    conn.commit()
    conn.close()
    
    query_display = selected_query if selected_query else "τυχαίων πακέτων"
    print("=" * 60)
    print(f"Επιτυχία! Προστέθηκαν δεδομένα για {len(target_dates)} ημέρες του πακέτου '{query_display}' για τον {month:02d}/{year}.")
    print("Ανανεώστε τη σελίδα stats.html για να δείτε τα αποτελέσματα.")
    print("=" * 60)

if __name__ == "__main__":
    insert_interactive_data()
