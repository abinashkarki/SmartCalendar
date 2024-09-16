# Smart Calendar Management System

This project is an advanced calendar management system that helps users manage their schedules smartly and efficiently by performing various calendar operations. The system is built using FastHTML and integrates with Google for authentication.

## Features

- Retrieve calendar information
- Add new events to the calendar
- Modify existing events
- Remove events from the calendar
- Perform bulk operations on multiple events
- Intelligent handling of date and time information
- SMARTLY have it do it all for you with "smart" requests.

## Prerequisites

- Python 3.8+
- Virtual environment (optional but recommended)

## Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/abinashkarki/SmartCalendar.git
    cd smart-calendar
    ```

2. **Create and activate a virtual environment:**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```
4. **Install additional dependencies:**
    ```sh
    pip install langtrace-python-sdk
    pip install python-fasthtml
    pip install llama-index
    pip install llama-index-llms-groq
    ```

## Configuration

1. **Set up environment variables:**

    Create a `.env` file in the root directory and add the following variables:
    ```env
    GOOGLE_CLIENT_ID=your_google_client_id
    GOOGLE_CLIENT_SECRET=your_google_client_secret
    GOOGLE_REDIRECT_URI=your_google_redirect_uri
    GITHUB_CLIENT_ID=your_github_client_id
    GITHUB_CLIENT_SECRET=your_github_client_secret
    GITHUB_REDIRECT_URI=your_github_redirect_uri
    OPENAI_API_KEY=your_openai_api_key
    GROQ_API_KEY=your_groq_api_key
    ```

2. **Initialize the database:**

    The application uses an SQLite database named `calendar.db`. It will be created automatically when you run the application for the first time.

## Running the Application

1. **Start the server:**
    ```sh
    python main.py
    ```

2. **Access the application:**

    Open your web browser and navigate to `http://localhost:5000`.

## Usage

### Authentication

- **Login with Google:**
    - Navigate to the login page and click on "Login with Google".
    - Follow the prompts to authenticate with your Google account.

- **Login with GitHub:**
    - Uncomment the GitHub client initialization code in `main.py` if you want to use GitHub for authentication.
    - Navigate to the login page and click on "Login with GitHub".
    - Follow the prompts to authenticate with your GitHub account.

### Calendar Operations

- **View Events:**
    - The calendar grid displays events for the current week.
    - Hover over an event to see options to edit or delete the event.

- **Add Event:**
    - Click on the "+" button in any time slot to add a new event.
    - Fill in the event details and click "Save".

- **Edit Event:**
    - Click on the "Edit" button on an event to modify its details.
    - Update the event information and click "Save".

- **Delete Event:**
    - Click on the "Delete" button on an event to remove it from the calendar.
    - Confirm the deletion.

- **Smart Requests:**
    - Click on the "Smart Requests" button to open the smart request form.
    - Enter your request in natural language and click "Send".
    - The system will interpret your request and perform the necessary operations.

## Contributing

1. **Fork the repository:**
    - Click the "Fork" button on the top right of the repository page.

2. **Clone your fork:**
    ```sh
    git clone https://github.com/abinashkarki/SmartCalendar.git
    cd smart-calendar
    ```

3. **Create a new branch:**
    ```sh
    git checkout -b feature/your-feature-name
    ```

4. **Make your changes and commit them:**
    ```sh
    git add .
    git commit -m "Add your commit message"
    ```

5. **Push to your fork:**
    ```sh
    git push origin feature/your-feature-name
    ```

6. **Create a pull request:**
    - Go to the original repository and click on "New Pull Request".

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
