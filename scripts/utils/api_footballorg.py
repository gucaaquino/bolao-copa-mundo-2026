import requests

BASE_URL    = 'https://api.football-data.org/v4'

def api_request(url, API_TOKEN, COMPETITION):
    r = requests.get(f'{BASE_URL}/competitions/{COMPETITION}/{url}',
        headers={
            'X-Auth-Token': API_TOKEN
        },
    )
    r.raise_for_status()

    return r

def buscar_jogos_api(rodadas_filter, API_TOKEN, COMPETITION):
    r = api_request('matches', API_TOKEN, COMPETITION)
    
    jogos = [p for p in r.json()['matches'] if p['matchday'] in rodadas_filter]
    print(f"⚽ {len(jogos)} jogos encontrados")

    return jogos

def buscar_times_api(API_TOKEN, COMPETITION):
    r = api_request('teams', API_TOKEN, COMPETITION)

    times = [[aux['id'], aux['name'], aux['tla']] for aux in r.json()['teams']]
    
    print(f"⚽ {len(times)} times encontrados")

    return times