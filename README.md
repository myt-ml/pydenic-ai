# Arabic AI Agent

A simple conversational AI agent built with [Pydantic AI](https://ai.pydantic.dev/) and [Gradio](https://www.gradio.app/).

## Features

- **Model**: Uses OpenAI's `gpt-4o-mini`.
- **Language**: Responds exclusively in Modern Standard Arabic (Standard Arabic).
- **Style**: Short, concise, and direct answers.
- **Interface**: Clean web interface powered by Gradio.

## Prerequisites

- Python 3.10+
- OpenAI API Key

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/myt-ml/pydenic-ai.git
    cd pydenic-ai
    ```

2.  **Create and activate a virtual environment**:
    - macOS/Linux:
      ```bash
      python3 -m venv venv
      source venv/bin/activate
      ```
    - Windows (PowerShell):
      ```powershell
      python -m venv venv
      .\venv\Scripts\activate
      ```

3.  **Install Dependencies**:
    ```bash
    pip install pydantic-ai[logfire] gradio python-dotenv
    ```

## Configuration

1.  Create a `.env` file in the project root.
2.  Add your OpenAI API Key:
    ```env
    OPENAI_API_KEY=sk-your-api-key-here
    ```

## Usage

Run the application:

```bash
python app.py
```

Open your browser and navigate to the URL shown (usually `http://127.0.0.1:7860`).

## Example Queries

- **Greeting**: "مرحبا" (Hello)
- **Question**: "ما هي عاصمة مصر؟" (What is the capital of Egypt?)
