import os
import sqlite3
import functools
import logging
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv

from schema import Link, EmailEvent

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

# TODO Add subject
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

        if cursor.rowcount == 0:
            logging.warning(f"Link {link} already exists in the database.")
        else:
            logging.info(f"Link {link} added to the database.")
    except Exception as e:
        logging.error(f"Error adding link {link}: {e}")

# TODO Change contacted_at to deliverytime
@connection
def db_create_email_event(
    link_id: int,
    qc_result: int,
    email_content: str,
    deliverytime: datetime = None,
    conn=None,
    cursor=None,
):
    try:
        # Check if contacted_at is provided, adjust query and data accordingly
        if deliverytime:
            query = "INSERT INTO email_event (link_id, qc_result, email_content, contacted_at) VALUES (?, ?, ?, ?)"
            data = (link_id, qc_result, email_content, deliverytime)
        else:
            query = "INSERT INTO email_event (link_id, qc_result, email_content) VALUES (?, ?, ?)"
            data = (link_id, qc_result, email_content)

        cursor.execute(query, data)

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
def db_get_events(conn=None, cursor=None):
    query = """
        SELECT link.link, email_event.contacted_at
        FROM email_event
        INNER JOIN link ON email_event.link_id = link.id
        WHERE email_event.contacted_at IS NOT 'None'
        """

    cursor.execute(query)

    rows = cursor.fetchall()

    print(rows)

    # Fetch column names from cursor.description
    columns = [col[0] for col in cursor.description]

    # Convert rows to list of dictionaries
    events = [EmailEvent(**dict(zip(columns, row))) for row in rows]

    return events


@connection
def db_get_links_for_parsing(conn=None, cursor=None):
    query = "SELECT id, content_file FROM link WHERE parsed = 0 AND content_file IS NOT NULL"

    cursor.execute(query)

    rows = cursor.fetchall()

    return rows


@connection
def get_latest_email_event_date(conn=None, cursor=None):
    cursor.execute("SELECT MAX(contacted_at) FROM email_event")
    latest_date = cursor.fetchone()[0]
    return latest_date


# TODO Return time as well

@connection
def get_next_email_event_date(conn=None, cursor=None):
    latest_date = get_latest_email_event_date()

    # Check if latest_date is not None and is a string, then convert to date
    if latest_date is not None and isinstance(latest_date, str):
        latest_date_str = latest_date.split(' ')[0]
        latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d").date()
    else:
        # If there are no email events, use today's date
        return datetime.now().date()

    today = datetime.now().date()

    # Check if the latest email_event is more than 3 days in the future
    delta = latest_date - today
    days = delta.days
    if days > 3:
        raise Exception("Can't schedule more than 3 days in the future..")

    # If the latest email_event is before today, then return today
    if latest_date < today:
        return today

    # If the latest email_event is today or later, count the email_events for that day
    cursor.execute(
        "SELECT COUNT(*) FROM email_event WHERE DATE(contacted_at) = ?", (latest_date,))
    count = cursor.fetchone()[0]

    # If the count is less than 60, return that day
    if count < 20:
        return latest_date

    # Calculate the next day
    next_day = latest_date + timedelta(days=1)

    # Check if next_day is more than 3 days in the future
    delta = next_day - today
    days = delta.days
    if days > 3:
        raise Exception("Can't schedule more than 3 days in the future..")

    # Return next_day if it's within the 3-day limit
    return next_day



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
        if isinstance(new_industry, list):
            new_industry = ",".join(new_industry)
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
    data = tuple(params)
    # Execute the SQL command
    cursor.execute(sql, data)
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
