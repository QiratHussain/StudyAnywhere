import os
from dotenv import load_dotenv
from urllib.parse import urlsplit

load_dotenv()

url = os.getenv("DB_LINK")

print("URL exists:", bool(url))
print("PostgreSQL prefix count:", url.count("postgresql://") if url else 0)
print("Question mark count:", url.count("?") if url else 0)

if url:
    parsed = urlsplit(url)
    print("Scheme:", parsed.scheme)
    print("Database:", parsed.path)
    print("Parameters:", parsed.query)