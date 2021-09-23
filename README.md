# curseforge-cli
### (unofficial) command line addon manager for World of Warcraft, The Elder Scrolls Online, coming soon: Minecraft [and more](https://www.curseforge.com/all-games)

## Installation
Install via [pipx](https://github.com/pypa/pipx)
```
pipx install curseforge-cli
```

## Basic usage
```
curseforge-cli game action [arguments]
```

## Supported games
- wow_retail - *World of Warcraft Retail*
- wow_classic - *World of Warcraft Classic*
- wow_tbc - *World of Warcraft The Burning Crusade*
- teso - *The Elder Scrolls Online*

## Actions
- ## list - *list installed addons*
  Examples:
  ```
  curseforge-cli wow_tbc list
  ```
- ## search - *search addon by name*
  Arguments:
  - {name} - *string, e.g. "bartender"*
  - --game_version - *string, e.g. "1.13.7"*
  - --page_size - *int, max number of results (500 max)*
  - --sort - *int, choose from 0 (featured), 1 (popularity), 2 (last update), 3 (name), 4 (author), 5 (total_downloads)*

  Examples:

  Search addons for WoW classic with name similar to "bartender"
  ```
  curseforge-cli wow_tbc search bartender
  ```

  Search the most downloaded "dbm" addon. Will probably be [Deadly Boss Mods](https://www.curseforge.com/wow/addons/deadly-boss-mods)
  ```    
  curseforge-cli wow_tbc search dbm --page_size 1 --sort 5
  ```
- ## install - *install addon*
  Arguments:
  - {id} - *int, curseforge addon id*
    
  Examples:

  Install [Total RP 3: Classic](https://www.curseforge.com/wow/addons/total-rp-3-classic) 
  ```
  curseforge-cli wow_tbc install 335857
  ```

## Coming soon<sup>TM</sup>
- Manual game discovery and configuration
- Smart updater
- Addon config import/export

## API info (very scarce because the docs [are not officially written yet](https://curseforge-ideas.overwolf.com/ideas/CF-I-1200)):

https://github.com/Mondanzo/mc-curseforge-api/blob/master/index.js
https://gist.github.com/crapStone/9a423f7e97e64a301e88a2f6a0f3e4d9

