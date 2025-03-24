# Monuments Chatbot

A sophisticated chatbot application designed to provide information about monuments while incorporating secure user verification through email OTP. Built with Flask, LangGraph, and Google's Gemini AI model.

## Features

- Interactive chat interface for monument-related queries
- Email verification system with OTP
- Advanced conversation flow management using LangGraph
- Integration with Google's Gemini 2.0 Flash AI model
- Secure session management
- Responsive web interface

## Prerequisites

- Python 3.8 or higher
- Gmail account (for sending OTP emails)
- Google API key (for Gemini AI)
- Tavily API key (for search functionality)

## Installation

1. Clone the repository:
   ```bash
   git clone <https://github.com/robotraja96/Monuments-Chat-Bot.git>
   cd monuments-chatbot
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in a `.env` file:
   ```
   GOOGLE_API_KEY=your_google_api_key
   EMAIL_USER=your_gmail_address
   EMAIL_APP_PASSWORD=your_gmail_app_password
   EMAIL_SERVER=smtp.gmail.com
   EMAIL_PORT=587
   ```

## Configuration

1. Gmail Setup for OTP:
   - Enable 2-factor authentication in your Gmail account
   - Generate an App Password for the application
   - Use the generated App Password in your `.env` file

2. API Keys:
   - Obtain a Google API key for Gemini AI
   - Set up necessary API keys in the `.env` file

## Running the Application

1. Start the Flask server:
   ```bash
   python app.py
   ```

2. Access the application:
   - Open your web browser
   - Navigate to `http://localhost:5000`

## Usage

1. **Starting a Chat**:
   - Open the web interface
   - Start asking questions about monuments

2. **User Verification**:
   - When prompted, provide your email address
   - Check your email for the OTP
   - Enter the OTP in the chat interface
   - Continue with verified access

3. **Chat Features**:
   - Ask questions about monuments
   - Get detailed information and historical facts
   - Real-time search integration for up-to-date information

## Project Structure

```
monuments-chatbot/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── templates/         
│   └── index.html     # Frontend template
└── .env               # Environment variables (create this)
```

## Tech Stack

- **Backend Framework**: Flask
- **AI/ML**: 
  - Google Gemini 2.0 Flash
  - LangGraph for conversation flow
  - LangChain for AI interactions
- **Frontend**: HTML, JavaScript
- **External Services**:
  - Tavily Search API for real-time information
  - SMTP for email services
- **Security**: Session-based authentication with email OTP

## Security Features

- Email verification with OTP
- Session management
- Secure credential handling
- Environment variable protection

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


## Support

For support, please check out my [linkedin](https://www.linkedin.com/in/raja-raman-173a082a1/), [WordPress](https://thevicariousview.wordpress.com/),[Substack](https://substack.com/@vicariousviews)