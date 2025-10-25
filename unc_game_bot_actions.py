"""
UNC Tar Heels Game Thread Bot - GitHub Actions Version
Runs on GitHub's servers every 5 minutes automatically
"""

import praw
import requests
import json
import os
from datetime import datetime, timedelta
import pytz

# Get credentials from environment variables (set in GitHub Secrets)
REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')
REDDIT_USERNAME = os.environ.get('REDDIT_USERNAME')
REDDIT_PASSWORD = os.environ.get('REDDIT_PASSWORD')
SUBREDDIT_NAME = os.environ.get('SUBREDDIT_NAME', 'tarheels')

UNC_TEAM_ID = "153"
PREGAME_HOURS = 3

# File to track posted threads (persists between runs)
STATE_FILE = "bot_state.json"

def load_state():
    """Load bot state from file"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {'posted_threads': {}, 'active_games': {}}

def save_state(state):
    """Save bot state to file"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_reddit_client():
    """Initialize Reddit client"""
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD,
        user_agent=f"UNC Game Thread Bot v2.0 (GitHub Actions) by /u/{REDDIT_USERNAME}"
    )

def get_game_details(game_id, sport):
    """Fetch detailed game information"""
    if sport == 'basketball':
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={game_id}"
    else:
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event={game_id}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching game {game_id}: {e}")
        return None

def format_pregame_thread(game_data, sport):
    """Create pre-game thread"""
    header = game_data.get('header', {})
    competitions = header.get('competitions', [{}])[0]
    competitors = competitions.get('competitors', [])
    
    home_team = next((t for t in competitors if t.get('homeAway') == 'home'), {})
    away_team = next((t for t in competitors if t.get('homeAway') == 'away'), {})
    
    home_name = home_team.get('team', {}).get('displayName', 'Home')
    away_name = away_team.get('team', {}).get('displayName', 'Away')
    home_record = home_team.get('records', [{}])[0].get('summary', 'N/A')
    away_record = away_team.get('records', [{}])[0].get('summary', 'N/A')
    
    game_time = competitions.get('date', '')
    venue = competitions.get('venue', {}).get('fullName', 'TBA')
    broadcast = competitions.get('broadcasts', [{}])[0].get('names', ['TBA'])[0] if competitions.get('broadcasts') else 'TBA'
    
    if game_time:
        dt = datetime.strptime(game_time, '%Y-%m-%dT%H:%M%SZ')
        dt = dt.replace(tzinfo=pytz.UTC)
        et = pytz.timezone('US/Eastern')
        dt_et = dt.astimezone(et)
        game_time_str = dt_et.strftime('%I:%M %p ET')
    else:
        game_time_str = 'TBA'
    
    sport_emoji = "🏀" if sport == "basketball" else "🏈"
    title = f"[Pre-Game Thread] {away_name} @ {home_name}"
    
    body = f"""# {sport_emoji} {away_name} @ {home_name}

**Game Info**

* **Time:** {game_time_str}
* **Location:** {venue}
* **TV:** {broadcast}

---

**Team Stats**

| Team | Record |
|------|--------|
| {away_name} | {away_record} |
| {home_name} | {home_record} |

---

**Go Heels!** 🐏

*This thread was automatically created by the /r/{SUBREDDIT_NAME} bot*
"""
    return title, body

def format_game_thread(game_data, sport):
    """Create/update game thread"""
    header = game_data.get('header', {})
    competitions = header.get('competitions', [{}])[0]
    competitors = competitions.get('competitors', [])
    
    home_team = next((t for t in competitors if t.get('homeAway') == 'home'), {})
    away_team = next((t for t in competitors if t.get('homeAway') == 'away'), {})
    
    home_name = home_team.get('team', {}).get('displayName', 'Home')
    away_name = away_team.get('team', {}).get('displayName', 'Away')
    home_score = home_team.get('score', '0')
    away_score = away_team.get('score', '0')
    
    status = competitions.get('status', {})
    game_status = status.get('type', {}).get('shortDetail', 'In Progress')
    
    sport_emoji = "🏀" if sport == "basketball" else "🏈"
    title = f"[Game Thread] {away_name} @ {home_name}"
    
    linescore = f"""**Score**

| Team | Total |
|------|-------|
| {away_name} | **{away_score}** |
| {home_name} | **{home_score}** |

**{game_status}**
"""
    
    body = f"""# {sport_emoji} {away_name} @ {home_name}

{linescore}

---

**Thread Notes:**

* Discuss whatever you wish. Keep it civil.
* Try [Chrome Refresh](https://chrome.google.com/webstore/detail/easy-auto-refresh/aabcgdmkeabbnleenpncegpcngjpnjkc) or Firefox's [ReloadEvery](https://addons.mozilla.org/en-US/firefox/addon/reloadevery/) to auto-refresh.
* Follow [@TarHeelBlog](https://twitter.com/tarheelblog) on Twitter.

---

**Go Heels!** 🐏

*Last updated: {datetime.now(pytz.timezone('US/Eastern')).strftime('%I:%M:%S %p ET')}*
"""
    return title, body

