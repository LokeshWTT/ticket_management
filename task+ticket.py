import sys
import getpass
import requests
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QFrame, QDesktopWidget
from PyQt5.QtCore import QUrl, Qt, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtGui import QDesktopServices, QWindow
import json
import time

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.WindowsModifier and event.key() == Qt.Key_D:
            # Suppress the Win+D shortcut
            event.ignore()
        else:
            super().keyPressEvent(event)

class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if _type == QWebEnginePage.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False
        return super().acceptNavigationRequest(url, _type, isMainFrame)


class TicketSystem(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.fetch_initial_data()

    def initUI(self):
        self.setup_window()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.username_label = QLabel()

        # Boxes for open and closed counts
        self.open_box = self.create_info_box("Open")
        self.closed_box = self.create_info_box("Closed")

        # Web view for incidents and news
        self.webview = QWebEngineView()
        self.webview.setPage(CustomWebEnginePage(self.webview))
        layout.addWidget(self.webview)

        # Timer for periodic updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(60000)  # 60 seconds interval

    def setup_window(self):
        # Set window flags to make it a desktop widget
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnBottomHint)

        # Set initial size
        self.resize(310, 450)

        # Get the primary screen geometry
        screen = QDesktopWidget().screenGeometry(0)  # 0 for primary screen

        # Calculate the position for the top right corner of the primary screen
        x = screen.width() - self.width()
        y = 1  # Top right corner

        # Set the geometry
        self.setGeometry(x, y, self.width(), self.height())

        self.setStyleSheet("background-color: white;")

    def fetch_initial_data(self):
        username = getpass.getuser()


        self.username_label.setText(f"Name: {username.upper()}")

        # Fetch user email and add a delay
        email, full_name = self.fetch_user_email(username)
        if email:
            print(f"Email for username '{username}': {email}")
        else:
            print(f"No email found for username '{username}'.")

        # Fetch user info and add a delay
        if email:
            user_id, name = self.fetch_user_info(email)
            if user_id and name:
                print(f"User ID: {user_id}, Name: {name}")
            else:
                print(f"No user info found for email '{email}'.")
        else:
            user_id, name = "", ""

        # Fetch incidents data and add a delay
        if name:
            incidents_data = self.fetch_incidents_data(name)
            incidents_data1 = self.fetch_incidents_data1(name)
            open_count = sum(1 for incident in incidents_data if incident.get('status') == 'Pending')
            close_count = sum(1 for incident in incidents_data if incident.get('status') == 'Completed')
        else:
            incidents_data = []
            incidents_data1 = []
            open_count = close_count = 0

        # Fetch news and add a delay
        news_text = self.fetch_news()

        # Update the UI
        self.update_ui(open_count, close_count, incidents_data, incidents_data1, news_text, full_name)

    def update_data(self):
        username = getpass.getuser()

        email, full_name = self.fetch_user_email(username)
        user_id, name = self.fetch_user_info(email)
        incidents_data = self.fetch_incidents_data(name)
        incidents_data1 = self.fetch_incidents_data1(name)
        open_count = sum(1 for incident in incidents_data if incident.get('status') == 'Pending')
        close_count = sum(1 for incident in incidents_data if incident.get('status') == 'Completed')
        news_text = self.fetch_news()

        self.update_ui(open_count, close_count, incidents_data, incidents_data1, news_text, full_name)

    def update_ui(self, open_count, close_count, incidents_data, incidents_data1, news_text, full_name):
        self.open_box['count_label'].setText(str(open_count))
        self.closed_box['count_label'].setText(str(close_count))

        # Prepare HTML content
        html_content = self.generate_html(incidents_data, news_text, full_name, incidents_data1)

        # Load HTML content into QWebEngineView
        self.webview.setHtml(html_content, QUrl(''))

        # Calculate lists
        open_incidents = [incident for incident in incidents_data if incident.get('status') == 'Pending']
        open_incidents1 = [incident for incident in incidents_data1 if incident.get('status') == 'Open']

        # Adjust window size based on data presence
        if not open_incidents and not open_incidents1:
            self.setGeometry(self.x(), self.y(), 310, 250)
        elif not open_incidents or not open_incidents1:
            self.setGeometry(self.x(), self.y(), 310, 450)
        else:
            self.setGeometry(self.x(), self.y(), 310, 750)

    def generate_html(self, incidents_data, news_text, full_name, incidents_data1):
        username = getpass.getuser().capitalize()

        open_incidents = [incident for incident in incidents_data if
                          incident.get('status') in ['Pending', 'Partially pending']]
        open_incidents1 = [incident for incident in incidents_data1 if incident.get('status') == 'Open']

        current_date = datetime.now()

        # Calculate overdue count
        overdue_count = sum(
            1 for incident in incidents_data1
            if incident.get('status') == 'Open' and
            incident.get('report_date') and
            (current_date - datetime.strptime(incident['report_date'], '%d-%m-%y')).days > 3
        )



        # Pre-calculate necessary values
        has_open_incidents = len(open_incidents1) > 0
        open_incidents_count = len(open_incidents1)
        closed_incidents_count = len([incident for incident in incidents_data1 if incident.get('status') == 'Closed'])
        pending_count = len([incident for incident in incidents_data if incident.get('status') == 'Pending'])
        partially_pending_count = len(
            [incident for incident in incidents_data if incident.get('status') == 'Partially pending'])

        table_html = ""
        if pending_count > 0 or partially_pending_count > 0:
            table_html = f"""
            <h3 style="font-size: 16px; margin-top: 10px; text-align: center;">Task System</h3>


              <div class="box-container">
                        <div class="box" style="background-color: #f87c7c; font-size: 14px;">
                            <h3>Pending</h3>
                            <p>{len([incident for incident in incidents_data if incident.get('status') == 'Pending'])}</p>
                        </div>
                        <div class="box" style="background-color: #FFA07A; font-size: 14px;">
                            <h3>&nbsp;Partially Pending</h3>
                            <p>{len([incident for incident in incidents_data if incident.get('status') == 'Partially pending'])}</p>
                        </div>
                        <div class="box" style="background-color: #87A96B; font-size: 14px;">
                            <h3>Completed</h3>
                            <p>{len([incident for incident in incidents_data if incident.get('status') == 'Completed'])}</p>
                        </div>
                    </div>
                   <div class="table-container" style="margin-bottom: 20px;"> <!-- Added margin to create space -->
    <table class="table table-bordered">
        <thead class="thead-dark">
            <tr>
                <th style="font-size: 10px; background-color: #001F5C; padding: 5px;">Assigned By</th> <!-- Added padding for spacing -->
                <th style="font-size: 10px; background-color: #001F5C; padding: 5px;">Type Of Work</th>
                <th style="font-size: 10px; background-color: #001F5C; padding: 5px;">From Time</th>
                <th style="font-size: 10px; background-color: #001F5C; padding: 5px;">To Time</th>
            </tr>
        </thead>
        <tbody id="incidentsTableBody">
            {self.generate_incidents_table(open_incidents)}
        </tbody>
    </table>
</div>
            """

        # Conditionally generate parts of the HTML
        ticket_system_html = ""
        if has_open_incidents:
            ticket_system_html = f"""
                <div style="text-align: center; flex-grow: 1;">
                    <h3 style="font-size: 16px; margin-top: 10px; text-align: center;">Ticket System</h3>
                </div>
                <div class="box-container">
                    <div class="box" style="background-color: #f87c7c;">
                        <h3>Overdue</h3>
                        <p>{overdue_count}</p>
                    </div>
                    <div class="box" style="background-color: #FFA07A;">
                        <h3>Open</h3>
                        <p>{open_incidents_count}</p>
                    </div>
                    <div class="box" style="background-color: #87A96B;">
                        <h3>Closed</h3>
                        <p>{closed_incidents_count}</p>
                    </div>
                </div>
                <div class="table-container">
                        <table class="table table-bordered">
                            <thead class="thead-dark">
                                <tr>
                                
                                    <th style="font-size: 10px; background-color: #001F5C;">Assigned By</th>
                                    <th style="font-size: 10px; background-color: #001F5C;">Subject</th>
                                    <th style="font-size: 10px; background-color: #001F5C;">Date</th>
                                    <th style="font-size: 10px; background-color: #001F5C;">Priority</th>
                                </tr>
                            </thead>
                            <tbody id="incidentsTableBody">
                                {self.generate_incidents_table1(open_incidents1)}
                            </tbody>
                        </table>
                    </div>
                """

        html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
                <title>Ticket Management System</title>
            </head>
            <style>

                /* Custom CSS styles */
                body {{
                    background-color: #f8f9fa;
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                }}

                .container {{
                    margin-top: 5px;
                    padding: 5px;
                }}


                .box {{
                 display: flex;
                    justify-content: center;
                    width: 120px; /* Adjust width to make it rectangular */
                    height: 50px; /* Adjust height to make it rectangular */
                    margin: 3px;
                    padding: -1px;
                    border: 1px solid #ccc;
                    background-color: #e9ecef;
                    text-align: center;
                    display: inline-block;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}

                .box h3 {{
                    margin: 5px 0;
                    font-size: 10px;
                    color: #495057;
                    font-weight: bold;
                }}

                .box p {{
                    font-size: 18px;
                    color: #343a40;
                    margin: 0;
                }}

                .table-container {{
                    max-height: 200px; /* Set a fixed height for the table container */
                    overflow-y: auto; /* Enable vertical scrolling */
                    border: 1px solid #dee2e6; /* Add a border around the table */
                    border-radius: 4px; /* Rounded corners for the container */
                    margin-top: 10px; /* Add space above the table */
                }}

                .table {{
                    width: 100%;
                    height:200px;
                    margin-bottom: 0; /* Remove bottom margin to fit in the container */
                    color: #212529;
                    border-collapse: collapse;
                }}

                .table th,
                .table td {{
                    padding: 5px;
                    vertical-align: top;
                    border-top: 1px solid #dee2e6;
                    font-size: 12px; /* Adjust font size for table headers and data cells */
                }}

                .table thead th {{
                    vertical-align: bottom;
                    border-bottom: 2px solid #dee2e6;
                    background-color: #001F5C;
                    color: #fff;
                }}

                .table tbody+tbody {{
                    border-top: 2px solid #dee2e6;
                }}

                .table-bordered {{
                    border: 1px solid #dee2e6;
                }}

                .alert {{
                    padding: 5px 8px;
    margin-bottom: 0; /* Remove bottom margin to fit in the container */
    border: 1px solid transparent;
    border-radius: 4px;
    overflow: hidden; /* Hide overflow content */
                }}

                .alert-info {{
                    color: #0c5460;
                    background-color: #d1ecf1;
                    border-color: #bee5eb;
                }}

                /* Adjust specific column widths */
                .table th:nth-child(1),
                .table td:nth-child(1) {{
                    width: 25%; /* Adjust width of the Date column */
                }}

                .table th:nth-child(2),
                .table td:nth-child(2) {{
                    width: 28%; /* Adjust width of the Assigned By column */
                }}

                .table th:nth-child(3),
                .table td:nth-child(3) {{
                    width: 25%; /* Adjust width of the Subject column */
                }}

                #news {{
                    margin-top: 20px; /* Adjust this value to move the news section further down */
                    overflow: hidden; /* Hide overflow content */
                    white-space: nowrap; /* Prevent news text from wrapping */
                    position: relative;
                }}

                .marquee {{
                    display: inline-block;
                    animation: marquee 15s linear infinite; /* Marquee animation */
                }}

                @keyframes marquee {{
                    0% {{
                        transform: translateX(100%);
                    }}
                    100% {{
                        transform: translateX(-100%);
                    }}
                }}

                /* Adjust image styles */
                .logo-img {{
                    width: 30px; /* Adjust width of the image */
                    height: auto; /* Maintain aspect ratio */
                    margin-right: 10px; /* Add spacing between logo and text */
                }}
                .box-container {{
    display: flex;
    justify-content: center;
    margin-top: 10px; /* Add space above the boxes */
}}

            </style>
            <body>
                <div class="container">
                    <div class="heading" style="display: flex; align-items: center; justify-content: space-between;">
    <div style="text-align: left; flex-grow: 1;">
        <h2 style="font-size: 16px; margin-right: 15px;">{full_name}</h2>
    </div>
    <img src="https://erp.wttindia.com/files/wttlogo7074b6.png" alt="WTT Logo" class="logo-img" style="height: 30px; width: auto;">
