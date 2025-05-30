# Monuments Chatbot

A sophisticated chatbot application designed to provide information about monuments while incorporating secure user verification through email OTP. Built with Fastapi, LangGraph, and Google's Gemini AI model.

## Features

- Interactive chat interface for monument-related queries
- Email verification system with OTP
- Advanced conversation flow management using LangGraph
- Integration with Google's Gemini 2.0 Flash AI model
- Robust tracing of LLM calls for observation and evaluation using Langfuse
- Responsive web interface using Fastapi backend

## Prerequisites

- Python 3.11 or higher
- Gmail account (for sending OTP emails)
- Google API key (for Gemini AI)
- Tavily API key (for search functionality)
- Langfuse secret and public API key (for tracing and evaluation)

## Installation

1. Clone the repository:
   ```bash
   git clone <https://github.com/robotraja96/Monuments-Chat-Bot.git>
   cd monuments-chatbot
   ```

2. Create new environment in your terminal
   ```bash
   python -m venv venv
   ```

3. Activate it
   ```bash
   .\.venv\Scripts\activate
   ```

4. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up environment variables in a `.env` file:
   ```
   GOOGLE_API_KEY=your_google_api_key
   EMAIL_USER=your_gmail_address
   EMAIL_APP_PASSWORD=your_gmail_app_password
   EMAIL_SERVER=smtp.gmail.com
   EMAIL_PORT=587
   LANGFUSE_BASE_URL=langfuse_host_url
   LANGFUSE_PUBLIC_KEY=your_langfuse_public_api_key
   LANGFUSE_SECRET_KEY=your_langfuse_secret_api_key

   ```

## Configuration

1. Gmail Setup for OTP:
   - Enable 2-factor authentication in your Gmail account
   - Generate an App Password for the application
   - Use the generated App Password in your `.env` file

2. API Keys:
   - Obtain a Google API key for Gemini AI
   - Set up a Tavily account and generate an API key
   - Set up Langfuse account, set up a project for your organization and generate the required API keys. Also copy the base url
   - Set up necessary API keys in the `.env` file

## Running the Application

1. Start the fastapi server:
   i) Shift to the src folder
   ```bash
   cd src
   ```
   ii) Start the server
   ```bash
   fastapi dev app.py
   ```

2. Access the application:
   - Open your web browser
   - Navigate to `http://127.0.0.1:8000`

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
monuments-chat-bot/
├── src/
│   ├── static/
│   │   ├── script.js
│   │   └── styles.css
│   ├── templates/
│   │   └── chatbox.html
│   ├── app.py              # Main application file
│   ├── graph.py            # Defines the langraph architecture of our agent
│   ├── prompts.py          # Stores prompt definitions
│   ├── session_manager.py  # Manages user sessions
│   └── utils.py            # Utility functions
├── .env                    # Environment variables (create this)
├── pyproject.toml          # Project metadata and dependencies (if using UV)
├── README.md               
└── requirements.txt        # Python dependencies
```

## Tech Stack

- **Backend Framework**: Fastapi
- **AI/ML**: 
  - Google Gemini 2.0 Flash
  - LangGraph for conversation flow
  - LangChain for AI interactions
- **Frontend**: HTML, JavaScript, CSS
- **External Services**:
  - Tavily Search API for real-time information
  - SMTP for email services




## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


## Support

For support, please check out my [linkedin](https://www.linkedin.com/in/raja-raman-173a082a1/), [WordPress](https://thevicariousview.wordpress.com/),[Substack](https://substack.com/@vicariousviews)