# dot-jenkins (Display-O-Tron Jenkins)

dot-jenkins is a python tool that visualizes a Jenkins view using a Pimoroni Display-O-Tron
(see: https://shop.pimoroni.com/collections/raspberry-pi/products/display-o-tron-hat)

# Preparing your RasperryPi

To get started, make sure you have set up the Display-O-Tron dependencies correctly using the Pimoroni scripts, see: https://github.com/pimoroni/dot3k

You also need to have the requests Python library installed. If you are using Raspbian, you can use ```pip install requests``` to get it.

If you're interested, there is an Ansible playbook for automating the setup in the ```ansible``` subdirectory. This can be useful if you are dealing with a lot of Pi's.

# Configuration
First you muste  create a configuration pointing to your Jenkins instance and view. Make sure you do not forget to add ```/api/json``` to the end of the view URL.

An example configuration for Jenkins running on ```localhost:8080``` and a view named _myview_, using no authentication:

```json
{
    "viewUrl": "http://localhost:8080/view/myview/api/json",
    "viewRefreshInterval": 60,
    "viewRefreshErrorInterval": 60,
    "sslVerifyCertificates": false,
    "networkInterfaceName": "wlan0"
}
```

This example uses HTTPS and username/token authentication:

```json
{
    "viewUrl": "https://jenkins.company.com/view/dot-jenkins/api/json",
    "viewRefreshInterval": 30,
    "viewRefreshErrorInterval": 60,
    "deltaTimeStep": 5,
    "sslVerifyCertificates": false,
    "networkInterfaceName": "wlan0",
    "username": "john",
    "authToken": "adf63446de6571dfa1"
}
```

The table below shows all possible configuration properties with their meaning and default values.

| Configuration Parameter | Description | Default Value |
| ----------------------- | :----------- | :------------- |
| ```viewUrl``` | The URL of the Jenkins view (JSON API) | _<none>_ |

*TODO: document the other parameters*

# Running the daemon

Run Python with the ```controller.py``` script and specify your configuration on the command-line.

```bash
python controller.py -c my-config.cfg --debug
```

To automate this, a supervisord configuration is located in the the ```etc``` subdirectory. The configuration assumed that dot-jenkins was installed using the Ansible playbook, and is located in ```/opt/dot-jenkins``` and gets its configuration from ```/etc/dot-jenkins.cfg```