def format_postgame_thread(game_data, sport):
    """Create post-game thread"""
    header = game_data.get('header', {})
    competitions = header.get('competitions', [{}])[0]
    competitors = competitions.get('competitors', [])
    
    home_team = next((t for t in competitors if t.get('homeAway') == 'home'), {})
    away_team = next((t for t in competitors if t.get('homeAway') == 'away'), {})
    
    home_name = home_team.get('team', {}).get('displayName', 'Home')
    away_name = away_team.get('team', {}).get('displayName', 'Away')
    home_score = int(home_team.get('score', '0'))
    away_score = int(away_team.get('score', '0'))
    
    if home_score > away_score:
        winner, loser = home_name, away_name
        winner_score, loser_score = home_score, away_score
    else:
        winner, loser = away_name, home_name
        winner_score, loser_score = away_score, home_score
    
    sport_emoji = "🏀" if sport == "basketball" else "🏈"
    title = f"[Post-Game Thread] {winner} defeats {loser}, {winner_score}-{loser_score}"
    
    body = f"""# {sport_emoji} {winner} defeats {loser}

## Final Score: {winner} {winner_score}, {loser} {loser_score}

---

**Box Score:** [ESPN](http://www.espn.com/college-{sport}/game?gameId={header.get('id', '')})

---

**Go Heels!** 🐏

*This thread was automatically created by the /r/{SUBREDDIT_NAME} bot*
"""
    return title, body

def should_post_pregame(game_time, state, thread_key):
    """Check if pre-game thread should be posted"""
    if thread_key in state['posted_threads'].get('pregame', {}):
        return False
    
    now = datetime.now(pytz.UTC)
    pregame_time = game_time - timedelta(hours=PREGAME_HOURS)
    return now >= pregame_time and now < game_time

def is_game_live(status):
    """Check if game is in progress"""
    state = status.get('type', {}).get('state', '')
    return state in ['in', 'pre']

def is_game_final(status):
    """Check if game is finished"""
    state = status.get('type', {}).get('state', '')
    return state == 'post'

def get_unc_schedule(sport):
    """Get UNC schedule for a sport"""
    if sport == 'basketball':
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/{UNC_TEAM_ID}/schedule"
    else:
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{UNC_TEAM_ID}/schedule"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {sport} schedule: {e}")
        return None

def run_bot():
    """Main bot execution - runs once"""
    print(f"🚀 UNC Game Thread Bot starting...")
    print(f"📅 {datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %I:%M:%S %p ET')}")
    
    # Load state
    state = load_state()
    if 'posted_threads' not in state:
        state['posted_threads'] = {}
    if 'active_games' not in state:
        state['active_games'] = {}
    
    # Initialize Reddit
    reddit = get_reddit_client()
    subreddit = reddit.subreddit(SUBREDDIT_NAME)
    
    # Check both sports
    for sport in ['basketball', 'football']:
        print(f"\n🔍 Checking {sport}...")
        
        schedule = get_unc_schedule(sport)
        if not schedule:
            continue
        
        events = schedule.get('events', [])
        print(f"   Found {len(events)} games")
        
        for event in events:
            game_id = event.get('id')
            if not game_id:
                continue
            
            # Get detailed game data
            game_data = get_game_details(game_id, sport)
            if not game_data:
                continue
            
            competition = game_data.get('header', {}).get('competitions', [{}])[0]
            status = competition.get('status', {})
            game_date_str = competition.get('date', '')
            
            if not game_date_str:
                continue
            
            game_time = datetime.strptime(game_date_str, '%Y-%m-%dT%H:%M%SZ')
            game_time = game_time.replace(tzinfo=pytz.UTC)
            
            thread_key = f"{sport}_{game_id}"
            
            # Check for pre-game thread
            if should_post_pregame(game_time, state, thread_key):
                print(f"📝 Posting pre-game thread for game {game_id}")
                title, body = format_pregame_thread(game_data, sport)
                submission = subreddit.submit(title, selftext=body)
                
                if 'pregame' not in state['posted_threads']:
                    state['posted_threads']['pregame'] = {}
                state['posted_threads']['pregame'][thread_key] = submission.id
                print(f"✅ Posted: {submission.shortlink}")
            
            # Check for game thread
            if is_game_live(status):
                if thread_key not in state['active_games']:
                    print(f"🏁 Posting game thread for game {game_id}")
                    title, body = format_game_thread(game_data, sport)
                    submission = subreddit.submit(title, selftext=body)
                    
                    state['active_games'][thread_key] = submission.id
                    
                    try:
                        submission.mod.sticky()
                        print(f"📌 Stickied thread")
                    except:
                        pass
                    
                    print(f"✅ Posted: {submission.shortlink}")
                else:
                    # Update existing thread
                    print(f"🔄 Updating game thread for game {game_id}")
                    submission_id = state['active_games'][thread_key]
                    title, body = format_game_thread(game_data, sport)
                    submission = reddit.submission(id=submission_id)
                    submission.edit(body)
                    print(f"✅ Updated")
            
            # Check for post-game thread
            if is_game_final(status):
                if thread_key in state['active_games']:
                    print(f"🏆 Posting post-game thread for game {game_id}")
                    title, body = format_postgame_thread(game_data, sport)
                    submission = subreddit.submit(title, selftext=body)
                    
                    try:
                        game_thread = reddit.submission(id=state['active_games'][thread_key])
                        game_thread.mod.sticky(state=False)
                        submission.mod.sticky()
                    except:
                        pass
                    
                    del state['active_games'][thread_key]
                    print(f"✅ Posted: {submission.shortlink}")
    
    # Save state
    save_state(state)
    print(f"\n✨ Run complete!")

if __name__ == "__main__":
    run_bot()
