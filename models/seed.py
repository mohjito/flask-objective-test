from app import app
from models.user import db, User

def seed_database():
    """
    Function to seed the database with initial data.
    """
    with app.app_context():
        # Clear the database (optional, useful during testing)
        db.drop_all()
        db.create_all()

        # Add test users
        user1 = User(username='testuser1', email='test1@example.com')
        user1.set_password('password123')  # Set the password for user1

        user2 = User(username='testuser2', email='test2@example.com')
        user2.set_password('password456')  # Set the password for user2

        user3 = User(username='admin', email='admin@example.com')
        user3.set_password('adminpassword')  # Set the password for admin

        # Add users to the session
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)

        # Commit changes to the database
        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
