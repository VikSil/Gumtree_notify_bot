# Gumtree_notify_bot

The script checks if new ads have been posted to a URL on Gumtree website. SMS notification about new ads is sent via mobile internet router.

## Prerequisites

To run this script you will need:
* D-Link DWR-921 router with mobile internet connection via SIM card
* A computer connected to that router

## Setup

1. Install the requirements by running `pip install -r requirements.txt`
2. Add the Gumtree URLs that you want to be parsed to `URLs` variable on line `30` of `main()` function.
3. Create a `variables.env` file and place it in the root directory. It should look something like this:

```
PHONE_NUMBER=12345678901
ROUTER_IP=192.168.0.1
ROUTER_USER=IAmAdmin
ROUTER_PASSWORD=ThisIsMyEncodedPasswordThatIPulledOutOfNetworkTabInBrowserInspectWindow
```

4. Create an `ads.txt` file in the root directory
5. Once per day the script sends a Heartbeat message to notify that it is still running as scheduled. Adjust time to your liking on line `25` of `main()` function.

## Execution

Once above is done, you should be all set up to run the script on a schedule as a cron job.