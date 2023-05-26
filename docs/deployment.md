# Deployment

## View this file in a web browser

To make these docs pretty, run mkdocs ([manual](https://www.mkdocs.org/getting-started/))

## Docker

### Install Docker

Go to [DevOps Documentation — Docker](https://github.com/0xb1b1/devops/blob/main/docs/docker/beginners_guide.md) to learn about Docker and how to deploy the bot.

### Backend service

#### Deployment options

All deployment options are to be defined in the `.env` (environment) file. Copy `env.example` to `.env` and change values to their desired state. Below are descriptions of all environment variables. Should you wish to compose the `.env` file yourself, use the following as reference.

| Variable           | Example value              | Description |
| ------------------ | :------------------------- | :---------- |
| `GOOGLE_API_TOKEN` | `{'JSON': 'privkey', ...}` | Google API Developer key. [Documentation from GSpread](https://docs.gspread.org/en/latest/oauth2.html) |
| `LOGGING_LEVEL`    | `info`                     | Service-wide logging level. Acceptable values: `debug`, `info`, `warning`, `error` |
| `PG_USER`          | `root`                     | Username for PGSQL |
| `PG_PASS`          | `supersecretpass`          | Password for PGSQL User |
| `PG_HOST`          | `db`                       | Docker DNS hostname for PGSQL (configured in `docker-compose.yml`) |
| `PG_PORT`          | `5432`                     | Port for PSQL (configured in `docker-compose.yml` (see PSQL image documentation)) |
| `ADMIN_TOKEN`      | `supersecrettoken69`       | Secret token for admin authentication in bots |
| `WS_CONTENT_ID`    | `0`                        | Sheet Page ID. It's the last argument of the page's URL. Should be populated with bot replies and buttons before deployment |
| `WS_TELEMETRY_ID`  | `123454424`                | Same as previous, but it's autopopulated on start. Stores user telemetry |
| `WS_USERS_ID`      | `371383718`                | Same as previous, but it's autopopulated on start. Stores user data |
| `WS_ADMINS_ID`     | `429291331`                | Same as previous, but it's autopopulated on start. Stores admin IDs |

#### Preconfiguration

After you created the spreadsheet on [Google Sheets](https://sheets.google.com), add `client_email` from your `GOOGLE_API_TOKEN` environment variable to the spreadsheet and give it write access.

!!! warning
    Remove all Traefik labels from `docker-compose.yml` to avoid making the API world-r/writable! This is going to happen only if you left the labels and had a compatible `Traefik` setup. All communications should be internal by default!

#### Start the service

Start the service with `docker compose up -d` after you configured Frontend services.

### Frontend services (bots)

#### Telegram bot

##### Telegram bot Deployment options

All deployment options are to be defined in the `.env` (environment) file. Copy `env.example` to `.env` and change values to their desired state. Below are descriptions of all environment variables. Should you wish to compose the `.env` file yourself, use the following as reference.


| Variable           | Example value              | Description |
| ------------------ | :------------------------- | :---------- |
| `BACKEND_URI`      | `backend`                  | Backend URI. Should default to the `backend` service defined in `docker-compose.yml` |
| `TG_TOKEN`         | `3ABCDEF_GBKSBEFAKS=`      | Telegram token. Get one from [@BotFather](https://t.me/BotFather) |
| `LOGGING_LEVEL`    | `info`                     | Service-wide logging level. Acceptable values: `debug`, `info`, `warning`, `error` |

#### VKontakte bot

##### VKontakte bot Deployment options

All deployment options are to be defined in the `.env` (environment) file. Copy `env.example` to `.env` and change values to their desired state. Below are descriptions of all environment variables. Should you wish to compose the `.env` file yourself, use the following as reference.

| Variable           | Example value              | Description |
| ------------------ | :------------------------- | :---------- |
| `BACKEND_URI`      | `backend`                  | Backend URI. Should default to the `backend` service defined in `docker-compose.yml` |
| `VK_TOKEN`         | `3ABCDEF_GBKSBEFAKS=`      | Get from a VK Community's service settings |
| `LOGGING_LEVEL`    | `info`                     | Service-wide logging level. Acceptable values: `debug`, `info`, `warning`, `error` |

#### Deploy the stack

To deploy this stack, run `docker compose up -d` after you installed Docker on your system. Please note that Docker on Windows and OSX is not native and will consume more resources.
