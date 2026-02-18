# FrankenPHP CLI

A production-ready, open-source Python CLI for managing websites on Linux servers running **FrankenPHP** (Caddy with embedded PHP). It is **totally based on the FrankenPHP server**: site configs use FrankenPHP’s `php_server` directive only (no PHP-FPM). Professional hosting management similar to CyberPanel but CLI-first, modular, secure, and standardized.

## Features

- **Site management**: Add sites with multiple domains, delete, list, show info
- **Database management**: Create and delete MySQL/MariaDB databases (with generated credentials)
- **WordPress**: Install WordPress on an existing site
- **User management**: Create and delete Linux users
- **Safe by default**: Domain validation, subprocess (no raw shell), rollback on failure, logging, JSON state

## Prerequisites (install before using the CLI)

These must be installed and running on the server where you use `franken`:

| Requirement | Purpose | How to verify |
|-------------|---------|----------------|
| **Python 3.10+** | Run the CLI | `python3 --version` |
| **FrankenPHP** (Caddy + embedded PHP) | Serve PHP sites | FrankenPHP binary in PATH or Caddy with FrankenPHP; config dir writable (e.g. `/etc/caddy/sites.d`) |
| **MySQL or MariaDB** | Create DBs for sites/WordPress | Server listening on port 3306; root (or admin) user and password for `franken` to create databases |

**Install all prerequisites (Ubuntu/Debian, one command)**

```bash
sudo apt update && sudo apt install -y python3 python3-venv pipx mysql-server && pipx ensurepath && sudo systemctl start mysql && sudo systemctl enable mysql
```

Then set the MySQL root password and export it for the CLI (run once):

```bash
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'YourPassword'; FLUSH PRIVILEGES;" && export FRANKENPHP_DB_ROOT_PASSWORD='YourPassword'
```

