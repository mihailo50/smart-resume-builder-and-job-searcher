"""
Django management command to apply Supabase database schema.

This command reads SQL migration files and applies them to Supabase PostgreSQL
database using psycopg connection.

Usage:
    python manage.py apply_supabase_schema
    python manage.py apply_supabase_schema --skip-rls
    python manage.py apply_supabase_schema --file config/migrations/sql/001_initial_schema.sql
"""
import os
from pathlib import Path
from urllib.parse import urlparse
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import psycopg


class Command(BaseCommand):
    help = 'Apply Supabase database schema from SQL migration files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-rls',
            action='store_true',
            help='Skip Row Level Security policies migration',
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Apply specific SQL file instead of all migrations',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be executed without actually running it',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        # Validate Supabase configuration
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            raise CommandError(
                'DATABASE_URL is not set in environment variables. '
                'Please set it in your .env file.\n'
                'Format: postgresql://postgres:[password]@[host]:[port]/postgres'
            )

        # Parse DATABASE_URL to get connection details
        try:
            parsed = urlparse(database_url)
            db_host = parsed.hostname
            db_port = parsed.port or 5432
            db_user = parsed.username
            db_password = parsed.password
            db_name = parsed.path.lstrip('/') or 'postgres'
        except Exception as e:
            raise CommandError(f'Invalid DATABASE_URL format: {e}')

        self.stdout.write(
            self.style.SUCCESS(f'✓ Connecting to PostgreSQL at {db_host}:{db_port}')
        )

        # Connect to PostgreSQL database
        try:
            conn = psycopg.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                dbname=db_name,
                sslmode='require'
            )
            conn.autocommit = True
        except psycopg.OperationalError as e:
            raise CommandError(
                f'Failed to connect to database: {e}\n'
                'Please check your DATABASE_URL in .env file.'
            )
        except Exception as e:
            raise CommandError(f'Database connection error: {e}')

        # Determine which files to apply
        if options['file']:
            sql_files = [Path(options['file'])]
            if not sql_files[0].exists():
                # Try relative to BASE_DIR
                sql_files[0] = Path(settings.BASE_DIR) / options['file']
                if not sql_files[0].exists():
                    raise CommandError(f'SQL file not found: {options["file"]}')
        else:
            # Get all SQL files from migrations directory
            migrations_dir = Path(settings.BASE_DIR) / 'config' / 'migrations' / 'sql'
            
            if not migrations_dir.exists():
                raise CommandError(
                    f'Migrations directory not found: {migrations_dir}'
                )

            sql_files = sorted(migrations_dir.glob('*.sql'))
            
            if not sql_files:
                raise CommandError(
                    f'No SQL migration files found in {migrations_dir}'
                )

            # Filter out RLS file if --skip-rls is set
            if options['skip_rls']:
                sql_files = [f for f in sql_files if 'rls' not in f.name.lower()]

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Found {len(sql_files)} SQL file(s) to apply:'
            )
        )
        for sql_file in sql_files:
            self.stdout.write(f'  - {sql_file.name}')

        # Apply each SQL file
        try:
            for sql_file in sql_files:
                self.apply_sql_file(conn, sql_file, options['dry_run'])
            
            self.stdout.write(
                self.style.SUCCESS('\n✓ Schema migration completed successfully!')
            )
        except Exception as e:
            raise CommandError(f'Migration failed: {e}')
        finally:
            conn.close()

    def split_sql_statements(self, sql_content: str):
        """
        Split SQL content into individual statements.
        Handles semicolons within strings and comments.
        """
        statements = []
        current_statement = []
        in_string = False
        string_char = None
        comment_mode = None  # 'single' or 'multi'
        
        i = 0
        while i < len(sql_content):
            char = sql_content[i]
            next_char = sql_content[i + 1] if i + 1 < len(sql_content) else None
            
            # Handle comments
            if comment_mode == 'multi':
                if char == '*' and next_char == '/':
                    comment_mode = None
                    i += 2
                    continue
                i += 1
                continue
            elif char == '-' and next_char == '-':
                # Single-line comment
                comment_mode = 'single'
                i += 2
                continue
            elif char == '/' and next_char == '*':
                # Multi-line comment
                comment_mode = 'multi'
                i += 2
                continue
            
            if comment_mode == 'single':
                if char == '\n':
                    comment_mode = None
                i += 1
                continue
            
            # Handle strings
            if char in ("'", '"') and (i == 0 or sql_content[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
                current_statement.append(char)
                i += 1
                continue
            
            # Handle statement termination
            if char == ';' and not in_string:
                stmt = ''.join(current_statement).strip()
                if stmt:
                    statements.append(stmt)
                current_statement = []
                i += 1
                continue
            
            current_statement.append(char)
            i += 1
        
        # Add final statement if exists
        if current_statement:
            stmt = ''.join(current_statement).strip()
            if stmt:
                statements.append(stmt)
        
        return statements

    def apply_sql_file(self, conn, sql_file: Path, dry_run: bool):
        """Apply a single SQL file to Supabase PostgreSQL."""
        self.stdout.write(f'\nApplying: {sql_file.name}')

        try:
            # Read SQL file
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            if dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN - SQL would be executed:'))
                self.stdout.write('-' * 80)
                # Show first 500 characters
                preview = sql_content[:500]
                self.stdout.write(preview)
                if len(sql_content) > 500:
                    self.stdout.write(f'... ({len(sql_content) - 500} more characters)')
                self.stdout.write('-' * 80)
                return

            # Split SQL into statements
            statements = self.split_sql_statements(sql_content)
            
            self.stdout.write(f'  Parsed {len(statements)} SQL statement(s)')

            # Execute each statement
            cursor = conn.cursor()
            executed_count = 0
            error_count = 0

            for i, statement in enumerate(statements, 1):
                if not statement or statement.strip().startswith('--'):
                    continue
                
                try:
                    cursor.execute(statement)
                    executed_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Statement {i}/{len(statements)} executed')
                    )
                except psycopg.Error as e:
                    error_count += 1
                    # Some errors are expected (e.g., "already exists")
                    error_msg = str(e).strip()
                    if 'already exists' in error_msg.lower():
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠ Statement {i}/{len(statements)}: {error_msg[:100]}')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Statement {i}/{len(statements)} failed: {error_msg[:200]}')
                        )
                        # Continue with next statement
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Statement {i}/{len(statements)} error: {str(e)[:200]}')
                    )
            
            cursor.close()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'  ✓ Completed: {executed_count} executed, {error_count} with warnings/errors'
                )
            )

        except FileNotFoundError:
            raise CommandError(f'SQL file not found: {sql_file}')
        except Exception as e:
            raise CommandError(f'Error applying {sql_file.name}: {e}')









