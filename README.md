Irrigation Controller

Irrigation controller backend designed to run on a Raspberry Pi.
Connection between backend and frontend is made with MQTT.
The code repository does not contain frontend code.
My frontend is made with blynk - low code platform for IoT devices (it is free up to 2 devices)
Hardware schematics for MY ACTUAL system are in hardware folder.

HOW TO USE

1. Fetch src folder from repository.
2. Create your own .env file and config files (look in example folder)
3. If you want to use OpenWeather create account there and create additional .env for /utils/weather_adjuster.py script and run it as cron job (I run it one a day)
4. On RaspberryPi create a venv and download all needed dependencies
5. Then use python -m src (--log-config log_config.yml if you want custom logger config)
6. Best way to use it is through systemd service (look in example folder)
7. After setting up your RaspberryPi make the system read only, so sudden power drop does not corrupt your device

Hardware safety note:
While working with hardware part be careful when selecting and connecting valves.
Valves may differ with voltage requirements and MAY operate on AC or DC.
Verify specifications and make sure that every component is compatibile before wiring it up.

Architecture

Blynk frontend
↓
MQTT
↓
Raspberry Pi
↓
GPIO
↓
Relay
↓
Valve
↓
Water flows

RaspberryPi also can publish system status back through MQTT, that allows frontend to display current state of machine.
Raspberry Pi
↓
MQTT
↓
Blynk frontend
