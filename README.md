# pywam API explorer GUI tool

This is a simple GUI tool that uses the pywam library to explore API calls and answers from Samsung Wireless Audio (R) speakers (WAM).

## Installation

Clone the GitHub repository, and install the requirements.

## Usage

- Run `app.py`
- Enter speaker ip and port and click "Connect".
- In the top list you can see all attributes of the speaker that the pywam library supports and when it was last updated.
- In the middle list you can see all received events from the speaker.
  - To copy a full API response right click in the event list and choose copy
  - To view or copy a specific attribute to the API right click on that attribute and choose view or copy.
- In the bottom list you see the log. To debug the pywam library select DEBUG log level.
- You can add more speakers to the list if you edit `settings.json` which is created the first time you run the app.
- Click "Send API" to test new API calls. Then simply enter all the values and click "Send". If you have log level set to DEBUG you can see if the pywam.client is receiving any data from the speaker.

## Contribute

- Issue Tracker: https://github.com/Strixx76/pywam_api_gui/issues
- Source Code: https://github.com/Strixx76/pywam_api_gui

## License

The project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

## Disclaimer Notice

With this tool you will be able to send commands to the speaker that I have never tested. I can NOT guarantee that your speaker is compatible with this app, and you can’t hold me responsible if you brick your speaker when using this app.

## Support the work

[![BuyMeCoffee][coffeebadge]][coffeelink]

[coffeelink]: https://www.buymeacoffee.com/76strixx
[coffeebadge]: https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png
