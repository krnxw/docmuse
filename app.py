import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for your React frontend

# --- Spotify API Setup (Client Credentials Flow) ---
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
    print("Error: Spotify Client ID or Client Secret not found in environment variables.")
    print("Please create a .env file with SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET in your project root.")
    exit(1)

# Initialize auth_manager globally for Client Credentials Flow
auth_manager = SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
)


# --- Flask API Endpoint for Top 5 Tracks from Playlist ---
@app.route('/get_top_5_from_playlist', methods=['POST'])
def get_top_5_from_playlist_endpoint():
    try:
        # Get a fresh access token for each request
        # Explicitly setting as_dict=False to align with future behavior and suppress warning
        access_token = auth_manager.get_access_token(as_dict=False)

        if not access_token:
            print(
                "Error: Failed to obtain Spotify access token. Check your SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET in PyCharm Run Configuration (Environment Variables) or .env file.")
            return jsonify({"error": "Failed to authenticate with Spotify. Check your API credentials."}), 500

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        data = request.get_json()
        playlist_link = data.get('playlistLink')

        if not playlist_link:
            return jsonify({"error": "No playlist link provided"}), 400

        # Extract playlist ID from the link
        playlist_id_match = playlist_link.split('/')[-1].split('?')[0]
        if not playlist_id_match:
            return jsonify({"error": "Invalid Spotify playlist link format"}), 400

        playlist_id = playlist_id_match
        print(f"Extracted Playlist ID: {playlist_id}")  # Debug: Print extracted ID

        all_tracks = []
        playlist_items_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        current_url = playlist_items_url

        # Manually loop through all pages of results
        while current_url:
            # Removed 'market' parameter to broaden availability
            params = {'limit': 100}

            response = requests.get(current_url, headers=headers, params=params)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

            playlist_data = response.json()

            if 'items' in playlist_data and playlist_data['items']:
                for item in playlist_data['items']:
                    # Ensure 'track' object exists and has necessary details
                    if item and 'track' in item and item['track'] and item['track']['id']:
                        track = item['track']
                        artist_names = ", ".join(
                            [artist['name'] for artist in track['artists']]) if 'artists' in track and track[
                            'artists'] else "Unknown Artist"

                        all_tracks.append({
                            "id": track['id'],
                            "name": track['name'],
                            "artist": artist_names,
                            "popularity": track.get('popularity', 0)  # Get popularity, default to 0 if not present
                        })

            current_url = playlist_data.get('next')  # Get the URL for the next page, or None if no more pages

        if not all_tracks:
            return jsonify({"message": "No tracks found in this playlist."}), 200

        # Sort tracks by popularity in descending order
        sorted_tracks = sorted(all_tracks, key=lambda x: x['popularity'], reverse=True)

        # Get the top 5 tracks
        top_5_tracks = sorted_tracks[:5]

        # Format the output for the frontend
        formatted_top_5 = []
        for track in top_5_tracks:
            formatted_top_5.append({
                "name": track['name'],
                "artist": track['artist']
            })

        return jsonify({
            "message": "Successfully found top 5 tracks!",
            "top_tracks": formatted_top_5
        })

    except requests.exceptions.RequestException as e:
        print(f"HTTP Request Error: {e}")
        error_message = "Failed to communicate with Spotify API."
        status_code = 500
        if e.response is not None:
            status_code = e.response.status_code
            # Attempt to parse Spotify's specific error message from the response body
            try:
                error_details = e.response.json()
                if 'error' in error_details and 'message' in error_details['error']:
                    error_message = f"Spotify API Error: {error_details['error']['message']}"
                elif 'error_description' in error_details:
                    error_message = f"Spotify API Error: {error_details['error_description']}"
            except ValueError:  # Not a JSON response
                pass

            if status_code == 400:
                error_message = f"Invalid request to Spotify API. Check playlist link format. {error_message}"
            elif status_code == 403:
                error_message = f"Access to Spotify API forbidden. Check your Spotify app permissions or token. {error_message}"
            elif status_code == 404:
                error_message = f"Spotify resource not found. The playlist might be private, deleted, or the ID is incorrect. {error_message}"
            elif status_code == 429:
                error_message = f"Spotify API rate limit exceeded. Please try again later. {error_message}"
        return jsonify({"error": error_message, "details": str(e)}), status_code
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred.", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
