import React, { useState } from 'react';

// Main App component
const App = () => {
  const [playlistLink, setPlaylistLink] = useState('');
  const [topTracksResults, setTopTracksResults] = useState(null); // Renamed from analysisResults
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const pythonBackendBaseUrl = 'http://127.0.0.1:5000';

  // Regex to validate Spotify playlist URLs
  const spotifyPlaylistRegex = /^(https?:\/\/)?(www\.)?open\.spotify\.com\/playlist\/[a-zA-Z0-9]+(\?si=[a-zA-Z0-9]+)?$/;

  // Function to handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); // Clear previous errors
    setTopTracksResults(null); // Clear previous results

    if (!spotifyPlaylistRegex.test(playlistLink)) {
      setError('Please enter a valid Spotify playlist URL.');
      return;
    }

    setLoading(true); // Start loading state

    try {
      const response = await fetch(`${pythonBackendBaseUrl}/get_top_5_from_playlist`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ playlistLink }),
      });

      if (!response.ok) {
        let errorMessage = `HTTP error! Status: ${response.status}.`;
        try {
          const errorData = await response.json();
          if (errorData.error) {
            errorMessage += ` Details: ${errorData.error}`;
          }
        } catch (jsonError) {
          errorMessage += ` (Could not parse error details from backend)`;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setTopTracksResults(data); // Set the top tracks results
    } catch (err) {
      console.error('Error fetching top tracks:', err);
      setError(`Failed to analyze playlist: ${err.message}. Please ensure the playlist is public.`);
    } finally {
      setLoading(false); // End loading state
    }
  };

  return (
    <div className="min-h-screen bg-white bg-capacity-30 flex items-center justify-center p-4 font-inter">
      <div className="bg-white bg-opacity-10 backdrop-filter backdrop-blur-lg border border-gray-700 rounded-xl shadow-2xl p-8 max-w-lg w-full text-black">
        <h1 className="text-4xl font-bold text-center mb-6 text-black">
          Spotify Top 5 Playlist Tracks Analyzer
        </h1>
        <p className="text-center text-black mb-8">
          Enter a public Spotify playlist link to find its top 5 most listened tracks.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="flex flex-col items-center w-full">
            <label htmlFor="playlistLink" className="block text-lg font-medium text-gray-200 mb-2 text-center">
              Spotify Playlist Link:
            </label>
            <input
              type="text"
              id="playlistLink"
              value={playlistLink}
              onChange={(e) => setPlaylistLink(e.target.value)}
              placeholder="e.g., https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
              className="w-full px-4 py-3 rounded-lg bg-white bg-opacity-50 border border-gray-600 focus:border-purple-500 focus:ring focus:ring-purple-500 focus:ring-opacity-50 text-white placeholder-gray-400 text-base text-center"
              required
            />
          </div>

          {error && (
            <p className="text-red-400 text-sm text-center">{error}</p>
          )}

          <button
            type="submit"
            className="w-full bg-purple-600 hover:bg-purple-s200 text-white font-bold py-3 px-6 rounded-lg transition duration-300 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-75 disabled:opacity-50 disabled:cursor-not-allowed text-lg"
            disabled={loading}
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <svg className="animate-spin h-5 w-5 mr-3 text-white" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Analyzing Playlist...
              </div>
            ) : (
              'Find Top 5 Tracks'
            )}
          </button>
        </form>

        {topTracksResults && (
          <div className="mt-8 pt-6 border-t border-gray-700 text-center">
            <h2 className="text-3xl font-bold text-black mb-4">Top 5 Tracks</h2>
            {topTracksResults.top_tracks && topTracksResults.top_tracks.length > 0 ? (
              <ol className="list-decimal list-inside text-left text-gray-200 max-h-60 overflow-y-auto custom-scrollbar">
                {topTracksResults.top_tracks.map((track, index) => (
                  <li key={index} className="mb-1 text-base">
                    <span className="font-semibold">{track.name}</span> by {track.artist}
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-lg text-gray-300 italic">
                {topTracksResults.message || "No top tracks found."}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
