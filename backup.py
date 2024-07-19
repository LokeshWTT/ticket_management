import tkinter as tk
from tkinter import ttk, messagebox
import getpass
import requests
from datetime import datetime
import textwrap


class Marquee(tk.Canvas):
    def __init__(self, parent, text, margin=2, borderwidth=1, relief='flat', fps=30):
        super().__init__(parent, borderwidth=borderwidth, relief=relief)
        self.fps = fps
        self.text_id = self.create_text(0, -1000, text=text, anchor="w", tags=("text",))
        (x0, y0, x1, y1) = self.bbox("text")
        width = (x1 - x0) + (2*margin) + (2*borderwidth)
        height = (y1 - y0) + (2*margin) + (2*borderwidth)
        self.configure(width=width, height=height)
        self.animate()

    def animate(self):
        (x0, y0, x1, y1) = self.bbox("text")
        if x1 < 0 or y0 < 0:
            x0 = self.winfo_width()
            y0 = int(self.winfo_height()/2)
            self.coords("text", x0, y0)
        else:
            self.move("text", -1, 0)
        self.after_id = self.after(int(1000/self.fps), self.animate)


class TicketSystem:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.initUI()

    def setup_window(self):
        self.root.title('Ticket System')
        self.root.protocol("WM_DELETE_WINDOW", self.disable_event)
        self.root.overrideredirect(True)
        window_width = 300
        window_height = 500
        self.root.geometry(f'{window_width}x{window_height}')
        self.root.resizable(False, False)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - window_width
        y = 0
        self.root.geometry(f'+{x}+{y}')

    def disable_event(self):
        pass

    def initUI(self):
        username = getpass.getuser()
        try:
            self.logo = tk.PhotoImage(file='wtt_logo.png').subsample(12)  # Subsample to resize the image
        except tk.TclError:
            messagebox.showerror("Error", "Logo image file not found!")
            self.logo = None

        heading_frame = ttk.Frame(self.root)
        heading_frame.pack(padx=2, pady=2, anchor=tk.W)  # Pack the heading frame with anchor=tk.W

        if self.logo:
            logo_label = ttk.Label(heading_frame, image=self.logo)
            logo_label.pack(side=tk.LEFT, padx=(2, 0))

        # Center the 'Ticket System' label within its frame
        heading_label = ttk.Label(heading_frame, text='Ticket System', font='Helvetica 12 bold')
        heading_label.pack(side=tk.LEFT, padx=30)  # Adjust padx as needed to center

        user_frame = ttk.Frame(self.root)
        user_frame.pack(padx=2, pady=2, anchor=tk.W)
        username_label = ttk.Label(user_frame, text=f'Name: {username.upper()}', font='Helvetica 10 bold')
        username_label.pack(anchor=tk.W, padx=2, pady=2)

        # Fetch incidents data
        incidents_data = self.fetch_incidents_data(username)

        # Fetch news data
        self.fetch_news()

        # Initialize news_list as an empty list
        self.news_list = []

        if incidents_data:
            open_incidents = [item for item in incidents_data if item['status'] == 'Open']
            closed_incidents = [item for item in incidents_data if item['status'] == 'Closed']

            ticket_counts_frame = ttk.Frame(self.root)
            ticket_counts_frame.pack(padx=2, pady=10)  # Increased pady for more padding

            open_frame = tk.Frame(ticket_counts_frame, borderwidth=2, relief="solid", background='#0077b6')
            open_frame.grid(row=0, column=0, padx=(0, 10), pady=2)  # Increased padx between frames
            open_tickets_label = tk.Label(open_frame, text='Open Tickets', font='Helvetica 10 bold', background='#0077b6', foreground='white')
            open_tickets_label.pack(padx=2, pady=2)
            open_tickets_num_label = tk.Label(open_frame, text=f'{len(open_incidents)}', font='Helvetica 16 bold', background='#0077b6', foreground='white')
            open_tickets_num_label.pack(padx=2, pady=2)

            closed_frame = tk.Frame(ticket_counts_frame, borderwidth=2, relief="solid", background='#0077b6')
            closed_frame.grid(row=0, column=1, padx=(10, 0), pady=2)  # Increased padx between frames
            closed_tickets_label = tk.Label(closed_frame, text='Closed Tickets', font='Helvetica 10 bold', background='#0077b6', foreground='white')
            closed_tickets_label.pack(padx=2, pady=2)
            closed_tickets_num_label = tk.Label(closed_frame, text=f'{len(closed_incidents)}', font='Helvetica 16 bold', background='#0077b6', foreground='white')
            closed_tickets_num_label.pack(padx=2, pady=2)

            table_frame = ttk.Frame(self.root)
            table_frame.pack(padx=2, pady=2, fill=tk.BOTH, expand=True)

            canvas = tk.Canvas(table_frame, width=280)  # Adjust the canvas width to 280
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=canvas.yview)
            scrollbar.pack(side=tk.LEFT, fill=tk.Y)  # Pack the scrollbar to the left

            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

            table_data_frame = tk.Frame(canvas, background='#caf0f8')  # Set the background color of the frame
            canvas.create_window((0, 0), window=table_data_frame, anchor=tk.NW)

            headers = ['Assigned Date', 'Ticket Subject', 'Assigned By']
            for col, header in enumerate(headers):
                header_frame = tk.Frame(table_data_frame, borderwidth=1, relief="solid", background='#0077b6')
                header_frame.grid(row=0, column=col, padx=2, pady=2, sticky='nsew')
                ttk.Label(header_frame, text=header, font='Helvetica 8 bold', background='#0077b6', foreground='white').pack(padx=2, pady=2)

            for row, data in enumerate(open_incidents, start=1):
                creation_date = datetime.strptime(data['creation'], '%Y-%m-%d %H:%M:%S.%f').strftime('%d-%m-%y')
                cell_frame = tk.Frame(table_data_frame, borderwidth=1, relief="solid", background='#caf0f8')
                cell_frame.grid(row=row, column=0, padx=4, pady=2, sticky='nsew')
                tk.Label(cell_frame, text=creation_date, font='Helvetica 8', background='#caf0f8').pack(padx=2, pady=2)

                wrapped_text = "\n".join(
                    textwrap.wrap(data['incident'], width=20))  # Wrap text to fit within 20 characters per line
                cell_frame = tk.Frame(table_data_frame, borderwidth=1, relief="solid", background='#caf0f8')
                cell_frame.grid(row=row, column=1, padx=4, pady=2, sticky='nsew')
                tk.Label(cell_frame, text=wrapped_text, font='Helvetica 8', anchor='w', background='#caf0f8').pack(padx=2, pady=2)

                cell_frame = tk.Frame(table_data_frame, borderwidth=1, relief="solid", background='#caf0f8')
                cell_frame.grid(row=row, column=2, padx=4, pady=2, sticky='nsew')
                tk.Label(cell_frame, text=data['employee'], font='Helvetica 8', background='#caf0f8').pack(padx=2, pady=2)

        # Display marquee below the user frame
        marquee = Marquee(self.root, text=self.news_text, borderwidth=1, relief="sunken", fps=30)
        marquee.pack(side="top", fill="x", pady=20)

    def fetch_news(self):
        try:
            api_url = 'http://10.15.5.191:5454/api/method/faq_chatgpt.news.call_news'
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json().get('data', [])
            if data:
                news_text = list(data[0].values())[0]  # Extract string content from list
                self.news_text = news_text.strip('[]').strip('"')  # Remove brackets and quotes
                print("Fetched news data:", self.news_text)  # Print fetched data
            else:
                self.news_text = "No news data found."
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Error fetching news: {str(e)}")
            self.news_text = "Error fetching news."

    def fetch_incidents_data(self, username):
        api_url = 'http://10.15.5.191:5454/api/method/faq_chatgpt.testtaskmanager.call_taskmanager'
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json().get('data', [])
            filtered_data = [item for item in data if item['employee'].lower() == username.lower() or item[
                'incident_made_by'].lower() == username.lower()]
            return filtered_data
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Error fetching data: {str(e)}")
            return []


def main():
    root = tk.Tk()
    app = TicketSystem(root)
    root.mainloop()


if __name__ == '__main__':
    main()
