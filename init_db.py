from models import init_db, add_sample_data

print("=" * 50)
print("Creating ARENA Database...")
print("=" * 50)

init_db()
add_sample_data()

print("=" * 50)
print("✓ Database created successfully!")
print("✓ Sample data added")
print("=" * 50)
print("Now run: python app.py")
print("Test login: admin / admin123")
print("=" * 50)