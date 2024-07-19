import sys
import getpass
import requests
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QFrame
from PyQt5.QtCore import QUrl, Qt, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView
import json
import time


class TicketSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.fetch_initial_data()

    def initUI(self):
        self.setup_window()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        self.username_label = QLabel()

        # Boxes for open and closed counts
        self.open_box = self.create_info_box("Open")
        self.closed_box = self.create_info_box("Closed")

        # Web view for incidents and news
        self.webview = QWebEngineView()
        layout.addWidget(self.webview)

        # Timer for periodic updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(60000)  # 10 seconds interval

    def setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint)  # Remove title bar and window controls
        self.setGeometry(100, 100, 310, 450)
        self.root = QWidget()
        self.setCentralWidget(self.root)
        self.root.setStyleSheet("background-color: white;")

    def fetch_initial_data(self):
        username = getpass.getuser()
        self.username_label.setText(f"Name: {username.upper()}")

        # Fetch user email and add a delay
        email = self.fetch_user_email(username)
        if email:
            print(f"Email for username '{username}': {email}")
        else:
            print(f"No email found for username '{username}'.")
        time.sleep(1)  # Add delay

        # Fetch user info and add a delay
        user_id, name = self.fetch_user_info(email)
        if user_id and name:
            print(f"User ID: {user_id}, Name: {name}")
        else:
            print(f"No user info found for email '{email}'.")
        time.sleep(1)  # Add delay

        # Fetch incidents data and add a delay
        incidents_data = self.fetch_incidents_data(name)
        open_count = sum(1 for incident in incidents_data if incident.get('status') == 'Open')
        close_count = sum(1 for incident in incidents_data if incident.get('status') == 'Closed')
        time.sleep(1)  #Add_delay

        # Fetch news and add a delay
        news_text = self.fetch_news()
        time.sleep(1)  #Add_delay

        # Update the UI
        self.update_ui(open_count, close_count, incidents_data, news_text)

    def update_data(self):
        username = getpass.getuser()
        email = self.fetch_user_email(username)
        user_id, name = self.fetch_user_info(email)
        incidents_data = self.fetch_incidents_data(name)
        open_count = sum(1 for incident in incidents_data if incident.get('status') == 'Open')
        close_count = sum(1 for incident in incidents_data if incident.get('status') == 'Closed')
        news_text = self.fetch_news()

        self.update_ui(open_count, close_count, incidents_data, news_text)

    def update_ui(self, open_count, close_count, incidents_data, news_text):
        self.open_box['count_label'].setText(str(open_count))
        self.closed_box['count_label'].setText(str(close_count))

        # Prepare HTML content
        html_content = self.generate_html(incidents_data, news_text)

        # Load HTML content into QWebEngineView
        self.webview.setHtml(html_content, QUrl(''))

    def generate_html(self, incidents_data, news_text):
        username = getpass.getuser()
        open_incidents = [incident for incident in incidents_data if incident.get('status') == 'Open']
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <!-- Bootstrap CSS -->
            <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
            <title>Ticket Management System</title>
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
                    font-size: 14px;
                    color: #495057;
                }}

                .box p {{
                    font-size: 18px;
                    color: #343a40;
                    margin: 0;
                }}

                .table {{
                    width: 100%;
                    margin-top: 5px;
                    margin-bottom: 5px;
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
                    background-color: #007bff;
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
                    margin-bottom: 5px;
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
                    width: 30%; /* Adjust width of the Subject column */
                }}

                .table th:nth-child(3),
                .table td:nth-child(3) {{
                    width: 45%; /* Adjust width of the Employee column */
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
            </style>
        </head>
        <body>
            <div class="container">
                <div class="heading" style="display: flex; align-items: center; justify-content: center;">
                    <img src="https://res.cloudinary.com/wtt-international/image/upload/v1665033178/WTT/ewlpcq8snvn1bbewif8r.png" alt="WTT Logo" class="logo-img" style="height: 30px; width: auto;">
                    <div style="text-align: center; flex-grow: 1;">
                         <h2 style="font-size: 16px; margin-left: -15px;">Ticket System</h2>
                    </div>
                </div>

  <h3 style="font-size: 16px; margin-top: 10px;">Name: {username}</h3> <!-- Display system username -->

                <div class="box">
                    <h3>Open</h3>
                    <p>{len(open_incidents)} </p>
                </div>
                <div class="box">
                    <h3>Closed</h3>
                    <p>{len([incident for incident in incidents_data if incident.get('status') == 'Closed'])}</p>
                </div>

                <div class="table-responsive">
                    <table class="table table-bordered">
                        <thead class="thead-dark">
                            <tr>
                                <th style="font-size: 10px;">Date</th>
                                <th style="font-size: 10px;">Assigned By</th>
                                <th style="font-size: 10px;">Subject</th>
                            </tr>
                        </thead>
                        <tbody id="incidentsTableBody">
                            {self.generate_incidents_table(open_incidents)}
                        </tbody>
                    </table>
                </div>

                <div id="news" class="alert alert-info" role="alert">
                    <div class="marquee">
                        {news_text} <!-- News text will be dynamically updated here -->
                    </div>
                </div>
            </div>

            <!-- Bootstrap JS and jQuery (optional for Bootstrap components) -->
            <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
            <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>

            <!-- Custom JavaScript for dynamic updates -->
            <script>
                function updateIncidents(incidentsData) {{
                    var tableBody = document.getElementById("incidentsTableBody");
                    tableBody.innerHTML = "";  // Clear previous data
                    incidentsData.forEach(function(data) {{
                        var row = tableBody.insertRow();
                        var cell1 = row.insertCell(0);
                        var cell2 = row.insertCell(1);
                        var cell3 = row.insertCell(2);
                        cell1.innerHTML = data.creation;
                        cell2.innerHTML = data.employee;
                        cell3.innerHTML = '<a href="http://10.15.5.191:5454/app/tickets/' + encodeURIComponent(data.ticket_no) + '">' + data.incident + '</a>';
                    }});
                }}

                function updateNews(newsText) {{
                    document.querySelector(".marquee").innerText = newsText;
                }}
            </script>

            <!-- Initialize with fetched data -->
            <script>
                var incidentsData = {json.dumps(open_incidents)};
                var newsText = "{news_text}";

                updateIncidents(incidentsData);
                updateNews(newsText);
            </script>

        </body>
        </html>
        """
        return html_content

    def generate_incidents_table(self, incidents):
        table_rows = ""
        for incident in incidents:
            table_rows += f"""
            <tr>
                <td>{incident['creation']}</td>
                <td>{incident['employee']}</td>
                <td><a href="http://10.15.5.191:5454/app/tickets/{incident['ticket_no']}">{incident['incident']}</a></td>
            </tr>
            """
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
        time.sleep(0)  # Add delay
        try:
            api_url = 'http://10.15.5.191:5454/api/method/faq_chatgpt.user_names.get_user_ticket_username'
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json().get('data', [])

            for user_data in data:
                if user_data.get('ticket_username') == username:
                    return user_data.get('email')
            return None  # If no matching email found
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user email: {str(e)}")
            return None

    def fetch_user_info(self, email):
        time.sleep(0)  # Add delay
        try:
            api_url = 'http://10.15.5.191:5454/api/method/faq_chatgpt.employee.get_username'
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json().get('data', [])

            for user_data in data:
                if user_data.get('user_id') == email:
                    return user_data.get('user_id'), user_data.get('name')
            return None, None  # If no matching user info found
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user info: {str(e)}")
            return None, None

    def fetch_incidents_data(self, name):
        time.sleep(0)  # Add delay
        try:
            api_url = 'http://10.15.5.191:5454/api/method/faq_chatgpt.testtaskmanager.call_taskmanager'
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json().get('data', [])

            # Filter and format data based on name matching incident_made_by
            filtered_data = []
            for item in data:
                if item.get('incident_made_by', '').lower() == name.lower():  # Case-insensitive comparison
                    creation_date = datetime.strptime(item['creation'], '%Y-%m-%d %H:%M:%S.%f')
                    formatted_creation_date = creation_date.strftime('%d-%m-%y')
                    filtered_data.append({
                        'creation': formatted_creation_date,
                        'incident': item['incident'],
                        'employee': item['employee'],
                        'status': item.get('status', 'Unknown'),
                        'ticket_no': item.get('name')
                    })

            return filtered_data

        except requests.exceptions.RequestException as e:
            print(f"Error fetching incidents data: {str(e)}")
            return []

    def fetch_news(self):
        try:
            api_url = 'http://10.15.5.191:5454/api/method/faq_chatgpt.news.call_news'
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json().get('data', [])
            if data:
                return list(data[0].values())[0]
            else:
                return "No news data found."
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news: {str(e)}")
            return "Error fetching news."


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = TicketSystem()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
