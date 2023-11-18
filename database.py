import os
import sqlite3
import functools
import logging
from typing import Optional

from dotenv import load_dotenv

from schema import Link

load_dotenv()

db_name = os.getenv("DB_NAME")


def connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
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
def create_link_table(conn=None, cursor=None):
    cursor.execute(
        """
CREATE TABLE link(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link TEXT UNIQUE, 
                content_file TEXT,
                email TEXT,
                contact_name TEXT,
                industry TEXT,
                city TEXT,
                area TEXT,
                parsed INTEGER DEFAULT 0,
                contacted_at TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)
"""
    )


@connection
def create_email_event_table(conn=None, cursor=None):
    cursor.execute(
        """
        CREATE TABLE email_event(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id INTEGER,
            qc_result INTEGER,
            qc_date TIMESTAMP,
            email_content TEXT,
            contacted_at TIMESTAMP,
            FOREIGN KEY (link_id) REFERENCES link(id)
        )
        """
    )


@connection
def db_create_link(link: str, conn=None, cursor=None):
    try:
        query = "INSERT OR IGNORE INTO link (link) VALUES (?)"
        data = (link,)

        cursor.execute(query, data)
        # conn.commit() # TODO Nessesary=?

        if cursor.rowcount == 0:
            logging.warning(f"Link {link} already exists in the database.")
        else:
            logging.info(f"Link {link} added to the database.")
    except Exception as e:
        logging.error(f"Error adding link {link}: {e}")


import logging


@connection
def db_create_email_event(
    link_id: int, qc_result: int, email_content: str, conn=None, cursor=None
):
    try:
        query = "INSERT INTO email_event (link_id, qc_result, email_content) VALUES (?, ?, ?)"
        data = (link_id, qc_result, email_content)

        cursor.execute(query, data)
        conn.commit()

        if cursor.rowcount == 0:
            logging.warning(
                f"Email event for link ID {link_id} was not added to the database."
            )
            return False
        else:
            logging.info(f"Email event for link ID {link_id} added to the database.")
            return True
    except Exception as e:
        logging.error(f"Error adding email event for link ID {link_id}: {e}")
        return False


@connection
def db_get_links(conn=None, cursor=None):
    query = "SELECT id, link FROM link WHERE content_file IS NULL"

    cursor.execute(query)

    rows = cursor.fetchall()

    return rows


@connection
def db_get_links_for_parsing(conn=None, cursor=None):
    query = "SELECT id, content_file FROM link WHERE parsed = 0 AND content_file IS NOT NULL"

    cursor.execute(query)

    rows = cursor.fetchall()

    return rows


from typing import Optional


@connection
def db_get_lead(conn=None, cursor=None) -> Optional[Link]:
    query = """
    SELECT link.*
    FROM link
    LEFT JOIN email_event ON link.id = email_event.link_id
    WHERE link.parsed = 1 AND link.email != 'None' AND email_event.id IS NULL
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
            "industry": row[5],
            "city": row[6],
            "area": row[7],
            "parsed": bool(row[8]),
            "contacted_at": row[9],
            "created_at": row[10],
        }
        return Link(**link_data)
    else:
        return None


@connection
def db_update_link_record(
    link_id,
    new_link=None,
    new_content_file=None,
    new_email=None,
    new_contact_name=None,
    new_industry=None,
    new_city=None,
    new_area=None,
    new_parsed=None,
    new_contacted_at=None,
    conn=None,
    cursor=None,
):
    # Start building the SQL update statement
    sql = "UPDATE link SET "
    params = []

    # Add fields to update, if provided
    if new_link is not None:
        sql += "link = ?, "
        params.append(new_link)
    if new_content_file is not None:
        sql += "content_file = ?, "
        params.append(new_content_file)
    if new_email is not None:
        sql += "email = ?, "
        params.append(new_email)
    if new_contact_name is not None:
        sql += "contact_name = ?, "
        params.append(new_contact_name)
    if new_industry is not None:
        sql += "industry = ?, "
        params.append(new_industry)
    if new_city is not None:
        sql += "city = ?, "
        params.append(new_city)
    if new_area is not None:
        sql += "area = ?, "
        params.append(new_area)
    if new_parsed is not None:
        sql += "parsed = ?, "
        params.append(new_parsed)
    if new_contacted_at is not None:
        sql += "contacted_at = ?, "
        params.append(new_contacted_at)

    # Remove trailing comma and space
    sql = sql.rstrip(", ")

    # Add the WHERE clause to specify which record to update
    sql += " WHERE id = ?"
    params.append(link_id)

    # Execute the SQL command
    cursor.execute(sql, tuple(params))
    conn.commit()


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


tables = {"link": create_link_table, "email_event": create_email_event_table}
