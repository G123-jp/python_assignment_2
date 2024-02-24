from datetime import datetime
import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)


def execute_sql_from_file(filename, connection):
    # The schema.sql file is located at the root of the project directory
    project_root = os.path.dirname(os.path.dirname(app.root_path))
    schema_path = os.path.join(project_root, filename)

    with open(schema_path, 'r') as sql_file:
        sql_script = sql_file.read()
    connection.executescript(sql_script)


def init_db():
    # The database is in the data directory, two levels above the current file
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'financial_data.db')
    conn = sqlite3.connect("/Users/jimmyhomefolder/PycharmProjects/python_assignment_2/financial/api/data/financial_data.db")

    # Execute the schema.sql file to create the tables
    execute_sql_from_file('schema.sql', conn)

    conn.commit()
    conn.close()


# Initialize the database
init_db()


def query_financial_data(start_date, end_date, symbol, limit, page):
    offset = (page - 1) * limit
    params = []
    where_clauses = []

    if start_date:
        where_clauses.append("date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("date <= ?")
        params.append(end_date)
    if symbol:
        where_clauses.append("symbol = ?")
        params.append(symbol)

    where_statement = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Connect to the SQLite database
    db_path = "/Users/jimmyhomefolder/PycharmProjects/python_assignment_2/financial/api/data/financial_data.db"

    # Connect to the SQLite database using the absolute path
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Query for pagination data
    count_query = f"SELECT COUNT(*) FROM financial_data WHERE {where_statement}"
    cur.execute(count_query, params)
    total_count = cur.fetchone()[0]
    total_pages = (total_count + limit - 1) // limit

    # Query for actual data
    data_query = f"SELECT * FROM financial_data WHERE {where_statement} LIMIT ? OFFSET ?"
    cur.execute(data_query, params + [limit, offset])
    records = [dict(row) for row in cur.fetchall()]

    conn.close()

    return {
        "data": records,
        "pagination": {
            "count": total_count,
            "page": page,
            "limit": limit,
            "pages": total_pages
        },
        "info": ""
    }


@app.route('/financial_data', methods=['GET'])
def financial_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    symbol = request.args.get('symbol')
    limit = request.args.get('limit', default=5, type=int)
    page = request.args.get('page', default=1, type=int)

    # Validate date format
    for date_str in [start_date, end_date]:
        if date_str:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return jsonify({"data": [], "pagination": {}, "info": "Invalid date format. Use YYYY-MM-DD."}), 400

    result = query_financial_data(start_date, end_date, symbol, limit, page)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)