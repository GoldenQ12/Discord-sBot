Imports and Froms
Tokens
Intents
Format Options = {
    format: best,
    type: audio
} = {
    Audio_Options () => {
        Buffer + Bitrate => Highest
    }
}

LoadYoutube(Format Options)

Bot instantiate via discord

load_playlist()
    From Json.load("json")

save_playlist(playlist: Dict[int, deque]):
    From Json.save(playlist)

## playlist: Dict[int, deque] = load_playlist_from_json('playlists.json')

OnReady () => {
    print("I am ready")
}

Help () => {
    print(command.name => bot.application_commands)
}

Play (ctx: Context, url: str, autoloop: bool) => {
    if (sender is not on voice call) => return false
    else: {
        getChannel,
        if (bot is not Connected) => connect - else: get the current voice_client
    }

    Extraction => https://open.spotify.com/intl-es/track/3XTyejUCaqoKy0bItVFLm5?si=448ca48227c645e6
    {
        track_id = si=448ca48227c645e6
        track_info = sp:Spotify.track(track_id) => {
            track_name,
            artist_name,
        }
    }

    embed creation

    view = classMusic(bot, ctx:Context, song)

    guild_id = context of current server
    if (guild_id == null) => create new one => deque()

    playlist.append (track_info)

    save()

## ? Need to check this
    if (guild_id is not in playlist) : {
        get_next_song()
        new song = next_song['url]
        playlist[guild].append(next_song)
    }

    displayMessage

    searchOnYoutube (track_name + artist_name ( Normal - Feid ))
    info = get_info(search: searchOnYoutube () => {
        track_name,
        artist_name
    }, (download=NOT) - Get First Entry)
    song = info['url'] => get_link()

# THIS HAPPENS AFTER PLAYING THE AUDIO
    after_playing (err) => {
        if err:
            error handle
**      elif (autoloop active and !err) -> **play_audio()**
        elif (!autoloop and !err and guild_id exists) -> **play_audio()**

        if !guild_id : (No more songs available), repeat bot exec
        else:
            delete_ended_song()
            save()
    }

 ***play_audio()*** => {
        next_song = get_last_song()
        add_song(next_song)

**        **CHECK THIS**
        query_it_again()

        embed_update()

        voice_client.play () => {
            discord.play(url, options)
**            **afterPlay => after_playing**
        }
    }

    play_audio()
    Excp catch
}

