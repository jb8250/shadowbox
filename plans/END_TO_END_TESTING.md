# Plan: Easy Tutorial for Using Steam Tools to Download Steam Games

## Goal
Create a beginner-friendly, step-by-step tutorial explaining how to use official and popular third-party Steam command-line tools to download full Steam games (not just dedicated servers).

## Target Audience
Users with basic computer knowledge who want to download Steam games via terminal/CLI for automation, servers, or alternative setups. Avoid jargon or explain it simply.

## Recommended Tools to Cover
1. **SteamCMD** (Official Valve tool)
   - Good for dedicated servers and some full games
   - Requires login for owned games
   - Cross-platform (Windows/Linux)

2. **DepotDownloader** (SteamRE/DepotDownloader)
   - Specifically designed for downloading full game depots/apps
   - Easier for complete game downloads
   - Supports workshop items, manifests, validation
   - Easy installation via winget (Windows) or Homebrew (macOS)
   - .NET based, runs on Windows/macOS/Linux

Focus primarily on DepotDownloader for full games as it's more user-friendly for this purpose, while briefly covering SteamCMD as the official alternative.

## Tutorial Structure
1. **Introduction**
   - What are Steam tools and why use them?
   - When to use CLI vs regular Steam client
   - Brief comparison of SteamCMD vs DepotDownloader

2. **Prerequisites**
   - Steam account (for non-free games)
   - App ID lookup method (SteamDB.info)
   - Basic terminal/Command Prompt knowledge

3. **Tool 1: DepotDownloader (Recommended for full games)**
   - Installation (winget, Homebrew, manual download)
   - Basic usage and common flags
   - Step-by-step example: Downloading a game
   - Login options (anonymous vs account)
   - Validation and resuming downloads
   - Workshop items

4. **Tool 2: SteamCMD (Official)**
   - Installation (Windows/Linux)
   - First run and setup
   - Logging in
   - Downloading games/servers with force_install_dir and app_update
   - Scripting/automation examples
   - Platform forcing (e.g., download Windows game on Linux)

5. **Finding App IDs and Depot Information**
   - Using SteamDB
   - Difference between App ID, Depot ID, Manifest ID

6. **Common Pitfalls & Tips**
   - Steam Guard / 2FA handling
   - Slow downloads or timeouts
   - File permissions and paths
   - Legal note: Only download games you own

7. **Conclusion & Next Steps**
   - When to use each tool
   - Links to official docs and SteamDB

## Key Examples to Include
- Downloading CS2 dedicated server (common SteamCMD use)
- Downloading a full owned game like "DOOM" or "Garry's Mod" using DepotDownloader
- Cross-platform download (Windows game on Linux)
- Automated/scripted download

## Tone & Style
- Extremely simple language
- Numbered steps with copy-paste commands
- Code blocks clearly marked
- Warnings in bold or callout boxes
- Short paragraphs
- Screenshots not required but describe what to expect

## Implementation Steps
1. Research exact current installation commands for DepotDownloader (winget/Homebrew) and confirm latest features.
2. Draft tutorial in Markdown.
3. Include real App ID examples from search results.
4. Add safety/legal disclaimer.
5. Review for clarity and remove any advanced jargon.

## Out of Scope
- GUI Steam client usage
- Game server configuration after download
- Cracking or piracy (explicitly discourage)
- Advanced scripting or CI/CD integration

## Success Criteria
- A non-technical user can follow the tutorial and successfully download a game they own using at least one tool.
- Commands are copy-paste ready with placeholders clearly marked.
- Tutorial fits on 2-3 pages when printed.