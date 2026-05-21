import argparse
import getpass
import os
import pathlib

from app import app, db, User, Branch, validate_password
from sqlalchemy import text


def parse_args():
    parser = argparse.ArgumentParser(description='Initialize the inventory database and create the admin account.')
    parser.add_argument('--admin-username', help='Admin username to create or update.')
    parser.add_argument('--admin-password', help='Admin password to set.')
    parser.add_argument('--branch-name', default=os.environ.get('ADMIN_BRANCH_NAME', 'Main Branch'), help='Branch name for the admin account.')
    parser.add_argument('--branch-address', default=os.environ.get('ADMIN_BRANCH_ADDRESS', 'HQ'), help='Branch address for the admin account.')
    parser.add_argument('--force', action='store_true', help='Drop and recreate the database before initialization.')
    parser.add_argument('--skip-confirm', action='store_true', help='Skip confirmation prompts for destructive actions.')
    return parser.parse_args()


def prompt_password(prompt='Password'):  # pragma: no cover
    return getpass.getpass(prompt + ': ')


def prompt_password_with_confirmation():  # pragma: no cover
    while True:
        password = prompt_password('Admin password')
        if not password:
            print('Password cannot be empty.')
            continue
        confirm_password = prompt_password('Confirm admin password')
        if password != confirm_password:
            print('Passwords do not match. Please try again.')
            continue
        return password


def confirm(prompt):  # pragma: no cover
    answer = input(prompt + ' [y/N]: ').strip().lower()
    return answer == 'y' or answer == 'yes'


def get_database_filename():
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if uri.startswith('sqlite:///'):
        return uri.replace('sqlite:///', '')
    return None


def ensure_user_columns():
    with app.app_context():
        result = db.session.execute(text("PRAGMA table_info('user')"))
        existing = {row[1] for row in result}
        alters = []
        if 'force_password_reset' not in existing:
            alters.append("ALTER TABLE user ADD COLUMN force_password_reset BOOLEAN NOT NULL DEFAULT 0")
        if 'failed_login_attempts' not in existing:
            alters.append("ALTER TABLE user ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0")
        if 'last_failed_login_at' not in existing:
            alters.append("ALTER TABLE user ADD COLUMN last_failed_login_at DATETIME NULL")
        if alters:
            for q in alters:
                db.session.execute(text(q))
            db.session.commit()


def main():
    args = parse_args()
    admin_username = args.admin_username or os.environ.get('ADMIN_USERNAME')
    admin_password = args.admin_password or os.environ.get('ADMIN_PASSWORD')
    branch_name = args.branch_name
    branch_address = args.branch_address

    if not admin_username:
        admin_username = input('Admin username: ').strip()
    if not admin_password:
        admin_password = prompt_password_with_confirmation()

    if not admin_username:
        print('Admin username is required.')
        raise SystemExit(1)
    if not admin_password:
        print('Admin password is required.')
        raise SystemExit(1)

    password_error = validate_password(admin_password)
    if password_error:
        if args.admin_password or os.environ.get('ADMIN_PASSWORD'):
            print('Password validation failed:', password_error)
            raise SystemExit(1)
        print('Password validation failed:', password_error)
        admin_password = prompt_password_with_confirmation()
        password_error = validate_password(admin_password)
        if password_error:
            print('Password validation failed:', password_error)
            raise SystemExit(1)

    db_file = get_database_filename()
    if args.force and db_file:
        if not args.skip_confirm and os.path.exists(db_file):
            if not confirm(f'WARNING: This will delete the existing database file {db_file}. Continue?'):
                print('Aborted.')
                raise SystemExit(1)
        if os.path.exists(db_file):
            os.remove(db_file)

    with app.app_context():
        db.create_all()
        ensure_user_columns()

        branch = Branch.query.filter_by(name=branch_name).first()
        if not branch:
            branch = Branch(name=branch_name, address=branch_address)
            db.session.add(branch)
            db.session.commit()
            print(f'Created branch {branch.name} (id={branch.id}).')
        else:
            print(f'Using existing branch {branch.name} (id={branch.id}).')

        admin = User.query.filter_by(username=admin_username).first()
        if admin:
            print(f'Updating existing admin account {admin_username}.')
            admin.role = 'admin'
            admin.branch_id = branch.id
            admin.locked = False
            admin.force_password_reset = False
            admin.failed_login_attempts = 0
            admin.set_password(admin_password)
        else:
            admin = User(
                username=admin_username,
                role='admin',
                branch_id=branch.id,
                force_password_reset=False,
                locked=False,
                failed_login_attempts=0,
            )
            admin.set_password(admin_password)
            db.session.add(admin)

        db.session.commit()
        print('Admin account is ready.')
        print(f'Username: {admin_username}')
        print('Remember your password and keep it secret.')

    print('Initialization complete.')


if __name__ == '__main__':
    main()
