# Cron jobs

## `get_correct-set.sh`

On the production machine `get_correct_set.sh` is set to run as cronjob on the root user.

The current cron job is as follows:

```
0 */6 * * * /home/cs334/mirruations/scripts/get_correct_set.sh
```

Output logs are stored in `/var/log/mirruations_counts.log`.
