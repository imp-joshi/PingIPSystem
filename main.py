# Importing the required libraries
import schedule, keyboard, platform, time, re, subprocess, os
from datetime import datetime
import pandas as pd
import pyodbc as db
import plotly.graph_objects as go
import plotly.offline as offline
import plotly.express as px

# Variables (Please fill in your own values)
input_table = 'IP_Master'               # Input table name
output_table = 'IP_History'                     # Output table name

retry = 4                               # Number of times to retry ping
pings = 1                               # Number of pings to send
success_threshold = 1                   # Number of successful pings to consider device up

# The folder where the graph will be saved
graph_folder = os.path.join(os.getcwd(), 'Graph')
print(graph_folder)
os.makedirs(graph_folder, exist_ok=True)    # Create the folder if it doesn't exist

# Establish connection to the MySQL Server
try:
    conn = db.connect('Driver={SQL Server};'
                      'Server=SQLEXPRESS;'
                      'Database=UCWL;'
                      'Trusted_Connection=yes;')
    print("Connection Successful")
except Exception as e:
    print("Error in Connection", e)

# Rest of the code here (Add the functions and the main program as provided in the code sample)

# Function to retrieve the list of IP addresses from the input table
def get_ip_list():
    query = f'SELECT IP_ADDRESS FROM {input_table}'
    df_ip = pd.read_sql_query(query, conn)
    ip_list = df_ip['IP_ADDRESS'].tolist()
    return ip_list

# Function to add a new row to the output table
def add_new_row(new_row):
    cursor = conn.cursor()
    insert_query = f"INSERT INTO {output_table} (IP_Address, Status, Timestamp, Maximum, Average, Bytes, TTL) VALUES (?, ?, ?, ?, ?, ?, ?)"
    cursor.execute(insert_query, new_row)
    cursor.commit()

def add_new_error_row(new_row):
    cursor = conn.cursor()
    insert_query = f"INSERT INTO {output_table} (IP_Address, Status, Timestamp, Maximum, Average, Bytes, TTL, ErrorResponse) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    cursor.execute(insert_query, new_row)
    cursor.commit()

# Function to generate a new output table based on the current date
def generate_output_table():
    #today = datetime.today().strftime('%Y-%m-%d')
    #global output_table
    #output_table = f"output_{today}"

    cursor = conn.cursor()
    create_table_query = f"""
        CREATE TABLE if not exists {output_table} (
            IP VARCHAR(255),
            Status INT,
            Timestamp varchar(19)
        )
    """
    try:
        cursor.execute(create_table_query)
        cursor.commit()
        print(f"Table {output_table} created successfully.")

    except Exception as e:
        print(f"Error creating table {output_table}:", e)

# Rest of the functions and the main program here (Add the remaining functions and the main loop as provided in the code sample)

# -------------------- Main Program --------------------

# Generate the initial output table, if it doesn't exist
generate_output_table()
ip_list = get_ip_list()     

# Loop to run ping() every 15 minutes
while True:
    try:
        if is_12am():
            try:
                generate_output_table()
            except Exception as e:
                print("Could not generate output table:", e)

        if is_15min():
            # Retrieve the list of IP addresses and ping them
            ip_list = get_ip_list()     # Retrieve the list of IP addresses before each ping operation
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"15 min cycle started at: {timestamp}")

            ping_loop(ip_list, timestamp)          # Ping all the IP addresses in the list
            print("Ping data successfully updated to database.")

            # Retrieve the output data and generate the graph
            try:
                try:
                    df = retrieve_output_data()
                except Exception as e:
                    print("Error retrieving output data:", e)
                generate_graph(df)
                print("Out Graph")
            except Exception as e:
                print("Error:", e)
                print ("Couldn't generate graph at:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                print()
            # time.sleep(60)

    except KeyboardInterrupt:
        print("Keyboard Interrupt")
        break

    except:
        print("Error")
        pass
    time.sleep(1)
print("Program terminated.")