Replace `YourPassword` with a strong password. Install the CLI with `pipx install frankenphp-cli`. FrankenPHP (Caddy + PHP) is not in apt; install it from [frankenphp.dev](https://frankenphp.dev) or run it via Docker when you are ready to serve sites.

**One-time setup for the database**

- Ensure MySQL/MariaDB is **running** (e.g. `systemctl status mysql` or `systemctl status mariadb`).
- Set the root (or admin) password and expose it to the CLI via environment:
  ```bash
  export FRANKENPHP_DB_HOST=localhost
  export FRANKENPHP_DB_ROOT_USER=root
  export FRANKENPHP_DB_ROOT_PASSWORD=your_mysql_root_password
  ```
- Optional: create a dedicated MySQL user with `CREATE DATABASE` / `CREATE USER` / `GRANT` rights and use that instead of `root`.

If you see **"Can't connect to MySQL server"** (e.g. 2003/111), the database server is not reachable: start the MySQL/MariaDB service and/or check `FRANKENPHP_DB_HOST` (and firewall) so the host and port are correct.

## Installation

On **Ubuntu 22.04+, Debian 12+**, and other systems that use [PEP 668](https://peps.python.org/pep-0668/) (externally managed Python environments), you should not install into the system Python. Use one of the methods below.

**From PyPI — recommended: pipx** (isolated, global CLI):

```bash
pipx install frankenphp-cli
```

**From PyPI — using a virtual environment**:

```bash
python3 -m venv .venv
source .venv/bin/activate   # or on Windows: .venv\Scripts\activate
pip install frankenphp-cli
```

**From source** (development):

```bash
git clone https://github.com/meetsohail/frankenphp-cli.git
cd frankenphp-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

The `franken` command will be available on your PATH (with pipx it’s global; with a venv, activate the venv first).

If you see **"externally-managed-environment"** when using `pip install` on Ubuntu/Debian, your distro enforces PEP 668—use **pipx** or a **venv** as above instead of installing into the system Python.

For local or CI testing without root, set state and log to writable paths:

```bash
export FRANKENPHP_STATE_DIR=/tmp/frankenphp-cli
export FRANKENPHP_LOG_FILE=/tmp/frankenphp-cli.log
export FRANKENPHP_WEB_ROOT=/tmp/var-www
```

## Configuration

Configure via environment variables (optional):

| Variable | Default | Description |
|----------|---------|-------------|
| `FRANKENPHP_STATE_DIR` | `/var/lib/frankenphp-cli` | State directory |
| `FRANKENPHP_LOG_FILE` | `/var/log/frankenphp-cli.log` | Log file |
| `FRANKENPHP_WEB_ROOT` | `/var/www` | Web root for sites |
| `FRANKENPHP_CADDY_CONFIG_DIR` | `/etc/caddy/sites.d` | Caddy site configs |
| `FRANKENPHP_CADDY_RELOAD` | `systemctl reload caddy` | Command to reload Caddy |
| `FRANKENPHP_DB_HOST` | `localhost` | MySQL host |
| `FRANKENPHP_DB_ROOT_USER` | `root` | MySQL root user |
| `FRANKENPHP_DB_ROOT_PASSWORD` | (empty) | MySQL root password |
| `FRANKENPHP_PHP_VERSION` | `8.3` | PHP version label in state (FrankenPHP uses its embedded PHP) |

## Usage

### Site management

```bash
# Add a site with aliases and WordPress
franken site add example.com www.example.com --app wordpress --php 8.3

# Using --aliases for extra domains
franken site add example.com --aliases www.example.com blog.example.com --app wordpress

# Delete a site
franken site delete example.com

# List all sites
franken site list

# Show site details
franken site info example.com
```

### Database

```bash
# Create database (user and password are generated)
franken db create example_db

# Delete database
franken db delete example_db
```

### WordPress

```bash
# Install WordPress on an existing site
franken wordpress install example.com
```

### User management

```bash
# Create Linux user
franken user create sohail

# Delete Linux user (and home)
franken user delete sohail
```

### Global options

- `--dry-run`: Preview commands without making changes
- `--force`: Overwrite existing site when adding
- `--version` / `-V`: Show version

## Project structure

```
frankenphp-cli/
├── frankenphp_cli/
│   ├── main.py          # Typer CLI entrypoint
│   ├── config.py        # Paths and env config
│   ├── core/
│   │   ├── site.py      # Site add/delete/list/info
│   │   ├── database.py  # DB create/delete
│   │   ├── wordpress.py # WordPress install
│   │   ├── user.py      # Linux user create/delete
│   │   ├── caddy.py     # FrankenPHP Caddy config (php_server)
│   │   └── php.py       # PHP version label helpers
│   ├── utils/
│   │   ├── system.py    # subprocess.run helpers
│   │   ├── validators.py
│   │   ├── logger.py
│   │   └── state.py     # JSON state
│   └── templates/
│       ├── caddy.tpl
│       └── wp-config.tpl
├── tests/
├── pyproject.toml
├── README.md
└── LICENSE
```

## Security

- Domains are validated with a strict regex
- All external commands use `subprocess.run([...], check=True)` (no shell)
- Database passwords are generated with `secrets` (32 chars)
- Operations are logged to `/var/log/frankenphp-cli.log`
- State is stored in `/var/lib/frankenphp-cli/state.json`

## Development

```bash
# Install with dev deps
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## Publishing to PyPI (GitHub Automation)

Releases are published to PyPI automatically when you push a **version tag**.

### One-time setup

1. Create an API token on [PyPI](https://pypi.org/manage/account/token/): Account → API tokens → Add API token (scope: entire account or just this project).
2. In your GitHub repo: **Settings → Secrets and variables → Actions** → **New repository secret**:
   - Name: `PYPI_API_TOKEN`
   - Value: `pypi-...` (the token you copied).

### Releasing a new version

1. Bump the version in `pyproject.toml` (e.g. `version = "0.2.0"`).
2. Commit and push, then create and push a tag matching the version:

   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

3. The **Publish to PyPI** workflow runs: runs tests (Python 3.10–3.12), builds the package, and publishes to PyPI. Install with `pip install frankenphp-cli`.

### TestPyPI (optional)

To try the release flow without publishing to production PyPI:

1. Create a token at [TestPyPI](https://test.pypi.org/manage/account/token/) and add it as `TESTPYPI_API_TOKEN` in GitHub Actions secrets.
2. In the Actions tab, run the workflow **Publish to TestPyPI** manually. It will publish to TestPyPI; install with `pip install -i https://test.pypi.org/simple/ frankenphp-cli`.

## Contributing

1. Fork the repo and create a branch
2. Make changes with tests where applicable
3. Ensure `pytest` and linting pass
4. Open a pull request with a clear description

## License

MIT License. See [LICENSE](LICENSE).
