import os
import sqlite3
import functools
import logging
from typing import Optional

import bcrypt

from dotenv import load_dotenv

from schema import Link

load_dotenv()

db_name = os.getenv("DB_NAME")


def connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Connection to: {db_name}")
        # If a connection is already provided, use it.
        conn = kwargs.pop("conn", None)

        # Determine whether the decorator should manage the connection.
        manage_conn = False
        if conn is None:
            conn = sqlite3.connect(db_name)
            manage_conn = True

        cursor = conn.cursor()

        try:
            # Run the wrapped function.
            result = func(*args, conn=conn, cursor=cursor, **kwargs)

            # Commit the transaction.
            conn.commit()

            return result
        finally:
            # Close the connection if it was opened by the decorator.
            if manage_conn:
                conn.close()

    return wrapper


@connection
def create_worklog_table(conn=None, cursor=None):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS worklog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            domain TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES user(id)
        )
        """
    )


@connection
def create_user_table(conn=None, cursor=None):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            superuser INTEGER DEFAULT 0,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pay_rate DECIMAL DEFAULT 0.06
        )
        """
    )


@connection
def create_link_table(conn=None, cursor=None):
    cursor.execute(
        """
CREATE TABLE IF NOT EXISTS link(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link TEXT UNIQUE, 
                content_file TEXT,
                email TEXT,
                contact_name TEXT,
                pronoun TEXT,
                industry TEXT,
                city TEXT,
                area TEXT,
                parsed INTEGER DEFAULT 0,
                invalid INTEGER DEFAULT 0,
                contacted_at TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                classification INTEGER DEFAULT 0)
"""
    )


@connection
def create_lead_table(conn=None, cursor=None):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS lead(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            name TEXT,
            domain TEXT UNIQUE, 
            pronoun TEXT, 
            campaign_id INTEGER,
            area TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaign(id))
        """
    )


@connection
def create_sent_table(conn=None, cursor=None):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sent(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            domain TEXT UNIQUE)
        """
    )


