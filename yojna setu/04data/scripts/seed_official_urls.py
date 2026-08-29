import sqlite3
import os

db_path = r"c:\Users\jaiku\OneDrive\Desktop\yojnasetu\yojna setu\02backend\yojnasetu.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

OFFICIAL_URL_MAPPING = {
    "SIH26092-001": "https://www.kviconline.gov.in/pmegpeportal/pmegpfilters/jsp/pmegponline.jsp", # PMEGP
    "SIH26092-002": "https://www.mudra.org.in/", # MUDRA
    "SIH26092-003": "https://www.standupmitra.in/", # Stand-Up India
    "SIH26092-004": "https://pmsvanidhi.mohua.gov.in/", # PM SVANidhi
    "SIH26092-005": "https://pmvishwakarma.gov.in/", # PM Vishwakarma
    "SIH26092-006": "https://pmfme.mofpi.gov.in/", # PMFME
    "SIH26092-008": "https://pmdaksh.dosje.gov.in/", # PM-DAKSH
    "SIH26092-018": "https://nrlm.gov.in/", # DAY-NRLM
    "SIH26092-019": "https://www.startupindia.gov.in/", # Startup India
    "SIH26092-020": "https://www.startupindia.gov.in/", # CGSS
    "SIH26092-025": "https://pmmsy.dof.gov.in/", # PMMSY
    "SIH26092-037": "https://agriinfra.dac.gov.in/", # AIF
    "SIH26092-049": "https://zed.msme.gov.in/", # ZED MSME
    "SIH26092-051": "https://www.cgtmse.in/", # CGTMSE
    "SIH26092-052": "https://pmsuraj.dosje.gov.in/", # NSFDC MFS
    "SIH26092-053": "https://pmsuraj.dosje.gov.in/", # NSFDC Term Loan
    "SIH26092-054": "https://pmsuraj.dosje.gov.in/", # NSFDC Aajeevika
    "SIH26092-055": "https://pmsuraj.dosje.gov.in/", # NSFDC UNY
    "SIH26092-056": "https://pmsuraj.dosje.gov.in/", # NSFDC ELS
}

updated_count = 0
for sid, url in OFFICIAL_URL_MAPPING.items():
    cursor.execute("""
        UPDATE schemes
        SET application_url = ?, official_portal = ?
        WHERE scheme_id = ?
    """, (url, url, sid))
    updated_count += cursor.rowcount

conn.commit()
print(f"Successfully updated official application URLs for {updated_count} schemes in database.")
conn.close()
