kill -9 `ps aux | grep gunicorn | grep verify | awk '{print $2}'`
