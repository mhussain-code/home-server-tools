import os
import sys
import requests

# Your anime-skip.com auth token and client ID, from environment variables
auth_token = os.environ["ANIME_SKIP_TOKEN"]
client_id = os.environ["ANIME_SKIP_CLIENT_ID"]

def fetch_time_skips(auth_token, anime_id, episode_number):
    url = "https://api.anime-skip.com/graphql"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {auth_token}',
        'X-Client-ID': client_id,  # Add the X-Client-ID header
    }

    # Construct your GraphQL query to fetch time skips
    query = f'''
    {{
      getSkipTimes(malId: "{anime_id}", episodeNumber: {episode_number}) {{
        found
        results {{
          interval {{
            startTime
            endTime
          }}
          skipType
          skipId
          episodeLength
        }}
        message
        statusCode
      }}
    }}
    '''

    data = {
        'query': query
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Request failed with status code {response.status_code}")
        print("Response content:")
        print(response.text)
        return None

# Example usage
anime_id = sys.argv[1]  # MyAnimeList ID of the show
episode_number = int(sys.argv[2])

result = fetch_time_skips(auth_token, anime_id, episode_number)

if result:
    print(result)
else:
    print("Request failed")