</div>

                    </div>

                   {table_html}
</div>
<div style="margin-top: 20px;"> <!-- Added margin to create space -->
    {ticket_system_html} <!-- Inject ticket system HTML here if it exists -->
</div>


                    <div id="news" class="alert alert-info" role="alert">
                        <div class="marquee">
                            {news_text}
                        </div>
                    </div>
                </div>
                <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
                <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
                <script>
                    var incidentsData = {json.dumps(open_incidents)};
                    var newsText = "{news_text}";
                    function updateIncidents(data) {{
                        // Your logic to update incidents
                    }}
                    function updateNews(text) {{
                        // Your logic to update news
                    }}
                    updateIncidents(incidentsData);
                    updateNews(newsText);
                </script>
            </body>
            </html>
            """
        return html_content

    def parse_datetime(datetime_str):
        try:
            # Try parsing with microseconds
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            # If that fails, try without microseconds
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')

    def parse_datetime(self, datetime_str):
        try:
            # Try parsing with microseconds
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            # If that fails, try without microseconds
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')

    def generate_incidents_table(self, incidents):
        table_rows = ""
        for incident in incidents:
            from_time = incident.get('from_time', '')
            to_time = incident.get('to_time', '')

            if from_time:
                creation_date_formatted = from_time.split('.')[0]
            else:
                creation_date_formatted = ''

            if to_time:
                creation_date_formatted1 = to_time.split('.')[0]
            else:
                creation_date_formatted1 = ''

            table_rows += f"""
            <tr>
                <td>{incident.get('assigned_by', 'No assigned_by')}</td>
                <td><a href="https://erp.wttindia.com/app/task-allocation/{incident.get('parent', 'No parent')}">{incident.get('type_of_work', 'No type_of_work')}</a></td>
                <td>{creation_date_formatted}</td>
                <td>{creation_date_formatted1}</td>
            </tr>
            """
        return table_rows

    def generate_incidents_table1(self, incidents):
        table_rows = ""
        current_date = datetime.now()

        for incident in incidents:
            # Convert the report date to a datetime object
            try:
                # Use the correct format for parsing
                report_date = datetime.strptime(incident['report_date'], '%d-%m-%y')
            except ValueError:
                report_date = None
                print(f"Invalid report date format for incident: {incident}")

            if report_date:
                age_days = (current_date - report_date).days

                # Determine the row color based on age
                if age_days > 7:
                    row_color = '#FFDDDD'  # Red for overdue by more than 7 days
                elif age_days > 3:
                    row_color = '#FFFFDD'  # Yellow for overdue by more than 3 days
                else:
                    row_color = '#FFFFFF'  # White for less than or equal to 3 days overdue

                table_rows += f"""
                <tr style="background-color: {row_color};">
                    
                    <td>{incident['employee_name']}</td>
                    <td><a href="https://erp.wttindia.com/app/ticket/{incident['ticket_no']}">{incident['incident']}</a></td>
                    <td>{incident['report_date']}</td>
                    <td>{incident['ticket_priority']}</td>
                </tr>
                """
            else:
                print(f"Report date is None for incident: {incident}")

        return table_rows

    def create_info_box(self, label_text):
        box_frame = QFrame()
        box_frame.setFrameShape(QFrame.StyledPanel)
        box_frame.setStyleSheet("background-color: #e9ecef; border: 1px solid #ccc; border-radius: 8px; margin: 3px;")

        layout = QVBoxLayout()
        box_frame.setLayout(layout)

        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; font-size: 14px; color: #495057;")
        layout.addWidget(label, alignment=Qt.AlignCenter)

        count_label = QLabel("0")
        count_label.setStyleSheet("font-size: 18px; color: #343a40;")
        count_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(count_label, alignment=Qt.AlignCenter)

        return {'frame': box_frame, 'count_label': count_label}

    def fetch_user_email(self, username):
        try:
            api_url = 'https://erp.wttindia.com/api/method/wtt_module.tickets_system.get_user_ticket_username'
            response = requests.get(api_url, params={'username': username})
            response.raise_for_status()
            data = response.json().get('data', [])

            for user_data in data:
                if user_data.get('ticket_user') == username:
                    return user_data.get('email'), user_data.get('full_name')
            return '', ''  # No matching email or full_name found
        except requests.exceptions.RequestException:
            return '', ''

    def fetch_owner_name(self, email):
        try:
            api_url1 = 'https://erp.wttindia.com/api/method/wtt_module.tickets_system.get_username'
            response1 = requests.get(api_url1, params={'email': email})
            response1.raise_for_status()
            data1 = response1.json().get('data', [])

            for user_data1 in data1:
                if user_data1.get('user_id') == email:
                    return user_data1.get('user_id'), user_data1.get('employee_name')
            return None, None  # No matching user info found
        except requests.exceptions.RequestException:
            return None, None

    def fetch_user_info(self, email):
        try:
            api_url = 'https://erp.wttindia.com/api/method/wtt_module.tickets_system.get_username'
            response = requests.get(api_url, params={'email': email})
            response.raise_for_status()
            data = response.json().get('data', [])

            for user_data in data:
                if user_data.get('user_id') == email:
                    return user_data.get('user_id'), user_data.get('name')
            return None, None  # No matching user info found
        except requests.exceptions.RequestException:
            return None, None

    def fetch_incidents_data(self, name):
        try:
            api_url = 'https://erp.wttindia.com/api/method/wtt_module.tickets_system.task_allocation'
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json().get('data', [])

            filtered_data = []
            owner_emails = set()

            for item in data:
                if item['employee'] == name:
                    owner_emails.add(item.get('owner'))

            # Fetch user details for each unique email
            email_to_name = {}
            for email in owner_emails:
                if email:
                    fetched_email, full_name = self.fetch_owner_name(email)
                    if fetched_email:
                        email_to_name[fetched_email] = full_name

            # Populate the filtered_data with full names
            for item in data:
                if item['employee'] == name:
                    # Set 'assigned_by' based on owner being 'Administrator' or fetching from 'email_to_name'
                    assigned_by = "Administrator" if item.get("owner") == "Administrator" else email_to_name.get(
                        item.get("owner"), "unknown")

                    # Append filtered data with the assigned_by field
                    filtered_data.append({
                        "employee_name": item.get("employee_name", "Unknown"),
                        "from_time": item.get("from_time", "No Time"),
                        "to_time": item.get("to_time", "No Time"),
                        "status": item.get("status", "No status"),
                        "type_of_work": item.get("type_of_work", "No work"),
                        "creation": item.get("creation", "No work"),
                        "assigned_by": assigned_by,  # Use the assigned_by variable here
                        "parent": item.get("parent", "No parent")
                    })

            # Print filtered data before returning
            print(filtered_data)

            return filtered_data

        except requests.exceptions.RequestException:
            return []

    def fetch_incidents_data1(self, name):
        try:
            api_url = 'https://erp.wttindia.com/api/method/wtt_module.tickets_system.call_taskmanager'
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json().get('data', [])

            filtered_data1 = []
            owner_emails = set()

            for item in data:
                if item.get('incident_made_by', '').lower() == name.lower():
                    owner_emails.add(item.get('owner'))

            # Fetch user details for each unique email
            email_to_name = {}
            for email in owner_emails:
                if email:
                    fetched_email, full_name = self.fetch_owner_name(email)
                    if fetched_email:
                        email_to_name[fetched_email] = full_name

            # Populate the filtered_data1 with full names
            for item in data:
                assigned_by = "Administrator" if item.get("owner") == "Administrator" else email_to_name.get(
                    item.get("owner"), "unknown")
                if item.get('incident_made_by', '').lower() == name.lower():
                    try:
                        report_date = datetime.strptime(item['report_date'], '%Y-%m-%d')
                        formatted_report_date = report_date.strftime('%d-%m-%y')
                    except ValueError:
                        formatted_report_date = 'Invalid date format'

                    filtered_data1.append({
                        'report_date': formatted_report_date,
                        'incident': item.get('incident', 'No incident'),
                        'employee_name': assigned_by,
                        'status': item.get('status', 'Unknown'),
                        'ticket_no': item.get('name', 'No ticket_no'),
                        'ticket_priority': item.get('ticket_priority', 'No priority'),
                    })

            return filtered_data1

        except requests.exceptions.RequestException:
            return []
    def fetch_news(self):
        try:
            api_url = 'https://erp.wttindia.com/api/method/wtt_module.tickets_system.call_news'
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json().get('data', [])
            if data:
                return list(data[0].values())[0]
            else:
                return "No news data found."
        except requests.exceptions.RequestException:
            return ""
    def parse_datetime(self, date_str):

        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S') if date_str else None
        except ValueError:
            return None


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = TicketSystem()
    window.show()
    sys.exit(app.exec_())
    #
    # window = MainWindow()
    # window.show()
    # sys.exit(app.exec_())


if __name__ == '__main__':
    main()


