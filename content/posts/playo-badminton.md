+++
title = "Automating Badminton Game Alerts"
date = 2025-03-04T00:10:55+05:30
type = "post"
description = "Vibe coding a script to automatically notify me about available badminton games on PlayO before they get fully booked."
in_search_index = true
[taxonomies]
tags= ["Python"]
[extra]
og_preview_img = "/images/badminton-header.webp"
+++

I've been playing badminton more regularly since the start of 2025 - almost 4-5 days a week. I recently moved to a new part of the city, which meant I couldn't play with my old friends anymore. [PlayO](https://playo.co/) has been super helpful for finding games with new people. On PlayO, a host creates a game and up to 6 people can join one court for a one-hour badminton doubles session.

However, on hectic days I would often forget to check for badminton games, only to find them fully booked later. I wanted to automate this process by creating a small script that would send me scheduled alerts about today's game availability, allowing me to book slots before they filled up. I drew inspiration from [Matt's](https://mattrighetti.com/2025/03/03/reverse-engineering-playtomic) post where he did something similar.

Thankfully, PlayO has a public API endpoint to retrieve a list of available games: `https://api.playo.io/activity-public/list/location`.

You can send a `POST` request to this URL with these parameters for filtering:

```json
{
  "lat": 12.9783692,
  "lng": 77.6408356,
  "cityRadius": 5,
  "gameTimeActivities": false,
  "page": 0,
  "lastId": "",
  "sportId": ["SP5"],
  "booking": false,
  "date": ["2025-03-04T11:03:17.260Z"]
}
```

It returns a list of activities matching these filters. One such activity looks like:

```json
{
  "userInfo": [
    {
      "profilePicUrl": "https://playov2.gumlet.io/profiles/redacted.511716.jpg",
      "fName": "Redacted",
      "lName": "",
      "karma": 2800
    },
    {
      "profilePicUrl": "https://playov2.gumlet.io/profiles/redacted-redacted.png",
      "fName": "redacted",
      "lName": "N",
      "karma": 499
    }
  ],
  "isPlayoGame": false,
  "skill": "Intermediate & above",
  "sportName": "Badminton",
  "shortListed": false,
  "joineeList": [
    "7f3cf298-3324-4fc2-96ad-b0f00093cd8f",
    "250572a2-555d-4a77-94f0-452142c08f81",
    "cc3b9eb6-a3b5-4c26-8605-0486fa000a4b",
    "8d5d4299-950b-4011-a7ac-b466b1c00e84",
    "235ae56d-6f4f-4106-9304-fb38e7d4add8"
  ],
  "isPlaypalPlaying": false,
  "lat": 12.976394040119704,
  "lng": 77.63644146986815,
  "location": "Game Theory - Double Road Indiranagar, Indiranagar",
  "joineeCount": 6,
  "status": -1,
  "sportsPlayingMode": {
    "name": "",
    "icon": ""
  },
  "maxPlayers": 7,
  "full": false,
  "price": 0,
  "startTime": "2025-03-04T13:30:00.000Z",
  "endTime": "2025-03-04T15:30:00.000Z",
  "minSkill": 3,
  "maxSkill": 5,
  "skillSet": true,
  "booking": false,
  "bookingId": "",
  "type": 0,
  "venueId": "82af038f-058c-4b2f-bc3d-3a47910d4f97",
  "venueName": "Game Theory - Double Road Indiranagar, Indiranagar",
  "activityType": "regular",
  "isOnline": false,
  "groupId": "",
  "groupName": "",
  "currencyTxt": "INR",
  "strictSkill": true,
  "date": "2025-03-04T00:00:00.000Z",
  "hostId": "redacted",
  "sportId": "SP5",
  "timing": 2,
  "id": "e2ee9f62-c9b6-472b-aea2-b0c52dd7c525",
  "distance": 0.5249236963063415,
  "courtInfo": "",
  "sponsored": false,
  "groups": []
}
```

Using the above response, I filtered for games where:

- `full` is `false` (This indicates that `joineeCount == maxPlayer` is not true, meaning spots are still available to join)
- `startTime` and `endTime` fall within 7-8PM IST

I also wanted to add a feature to send these details to Telegram for convenient notifications. I then [vibe coded](https://x.com/karpathy/status/1886192184808149383) with Claude 3.7 to create a Python script to automate this whole process. Impressively, it produced a working script pretty much in a one-shot prompt, though I had to make a few minor tweaks. I quite like [Simon Willison's approach](https://simonwillison.net/2024/Dec/19/one-shot-python-tools/) of using `uv` to build one-shot tools. Managing dependencies, virtual environments, etc. is still a pain point in Python, but using `uv` feels like magic by comparison.

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click",
#     "requests",
#     "pytz",
#     "rich",
#     "python-dateutil",
#     "python-telegram-bot",
# ]
# ///

import click
import requests
import json
import datetime
import pytz
import os
import sys
from rich.console import Console
from rich.table import Table
from dateutil import parser
from telegram import Bot, InputMediaPhoto
from telegram.constants import ParseMode
from io import BytesIO
import asyncio

console = Console()

@click.command()
@click.option("--lat", default=12.9783692, help="Latitude for search")
@click.option("--lng", default=77.6408356, help="Longitude for search")
@click.option("--radius", default=50, help="City radius in km")
@click.option("--sport", default="SP5", help="Sport ID (default: SP5 for Badminton)")
@click.option("--start-time", default="19:00", help="Desired start time (24-hour format HH:MM)")
@click.option("--end-time", default="20:00", help="Desired end time (24-hour format HH:MM)")
@click.option("--timezone", default="Asia/Kolkata", help="Your timezone")
@click.option("--verbose", is_flag=True, help="Show detailed information including exact UTC/IST times")
@click.option("--include-full", is_flag=True, help="Include games that are full")
@click.option("--telegram", is_flag=True, help="Send results to Telegram")
@click.option("--telegram-token", envvar="TELEGRAM_BOT_TOKEN", help="Telegram Bot Token (or set TELEGRAM_BOT_TOKEN env var)")
@click.option("--telegram-chat-id", envvar="TELEGRAM_CHAT_ID", help="Telegram Chat ID (or set TELEGRAM_CHAT_ID env var)")
def find_games(lat, lng, radius, sport, start_time, end_time, timezone, verbose, include_full, telegram, telegram_token, telegram_chat_id):
    """Find available badminton games on Playo matching your criteria."""
    # Get today's date in the specified timezone
    local_tz = pytz.timezone(timezone)
    now = datetime.datetime.now(local_tz)
    today_date = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # Parse desired time window
    try:
        desired_start = datetime.datetime.strptime(start_time, "%H:%M").time()
        desired_end = datetime.datetime.strptime(end_time, "%H:%M").time()
    except ValueError:
        console.print("[bold red]Error:[/bold red] Invalid time format. Please use HH:MM (24-hour format).")
        return

    console.print(f"[bold green]Searching for badminton games around your location...[/bold green]")
    console.print(f"Looking for games between [bold]{start_time}[/bold] and [bold]{end_time}[/bold] IST today")

    if verbose:
        console.print(f"[dim]Search parameters: lat={lat}, lng={lng}, radius={radius}km[/dim]")
        console.print(f"[dim]Current time in {timezone}: {now.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

    # Prepare API request
    url = "https://api.playo.io/activity-public/list/location"
    payload = {
        "lat": lat,
        "lng": lng,
        "cityRadius": radius,
        "gameTimeActivities": False,
        "page": 0,
        "lastId": "",
        "sportId": [sport],
        "booking": False,
        "date": [today_date]
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        if data.get("requestStatus") != 1 or "data" not in data:
            console.print("[bold red]Error:[/bold red] Failed to get valid response from Playo API")
            return

        # Process activities
        activities = data["data"].get("activities", [])
        if not activities:
            console.print("[yellow]No badminton activities found for today[/yellow]")
            return

        # Filter activities based on criteria
        matching_games = []

        for activity in activities:
            # Convert UTC times to local timezone
            start_time_utc = parser.parse(activity["startTime"])
            end_time_utc = parser.parse(activity["endTime"])

            start_time_local = start_time_utc.astimezone(local_tz)
            end_time_local = end_time_utc.astimezone(local_tz)

            # Print all times in debug mode
            # console.print(f"DEBUG: {activity.get('location', 'Unknown')} - Start: {start_time_local.strftime('%H:%M')} IST (UTC: {start_time_utc.strftime('%H:%M')})")

            # Convert time objects correctly for comparison
            start_hour = start_time_local.hour
            start_minute = start_time_local.minute

            # Convert desired times to hours and minutes for easier comparison
            desired_start_hour = desired_start.hour
            desired_start_minute = desired_start.minute
            desired_end_hour = desired_end.hour
            desired_end_minute = desired_end.minute

            # Check if this game starts at 7PM (19:00) and ends at 8PM (20:00)
            is_time_match = False

            # Get duration in minutes
            duration_minutes = ((end_time_local.hour * 60 + end_time_local.minute) -
                               (start_time_local.hour * 60 + start_time_local.minute))

            # Check if start time is 7PM (with small tolerance)
            if (start_hour == desired_start_hour and
                start_minute >= desired_start_minute and
                start_minute < desired_start_minute + 10):  # Allow a small window of 10 minutes

                # Check if duration is approximately 1 hour (between 50-70 minutes)
                if 50 <= duration_minutes <= 70:
                    is_time_match = True

            # Check if there are available slots
            is_available = (
                not activity.get("full", True) and
                (activity.get("maxPlayers", 0) == -1 or
                 activity.get("joineeCount", 0) < activity.get("maxPlayers", 0))
            )

            # When verbose, print time details for each game to help debug
            if verbose:
                time_info = f"[dim]{activity.get('location', 'Unknown')} - Start: {start_time_local.strftime('%H:%M')} IST ({start_time_utc.strftime('%H:%M')} UTC), " + \
                           f"End: {end_time_local.strftime('%H:%M')} IST, Duration: {duration_minutes} min, " + \
                           f"Time match: {'Yes' if is_time_match else 'No'}, Available: {'Yes' if is_available else 'No'}[/dim]"
                console.print(time_info)

            # Both conditions must be true
            if is_time_match and is_available:
                matching_games.append({
                    "id": activity["id"],
                    "location": activity["location"],
                    "venue_name": activity.get("venueName", "N/A"),
                    "start": start_time_local.strftime("%I:%M %p"),
                    "end": end_time_local.strftime("%I:%M %p"),
                    "players": f"{activity.get('joineeCount', 0)}/{activity.get('maxPlayers', 'unlimited')}",
                    "host": activity.get("userInfo", [{}])[0].get("fName", "Unknown"),
                    "skill": activity.get("skill", "Any"),
                    "price": f"{activity.get('price', 0)} {activity.get('currencyTxt', 'INR')}"
                })

        # Display results
        if matching_games:
            table = Table(title=f"Available Badminton Games ({len(matching_games)} matches found)")

            table.add_column("Location", style="cyan")
            table.add_column("Time", style="green")
            table.add_column("Players", style="yellow")
            table.add_column("Host", style="magenta")
            table.add_column("Skill Level", style="blue")
            table.add_column("Link", style="bright_blue")

            for game in matching_games:
                table.add_row(
                    f"{game['venue_name']}",
                    f"{game['start']} - {game['end']}",
                    game["players"],
                    game["host"],
                    game["skill"],
                    f"https://playo.co/match/{game['id']}"
                )

            console.print(table)

            # Send to Telegram if requested
            if telegram:
                if not telegram_token or not telegram_chat_id:
                    console.print("[bold red]Error:[/bold red] Telegram token and chat ID are required for Telegram notifications")
                    console.print("[dim]Set them with --telegram-token and --telegram-chat-id or via environment variables[/dim]")
                else:
                    try:
                        send_to_telegram(matching_games, telegram_token, telegram_chat_id)
                        console.print("[green]Results sent to Telegram successfully![/green]")
                    except Exception as e:
                        console.print(f"[bold red]Error sending to Telegram:[/bold red] {e}")
        else:
            console.print("[yellow]No games found matching your criteria[/yellow]")
            if telegram and telegram_token and telegram_chat_id:
                try:
                    asyncio.run(send_telegram_message(
                        "No badminton games found matching your criteria for today.",
                        telegram_token,
                        telegram_chat_id
                    ))
                    console.print("[green]Empty results notification sent to Telegram[/green]")
                except Exception as e:
                    console.print(f"[bold red]Error sending to Telegram:[/bold red] {e}")

    except requests.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] Failed to connect to Playo API: {e}")
    except json.JSONDecodeError:
        console.print("[bold red]Error:[/bold red] Failed to parse API response")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] An unexpected error occurred: {e}")

def send_to_telegram(games, token, chat_id):
    """Send game information to Telegram as a nicely formatted message."""
    if not games:
        return

    # Create a formatted message for Telegram
    message = "🏸 *Available Badminton Games* 🏸\n\n"

    for i, game in enumerate(games, 1):
        message += f"*{i}. {game['venue_name']}*\n"
        message += f"⏰ {game['start']} - {game['end']}\n"
        message += f"👥 Players: {game['players']}\n"
        message += f"👤 Host: {game['host']}\n"
        message += f"🎯 Skill: {game['skill']}\n"
        message += f"🔗 [Join Game](https://playo.co/match/{game['id']})\n\n"

    # Send the message
    asyncio.run(send_telegram_message(message, token, chat_id))

async def send_telegram_message(message, token, chat_id):
    """Send a message to Telegram using the Bot API."""
    bot = Bot(token=token)
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False
    )


if __name__ == "__main__":
    find_games()
```

The script outputs a beautiful output:

![image](/images/badminton_cli.png)

Telegram:

![image](/images/badminton_tg.png)

## Scheduling

I wanted this script to run reliably every day and used GitHub Actions for that.
GitHub Actions felt like the path of least resistance as I didn't have to worry about keeping a server running or getting alerts if something crashed. For a small personal script like this, it was the perfect "set it and forget it" solution.

```yml
name: Badminton Game Checker Base
on:
  schedule:
    # Run Monday to Friday at 12:00 PM IST (6:30 AM UTC)
    - cron: "30 6 * * 1-5"

jobs:
  check-games:
    runs-on: ubuntu-latest

    env:
      TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
      TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
      LATITUDE: ${{ inputs.latitude }}
      LONGITUDE: ${{ inputs.longitude }}
      RADIUS: ${{ inputs.radius }}
      SPORT_ID: ${{ inputs.sport_id }}
      TIMEZONE: ${{ inputs.timezone }}
      START_TIME: ${{ inputs.start_time }}
      END_TIME: ${{ inputs.end_time }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install uv

      - name: Run game check
        run: |
          echo "Checking for games from $START_TIME to $END_TIME"
          uv run finder.py \
            --lat "$LATITUDE" \
            --lng "$LONGITUDE" \
            --radius "$RADIUS" \
            --sport "$SPORT_ID" \
            --timezone "$TIMEZONE" \
            --start-time "$START_TIME" \
            --end-time "$END_TIME" \
            --telegram
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

I used GitHub Actions inputs to configure the variables for my script. Found this feature to be quite neat for scheduling different crons for weekday/weekends.

![alt text](/images/badminton_gh.png)

## Summary

For small quality-of-life improvements - solving your own specific problems with custom scripts tailored exactly to your needs - gotta love the LLMs man. We're gonna see more and more of such "personal tooling" in future as the entry to barrier for coding is lowered with LLMs. The democratization of coding through LLMs means people (even non-technical ones) can focus on "describing" the problem well, rather than struggling with implementation details. Being able to articulate what you want clearly becomes the primary skill - yes, it's a skill issue if you can't prompt well, but it's far more accessible than learning programming from scratch.

Fin!
