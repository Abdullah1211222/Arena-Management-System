# Arena Management System

A full-stack Arena Management System developed using Python, Flask, and SQLite. The application provides a platform for managing gaming tournaments, player registrations, live matches, match highlights, and tournament advertisements.

## Features

- **User Authentication:** Login and registration functionality.
- **Role-Based Access:** Separate roles for players, league owners, and advertisers.
- **Tournament Management:** Create and manage gaming tournaments.
- **Tournament Registration:** Players can register for available tournaments.
- **Live Matches:** Dedicated pages for live matches and streaming.
- **Match Highlights:** Access match highlights.
- **Advertisement Management:** Create and manage tournament advertisements.
- **Advertisement Analytics:** View advertisement performance and analytics.
- **Database Management:** SQLite database integration.

## Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript

## Project Structure

```text
Arena Management System/
│
├── app.py
├── models.py
├── init_db.py
├── requirements.txt
├── .gitignore
│
├── static/
│   └── style.css
│
└── templates/
    ├── ads_management.html
    ├── ad_analytics.html
    ├── create_ad.html
    ├── create_tournament.html
    ├── dashboard.html
    ├── index.html
    ├── login.html
    ├── register.html
    └── tournament.html
```

## Installation and Setup

1. Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/Arena-Management-System.git
```

2. Navigate to the project directory:

```bash
cd Arena-Management-System
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set the Flask secret key.

**Windows PowerShell:**

```powershell
$env:FLASK_SECRET_KEY = "your-secret-key"
```

5. Run the application:

```bash
python app.py
```

6. Open your browser:

```text
http://127.0.0.1:5000
```

## Demo Accounts

The application includes sample accounts for testing:

| Role | Username | Password |
|---|---|---|
| Player | test | test |
| League Owner | league | test |
| Advertiser | advertiser | test |
| Player | player1 | password |

*Demo accounts are intended for local testing only.*

## Database

The application uses SQLite for storing user information, tournament details, registrations, and advertisements.

Database files are excluded from version control. The application initializes its database when required.

## Author

**Abdullah Farrukh**

- GitHub: [Abdullah1211222](https://github.com/Abdullah1211222)
- LinkedIn: [Abdullah Farrukh](https://linkedin.com/in/abdullahfarrukh1/)