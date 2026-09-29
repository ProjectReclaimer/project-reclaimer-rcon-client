# Project Reclaimer RCON

A standalone Windows desktop console for Project Reclaimer dedicated servers.
Manage players, send commands, and follow live chat and server events. No game
installation is required on the administrator's PC.

**[Download the latest Windows EXE](https://github.com/ProjectReclaimer/project-reclaimer-rcon-client/releases/latest)**

Open the release's **Assets** and download `reclaimer-rcon-v<version>.exe`.
Double-click to run it. `SHA256SUMS.txt` contains its SHA-256 checksum.
Requires 64-bit Windows 10 or newer.

## Connect

1. Enter the server's **Host** (hostname or IP address, without a URL or port).
2. Enter its RCON TCP **Port**, normally the game port, such as `49176`.
3. Enter the RCON **Password** supplied by your server administrator.
4. Click **Connect**. An optional **Moderator name** identifies your actions.

The **Players** list refreshes every five seconds. Select a player to prepare
a `tell`, `kick`, `ban`, `mute`, or `unmute` command. Edit its arguments, then
press **Send**. You can also type a command directly or use **Status**, **Players**,
**Bans**, and **Help**. Up and Down recall previous commands.

The console displays live chat, joins, departures, and moderation events.
**JSON** shows the full message fields; **Copy** copies the displayed log.
The latest 500 entries are kept in memory, limited to 16,384 characters each.
Times are UTC. Passwords and connection settings are not saved. The password
field is cleared after a successful sign-in.

After a disconnection, reconnect explicitly. Commands are never automatically
retried: an unanswered moderation command may already have run.

## Enable RCON on your server

Set a password in the server's `dedicated.toml` and restart the server:

```toml
[rcon]
password = "replace this with a strong private passphrase"
address = "127.0.0.1"
```

The password must contain 8 to 128 characters. Each server listens on TCP at
its game port unless you set `rcon_port` in its `[[server]]` section.

RCON traffic is unencrypted. For remote administration, use a VPN or SSH tunnel.
For example, `ssh -L 49176:127.0.0.1:49176 you@server` lets you connect this client
to host `127.0.0.1`, port `49176`. Direct `wss://` URLs are not supported.

## Common commands

| Command | Purpose |
| --- | --- |
| `status` | Server and game status |
| `players` | Connected players and their IDs |
| `say Welcome everyone` | Send a server chat message |
| `tell "Master Chief" Hello` | Send a private message |
| `kick "Master Chief" spamming` | Remove a player |
| `ban "Master Chief" 7d cheating` | Ban a player for seven days |
| `mute "Master Chief" 30m spamming` | Mute a player for thirty minutes |
| `unmute "Master Chief"` | Lift a mute |
| `bans` | List active bans |
| `help` | All supported commands |
| `help ban` | Help for a specific command |

Players may also be named by their player ID or their current `#number`.
Quote names containing spaces.

## Releases and repository contents

This is a downloads repository. It contains documentation and release-mirroring
automation, **not the Project Reclaimer application or server source code**.
GitHub's automatic "Source code" archives contain only those public files;
download the `.exe` asset to use the client.

The publishing workflow checks the
[public Reclaimer releases](https://github.com/ProjectReclaimer/project-reclaimer-releases/releases)
twice an hour and verifies the RCON executable's SHA-256 checksum before
publishing it here. Maintainers can also run **Publish RCON downloads** manually
for a particular version. It has no access to the private application repository.
