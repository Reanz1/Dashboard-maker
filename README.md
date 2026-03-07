# Dashboard-maker

This app is a sleek, lightweight Home Server Dashboard built with Flask. It is designed for self-hosters who want a centralized hub for their local services without the overhead of complex configuration files or manual database management.

Its "minimalist-first" philosophy ensures that you can manage your entire home lab interface directly from the browser.

# 🚀 Key Features

Dynamic UI Management: Add, group, and delete services or categories on the fly without ever touching the source code or restarting the container.

Plug-and-Play Theming: Swap the entire look of your dashboard instantly. The app scans the /templates directory; simply drop in a new .html file, and it appears as a selectable option in the settings.

Zero-Database Architecture: Uses simple JSON flat-files for data storage, making backups and migrations as easy as copying a single folder.

Modern Aesthetics: Comes pre-loaded with a "Minimal Dark" theme for a clean professional look and a "Neon Cyberpunk" theme for high-energy setups.

Container Ready: Fully Dockerized and lightweight, using a Python-slim base to keep your system resources focused on your services, not the dashboard.


# 🎨 Adding Your Own Theme

One of the app's strongest features is its flexibility. To create a custom look:

Create a new HTML file (e.g., yourtheme.html).

Use standard Jinja2 or simple HTML/JavaScript to fetch data from the /api/services endpoint.

Place the file in the /templates folder.

The dashboard will automatically detect it and allow you to switch to it via the UI.



# 📦 Deployment
```
services:
  dashboard:
    image: randomsi/dashboard-maker:latest
    container_name: homelab-dashboard
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./data:/data
      - ./images:/images
      - ./templates:/templates
```
