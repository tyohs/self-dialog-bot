from dotenv import load_dotenv
import os, pathlib

dotenv_path = pathlib.Path(__file__).parent / ".env"
load_dotenv(dotenv_path)

print("ENV TEST:", os.getenv("OPENAI_API_KEY"))
