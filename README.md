
<img width="612" alt="Screenshot 2024-09-25 at 3 06 21 PM" src="https://github.com/user-attachments/assets/adf9e8b0-15e1-43fd-8eb1-bdb94165ed22">

# ElevenLabs Video Dubbing Application

## Description

The ElevenLabs Video Dubbing Application is a user-friendly interface for dubbing videos using the ElevenLabs API. This application allows users to upload video files or provide URLs to videos (from platforms like YouTube, TikTok, Twitter, or Vimeo) and dub them into various languages. The application uses Gradio to provide an easy-to-use web interface.

Key features:
- Support for both file uploads and video URLs
- Multiple language options for source and target languages
- Custom output directory selection
- Real-time progress updates during the dubbing process

## Setup

### Prerequisites

- Python 3.7 or higher
- An ElevenLabs API key

### Installation

1. Clone this repository or download the `dub.py` file.

2. Install the required Python packages:
   ```
   pip install elevenlabs gradio python-dotenv
   ```

3. Create a `.env` file in the same directory as `dub.py` and add your ElevenLabs API key:
   ```
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ```

## Usage

1. Run the application:
   ```
   python dub.py
   ```

2. Open the provided local URL in your web browser.

3. Choose either the "File Upload" or "URL Input" tab:

   - For File Upload:
     a. Upload a video file
     b. Select the source language
     c. Choose the target language for dubbing
     d. Specify an output directory (default is "output")
     e. Click "Dub Video File"

   - For URL Input:
     a. Enter the URL of the video
     b. Select the source language
     c. Choose the target language for dubbing
     d. Specify an output directory (default is "output")
     e. Click "Dub Video from URL"

4. Wait for the dubbing process to complete. You'll see progress updates in the interface.

5. Once completed, the application will provide the path to the dubbed video file.

## Supported Languages

The application supports dubbing between various languages, including but not limited to:
English, Hindi, Portuguese, Chinese, Spanish, French, German, Japanese, Arabic, Russian, Korean, Indonesian, Italian, Dutch, Turkish, Polish, Swedish, Filipino, Malay, Romanian, Ukrainian, Greek, Czech, Danish, Finnish, Bulgarian, Croatian, Slovak, and Tamil.

## Troubleshooting

- If you encounter any errors, check the console output for detailed error messages.
- Ensure your ElevenLabs API key is correct and has the necessary permissions.
- For issues with file permissions when saving the output, make sure the application has write access to the specified output directory.

## Limitations

- The dubbing process may take some time, especially for longer videos.
- The quality of dubbing depends on the ElevenLabs API and may vary based on the complexity of the video and languages involved.