@connection
def create_campaign_table(conn=None, cursor=None):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS campaign(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)
        """
    )


@connection
def db_create_worklog(
    user_id: int,
    domain: str,
    conn=None,
    cursor=None,
):
    query = "INSERT INTO worklog (user_id, domain) VALUES (?, ?)"
    data = (user_id, domain)

    try:
        cursor.execute(query, data)
        conn.commit()  # Commit the transaction
    except Exception as e:
        print(f"An error occurred: {e}")


@connection
def db_create_user(username, password, superuser, conn=None, cursor=None):
    # Hash the password
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    try:
        # Insert the new user into the users table
        cursor.execute(
            "INSERT INTO user (username, password_hash, superuser) VALUES (?, ?, ?)",
            (username, password_hash, superuser),
        )
        print(f"User {username} created successfully.")
    except sqlite3.IntegrityError:
        print("Error: That username is already taken.")
    except Exception as e:
        print(f"An error occurred: {e}")


@connection
def db_create_link(link: str, conn=None, cursor=None):
    try:
        query = "INSERT OR IGNORE INTO link (link) VALUES (?)"
        data = (link,)

        cursor.execute(query, data)

        if cursor.rowcount == 0:
            logging.warning(f"Link {link} already exists in the database.")
        else:
            logging.info(f"Link {link} added to the database.")
    except Exception as e:
        logging.error(f"Error adding link {link}: {e}")


@connection
def db_create_sent(domain: str, email: str = None, conn=None, cursor=None):
    """
    Inserts a new record into the 'sent' table with the given domain and email.

    Parameters:
    domain (str): The domain to insert.
    email (str): The email to insert. Default is None.

    The function uses a connection decorator to handle the database connection.
    """
    query = "INSERT INTO sent (domain, email) VALUES (?, ?)"
    data = (domain, email)

    try:
        cursor.execute(query, data)
        conn.commit()  # Commit the transaction
    except Exception as e:
        print(f"An error occurred: {e}")


@connection
def db_delete_link(id: int, conn=None, cursor=None):
    """
    Delete a link from the database based on its ID.

    :param id: The ID of the link to be deleted.
    :param conn: Database connection object.
    :param cursor: Database cursor object.
    :return: Number of rows affected by the delete operation.
    """
    try:
        query = "DELETE FROM link WHERE id = ?"
        cursor.execute(query, (id,))
        return cursor.rowcount
    except Exception as e:
        logging.error(f"Error deleting link with id {id}: {e}")
        return -1


@connection
def db_create_lead(
    email: str,
    name: str,
    domain: str,
    pronoun: str,
    campaign_id: int,
    area: str,
    conn=None,
    cursor=None,
):
    """
    Insert a new lead into the database.

    :param email: Email of the lead.
    :param name: Name of the lead.
    :param domain: Domain associated with the lead.
    :param pronoun: Pronoun of the lead.
    :param campaign_id: Campaign id associated with the lead.
    :param area: Area associated with the lead.
    :param conn: Database connection object.
    :param cursor: Database cursor object.
    :return: Status of the database operation.
    """
    try:
        query = "INSERT OR IGNORE INTO lead (email, name, domain, pronoun, campaign_id, area) VALUES (?,?,?,?,?,?)"
        data = (
            email,
            name,
            domain,
            pronoun,
            campaign_id,
            area,
        )

        cursor.execute(query, data)

        if cursor.rowcount == 0:
            logging.warning(f"Lead with email {email} already exists in the database.")
        else:
            logging.info(f"Lead with email {email} added to the database.")
        return cursor.rowcount
    except Exception as e:
        logging.error(f"Error adding lead with email {email}: {e}")
        return -1


@connection
def db_create_campaign(
    name: str,
    conn=None,
    cursor=None,
):
    """
    Insert a new campaign into the database.

    :param name: Name of the campaign.
    """
    try:
        query = "INSERT INTO campaign (name) VALUES (?)"
        data = (name,)

        cursor.execute(query, data)

        if cursor.rowcount == 0:
            logging.warning(
                f"Campaign with email {name} already exists in the database."
            )
        else:
            logging.info(f"Campaign with email {name} added to the database.")
        return cursor.rowcount
    except Exception as e:
        logging.error(f"Error adding campaign with email {name}: {e}")
        return -1


@connection
def db_get_campaign(
    campaign_name: str = None, campaign_id: int = None, conn=None, cursor=None
):
    if campaign_name:
        query = "SELECT * FROM campaign WHERE name = ?"
        cursor.execute(query, (campaign_name,))
    elif campaign_id is not None:
        query = "SELECT * FROM campaign WHERE id = ?"
        cursor.execute(query, (campaign_id,))
    else:
        raise ValueError("Either campaign_name or campaign_id must be provided")

    rows = cursor.fetchone()
    return rows


@connection
def db_get_campaigns(conn=None, cursor=None):
    query = "SELECT * FROM campaign"

    cursor.execute(query)

    rows = cursor.fetchall()

    return rows


@connection
def db_get_worklogs(user_id, conn=None, cursor=None):
    query = "SELECT * FROM worklog WHERE user_id = ?"

    cursor.execute(query, (user_id,))

    rows = cursor.fetchall()

    return rows


@connection
def db_get_links(conn=None, cursor=None):
    query = "SELECT id, link FROM link WHERE content_file IS NULL AND invalid = 0"

    cursor.execute(query)

    rows = cursor.fetchall()

    return rows


@connection
def db_get_user(username, conn=None, cursor=None):
    query = "SELECT * FROM user WHERE username = ?"
    cursor.execute(query, (username,))
    row = cursor.fetchone()
    return row


# TODO Change name?
@connection
def db_get_lead(conn=None, cursor=None) -> Optional[Link]:
    # Query to select links that are parsed, have an email, and are not present in the 'sent' table
    query = """
    SELECT l.id, l.link, l.content_file, l.email, l.contact_name, l.pronoun, l.industry, l.city, l.area, l.parsed FROM link l
    LEFT JOIN sent s ON l.link = s.domain
    WHERE l.parsed = 1 AND l.email != 'None' AND s.id IS NULL
    LIMIT 1
    """
    cursor.execute(query)
    row = cursor.fetchone()
    if row is not None:
        link_data = {
            "id": row[0],
            "link": row[1],
            "content_file": row[2],
            "email": row[3],
            "contact_name": row[4],
            "pronoun": row[5],
            "industry": row[6],
            "city": row[7],
            "area": row[8],
            "parsed": bool(row[9]),
        }
        return Link(**link_data)
    else:
        return None


@connection
def db_get_lead_count_remainder(conn=None, cursor=None) -> Optional[int]:
    # Query to select the count of links that are parsed, have an email, and are not present in the 'sent' table
    query = """
    SELECT COUNT(*) FROM link l
    LEFT JOIN sent s ON l.link = s.domain
    WHERE l.parsed = 1 AND l.email != 'None' AND s.id IS NULL
    """

    cursor.execute(query)
    result = cursor.fetchone()
    return result[0] if result else None


@connection
def db_get_unscraped_links(conn=None, cursor=None) -> Optional[int]:
    # Query to select the count of links that havent been scraped for content
    query = "SELECT COUNT(*) FROM link WHERE parsed = 0 AND invalid = 0 AND content_file IS NULL"
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0] if result else None


@connection
def db_get_unparsed_links(conn=None, cursor=None):
    # Query all scraped links that haven't been parsed by AI yet
    query = "SELECT id, content_file FROM link WHERE parsed = 0 AND invalid = 0 AND classification = 0 AND content_file IS NOT NULL"

    cursor.execute(query)

    rows = cursor.fetchall()

    return rows


@connection
def db_get_one_lead(lead_id: str, conn=None, cursor=None):
    query = "SELECT * FROM lead where id = ?"
    cursor.execute(query, (lead_id,))
    row = cursor.fetchone()
    return row


@connection
def db_delete_leads(campaign_id, conn=None, cursor=None):
    query = "DELETE from lead where campaign_id = ?"
    cursor.execute(query, (campaign_id,))


@connection
def db_get_leads(campaign_id, conn=None, cursor=None):
    query = (
        "SELECT id, email, name, domain, pronoun, area FROM lead WHERE campaign_id = ?"
    )

    cursor.execute(query, (campaign_id,))
    rows = cursor.fetchall()

    return rows


# TODO Data should be normalized e.g. None = none etc
@connection
def db_get_all_leads(conn=None, cursor=None):
    query = """
    SELECT link, email, contact_name, pronoun, area FROM link
    WHERE parsed = 1 AND LOWER(email) != 'none' AND LOWER(area) != 'none' AND LOWER(contact_name) != 'none'
    AND link NOT IN (
        SELECT domain FROM sent
    )
    """
    cursor.execute(query)
    result = cursor.fetchall()
    return result


@connection
def db_delete_all_leads(conn=None, cursor=None):
    query = """
    DELETE FROM link
    WHERE parsed = 1 AND LOWER(email) != 'none' AND LOWER(area) != 'none' AND LOWER(contact_name) != 'none'
    AND link NOT IN (
        SELECT domain FROM sent
    )
    """
    cursor.execute(query)
    conn.commit()
    return cursor.rowcount


@connection
def db_get_lead_count_from_campaign(campaign_id, conn=None, cursor=None):
    query = "SELECT COUNT(*) FROM lead WHERE campaign_id = ?"

    cursor.execute(query, (campaign_id,))

    # Fetch the result
    result = cursor.fetchone()
    if result:
        return result[0]  # This will return the count
    else:
        return 0


@connection
def db_get_lead_count(conn=None, cursor=None):
    query = "SELECT COUNT(*) FROM lead"

    cursor.execute(
        query,
    )

    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return 0


@connection
def db_get_sent(domain: str = None, email: str = None, conn=None, cursor=None):
    """
    Checks if there is a record in the 'sent' table that matches the given domain or email.

    Parameters:
    domain (str): The domain to search for. Default is None.
    email (str): The email to search for. Default is None.

    Returns:
    bool: True if a matching record is found, False otherwise.
    """
    if domain is None and email is None:
        return False

    query_parts = []
    params = []

    if domain is not None:
        query_parts.append("domain = ?")
        params.append(domain)

    if email is not None:
        query_parts.append("email = ?")
        params.append(email)

    query = f"SELECT COUNT(*) FROM sent WHERE {' OR '.join(query_parts)}"

    try:
        cursor.execute(query, tuple(params))
        result = cursor.fetchone()
        return result[0] > 0
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


@connection
def db_update_link_record(
    link_id,
    link=None,
    content_file=None,
    email=None,
    contact_name=None,
    pronoun=None,
    industry=None,
    city=None,
    area=None,
    parsed=None,
    invalid=None,
    contacted_at=None,
    classification=None,
    conn=None,
    cursor=None,
):
    # Start building the SQL update statement
    sql = "UPDATE link SET "
    params = []

    # Add fields to update, if provided
    if link is not None:
        sql += "link = ?, "
        params.append(link)
    if content_file is not None:
        sql += "content_file = ?, "
        params.append(content_file)
    if email is not None:
        if isinstance(email, list):
            email = ",".join(email)
        sql += "email = ?, "
        params.append(email)
    if contact_name is not None:
        sql += "contact_name = ?, "
        params.append(contact_name)
    if pronoun is not None:
        sql += "pronoun = ?, "
        params.append(pronoun)
    if industry is not None:
        if isinstance(industry, list):
            industry = ",".join(industry)
        sql += "industry = ?, "
        params.append(industry)
    if city is not None:
        if isinstance(city, list):
            city = ",".join(city)
        sql += "city = ?, "
        params.append(city)
    if area is not None:
        if isinstance(area, list):
            area = ",".join(area)
        sql += "area = ?, "
        params.append(area)
    if parsed is not None:
        sql += "parsed = ?, "
        params.append(parsed)
    if invalid is not None:
        sql += "invalid = ?, "
        params.append(invalid)
    if contacted_at is not None:
        sql += "contacted_at = ?, "
        params.append(contacted_at)
    if classification is not None:
        sql += "classification = ?, "
        params.append(classification)

    # Remove trailing comma and space
    sql = sql.rstrip(", ")

    # Add the WHERE clause to specify which record to update
    sql += " WHERE id = ?"
    params.append(link_id)
    data = tuple(params)
    # Execute the SQL command
    cursor.execute(sql, data)
    conn.commit()


@connection
def db_update_lead(
    id,
    email=None,
    name=None,
    domain=None,
    pronoun=None,
    campaign_id=None,
    area=None,
    conn=None,
    cursor=None,
):
    # Start building the SQL update statement
    sql = "UPDATE lead SET "
    params = []

    # Add fields to update, if provided
    if email is not None:
        sql += "email = ?, "
        params.append(email)
    if name is not None:
        sql += "name = ?, "
        params.append(name)
    if domain is not None:
        sql += "domain = ?, "
        params.append(domain)
    if pronoun is not None:
        sql += "pronoun = ?, "
        params.append(pronoun)
    if campaign_id is not None:
        sql += "campaign_id = ?, "
        params.append(campaign_id)
    if area is not None:
        sql += "area = ?, "
        params.append(area)

    # Remove trailing comma and space
    sql = sql.rstrip(", ")

    # Add the WHERE clause to specify which record to update
    sql += " WHERE id = ?"
    params.append(id)
    data = tuple(params)
    # Execute the SQL command
    cursor.execute(sql, data)
    conn.commit()


@connection
def db_verify_password(username, provided_password, conn=None, cursor=None):
    # Fetch the user by username
    cursor.execute("SELECT password_hash FROM user WHERE username = ?", (username,))
    result = cursor.fetchone()
    if result is None:
        return False

    stored_hash = result[0]

    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode("utf-8")

    return bcrypt.checkpw(provided_password.encode("utf-8"), stored_hash)


@connection
def check_table_exists(table_name, conn=None, cursor=None):
    cursor.execute(
        f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    )
    count = cursor.fetchone()[0]

    if count == 1:
        return True
    else:
        return False


tables = {
    "link": create_link_table,
    "lead": create_lead_table,
    "campaign": create_campaign_table,
    "sent": create_sent_table,
    "user": create_user_table,
    "worklog": create_worklog_table,
}
