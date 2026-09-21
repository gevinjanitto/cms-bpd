"""Portable entry point. PORT is supplied by the hosting environment."""
import os
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

if __name__ == '__main__':
    load_dotenv(Path(__file__).parent / '.env')
    uvicorn.run('server:app', host='0.0.0.0', port=int(os.environ['PORT']), proxy_headers=True)