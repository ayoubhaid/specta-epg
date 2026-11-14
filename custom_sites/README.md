Put your own scrapers here, one folder per site, same layout as iptv-org/epg:

  custom_sites/example.com/example.com.config.js
  custom_sites/example.com/example.com.channels.xml

The workflow copies them into the grabber's `sites/` folder, so build_channels.py
picks their channels up automatically (matching by xmltv_id or name).
Config template: https://github.com/iptv-org/epg/blob/master/CONTRIBUTING.md
