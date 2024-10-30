# Cron jobs

## `get_correct-set.sh`

On the production machine `get_correct_set.sh` is set to run as cronjob on the root user.
For the cron job to run successfully a virtual environment for Python 3.8+ must be created in `/home/cs334/mirrulations/scripts/.venv`.

The command to do so is as follows

```bash
cd /home/cs334/mirrulations/scripts
/usr/bin/python3.8 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

Now `get_correct_set.sh` will be able to be run as a script.
To add the cronjob to the root users crontab run the following

```bash
sudo crontab -e
```

Select an editor you feel comfortable with the line below if it is not already there

```
0 */6 * * * /home/cs334/mirruations/scripts/get_correct_set.sh
```

This line tells the cron daemon to run the script every 6 hours.
Output logs are stored in `/var/log/mirruations_counts.log`.
