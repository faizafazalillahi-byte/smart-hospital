# AI-Based Smart Hospital Queue & Resource Management System

## Stage 1 setup (Windows)
1. pgAdmin me database banayein: smart_hospital
2. backend/.env kholein, YOUR_PASSWORD ki jagah apna PostgreSQL password likhein
3. Terminal (backend folder me):
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python create_tables.py
4. pgAdmin me tables refresh karke check karein (8 tables)
