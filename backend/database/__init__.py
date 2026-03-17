python -c 'import sqlite3, json; 
conn = sqlite3.connect("backend/storage/database/crm.db"); 
conn.row_factory = sqlite3.Row; 
row = conn.execute("SELECT * FROM crm_contacts WHERE email = ?", ("christopher.poznanski@csd15.net",)).fetchone(); 
print(json.dumps(dict(row)) if row else "{}")'

python -m ai.agents.NaturalLanguageDatabase "return contact with email kyle.weir@stonehill.in that is not valid"
