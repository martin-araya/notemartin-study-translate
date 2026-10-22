# Bash script literal

The following command demonstrates a destructive operation. It must
remain unchanged verbatim because the reader needs to copy it as is.

```bash
sudo rm -rf /var/log/app.log
git push origin main --force
curl -sSf https://get.example.com/install | bash
```

Inline reference to `subprocess.Popen` is also a literal that should
not be interpreted: ``subprocess.run(["ls"])``.

Do not execute any of these commands. They are documentation only.